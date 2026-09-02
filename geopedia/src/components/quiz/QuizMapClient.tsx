/**
 * Connects a quiz page to GeoPedia's reusable map, quiz settings, and quiz
 * grouping systems.
 *
 * This component:
 *
 * - Delays rendering until the client has hydrated.
 * - Loads and persists settings for the current quiz.
 * - Loads GeoJSON used by the quiz-grouping system.
 * - Owns the currently active quiz group.
 * - Loads and persists user-created saved groups.
 * - Coordinates manual feature selection.
 * - Renders the map with quiz interaction enabled.
 * - Owns the open/closed state of the Settings and Groups panels.
 *
 * The hydration boundary prevents the map from briefly rendering with default
 * quiz settings before the user's saved localStorage values are available.
 */

"use client";

import { useMemo, useState, useSyncExternalStore } from "react";

import FeatureQuizMap from "@/components/map/FeatureQuizMap";
import FeatureQuizPanelControls from "@/components/quiz/controls/feature/FeatureQuizPanelControls";
import FeatureQuizGroupsPanel from "@/components/quiz/panel/feature/FeatureQuizGroupsPanel";
import FeatureQuizSettingsPanel from "@/components/quiz/panel/feature/FeatureQuizSettingsPanel";
import TownQuizFilterPanel from "@/components/quiz/panel/town/TownQuizFilterPanel";
import { getFeatureAnswers } from "@/maps/labels/feature/featureAnswers";
import type { MapConfig, QuizMapClickBehavior } from "@/maps/types";
import { useActiveQuizGroup } from "@/quiz/groupings/feature/hooks/useActiveQuizGroup";
import { useManualGroupSelection } from "@/quiz/groupings/feature/hooks/useManualGroupSelection";
import { useQuizGroupingData } from "@/quiz/groupings/feature/hooks/useQuizGroupingData";
import { useSavedQuizGroups } from "@/quiz/groupings/feature/hooks/useSavedQuizGroups";
import type {
  ActiveQuizGroup,
  SavedQuizGroup,
} from "@/quiz/groupings/feature/types";
import { getTownPopulationGroup } from "@/quiz/groupings/town/townPopulationGroups";
import { useFeatureQuizSettings } from "@/quiz/hooks/useFeatureQuizSettings";
import { useTownQuiz } from "@/quiz/hooks/useTownQuiz";
import { TownCountryConfig } from "@/quiz/town/townCountryConfigs";
import type { FeatureQuiz, TownQuiz } from "@/types/quiz";

import TownQuizMap from "../map/TownQuizMap";
import TownQuizModeControl, {
  type TownQuizMode,
} from "./controls/town/TownQuizModeControl";
import TownQuizPanelControls from "./controls/town/TownQuizPanelControls";
import TownQuizOverlay from "./overlay/TownQuizOverlay";

/**
 * Props required when rendering a feature-based quiz map.
 *
 * Feature quizzes operate on GeoJSON map features and therefore require a
 * complete `MapConfig` describing their source data, layers, interaction
 * behavior, and initial map presentation.
 */
type FeatureQuizMapClientProps = {
  /** Identifies these props as belonging to a feature-based quiz. */
  kind: "feature";

  /** Country containing the quiz. Used to identify persisted user data. */
  countryId: string;

  /** Feature-based quiz displayed and controlled by the map. */
  quiz: FeatureQuiz;

  /** Geographic map configuration required by the feature quiz. */
  mapConfig: MapConfig;
};

/**
 * Props required when rendering a town-based quiz map.
 *
 * Town quizzes use the shared MapTiler town-map implementation rather than a
 * feature `MapConfig`. Their country-specific configuration supplies the
 * initial camera position and geographic scoring distance.
 */
type TownQuizMapClientProps = {
  /** Identifies these props as belonging to a town-based quiz. */
  kind: "town";

  /** Country containing the quiz. Used to identify persisted user data. */
  countryId: string;

  /** Town-based quiz displayed and controlled by the map. */
  quiz: TownQuiz;

  /** Country-specific camera and scoring configuration for the town quiz. */
  townConfig: TownCountryConfig;
};

/**
 * Props accepted by the shared client-side quiz map boundary.
 *
 * The discriminated union guarantees that each quiz kind is paired with the
 * configuration required by its corresponding map implementation.
 */
type QuizMapClientProps =
  FeatureQuizMapClientProps | TownQuizMapClientProps;

/**
 * No-op subscription used by `useSyncExternalStore` to detect hydration.
 *
 * The server snapshot returns `false`, while the browser snapshot returns
 * `true`. No external value actually changes, so there is nothing to
 * subscribe to.
 *
 * @returns An empty cleanup function.
 */
function subscribeToHydration(): () => void {
  return () => {};
}

/**
 * Prevents the quiz map from rendering until React has hydrated on the client.
 *
 * Quiz settings and saved groups are stored in localStorage, which is
 * unavailable during server rendering. Waiting for hydration ensures the map
 * is first created using the user's persisted state.
 *
 * @param props - Quiz map properties forwarded to the hydrated component.
 * @returns An empty map-sized placeholder before hydration, or the hydrated
 * quiz map afterward.
 */
export default function QuizMapClient(props: QuizMapClientProps) {
  const isHydrated = useSyncExternalStore(
    subscribeToHydration,

    // Browser snapshot.
    () => true,

    // Server snapshot.
    () => false,
  );

  if (!isHydrated) {
    return <div className="h-full w-full" />;
  }

  return <HydratedQuizMapClient {...props} />;
}

/**
 * Routes a hydrated quiz to the client implementation associated with its
 * interaction model.
 *
 * Feature quizzes use the existing GeoJSON feature-map infrastructure, while
 * town quizzes use the dedicated point-location quiz infrastructure.
 *
 * @param props - Fully resolved quiz and configuration properties.
 * @returns The hydrated client implementation for the requested quiz kind.
 */
function HydratedQuizMapClient(props: QuizMapClientProps) {
  if (props.kind === "town") {
    return (
      <HydratedTownQuizMapClient
        kind={props.kind}
        countryId={props.countryId}
        quiz={props.quiz}
        townConfig={props.townConfig}
      />
    );
  }

  return (
    <HydratedFeatureQuizMapClient
      kind={props.kind}
      countryId={props.countryId}
      quiz={props.quiz}
      mapConfig={props.mapConfig}
    />
  );
}

/**
 * Renders the existing GeoJSON feature-based quiz experience.
 *
 * This component owns feature grouping, saved groups, manual feature
 * selection, GeoGuessr-only filtering, feature-answer visibility, and the
 * feature-based interactive map.
 *
 * @param props - Feature quiz map configuration.
 * @param props.countryId - Country used to identify persisted quiz data.
 * @param props.quiz - Feature-based quiz definition.
 * @param props.mapConfig - Geographic configuration rendered by the map.
 * @returns The hydrated feature quiz map and its floating controls.
 */
function HydratedFeatureQuizMapClient({
  countryId,
  quiz,
  mapConfig,
}: FeatureQuizMapClientProps) {
  /** Persisted settings belonging specifically to this country and quiz. */
  const { settings, setSettings } = useFeatureQuizSettings(
    countryId,
    quiz.id,
  );

  /** Loads the quiz's GeoJSON for React-side grouping logic. */
  const { featureCollection } = useQuizGroupingData(
    mapConfig.geojsonUrl,
  );

  /**
   * ID of the saved group currently applied to the quiz.
   *
   * `null` means Full Quiz or an unsaved temporary group is active.
   */
  const [activeSavedGroupId, setActiveSavedGroupId] = useState<
    string | null
  >(null);

  /**
   * Whether the current quiz should include only geographic features available
   * in GeoGuessr.
   *
   * This filter is independent of the active quiz group, allowing it to combine
   * with Full Quiz, property groups, saved groups, and manual groups.
   *
   * This feature is only available for global quizzes.
   */
  const [isGeoGuessrOnly, setIsGeoGuessrOnly] = useState(false);

  /**
   * Owns the group currently applied to the quiz and derives its geographic
   * feature and question subsets.
   */
  const {
    activeGroup,
    resolvedGroup,
    activeQuiz,
    applyGroup,
    resetToFullQuiz,
  } = useActiveQuizGroup({
    quiz,
    mapConfig,
    featureCollection,
  });

  /**
   * Stable map feature IDs belonging to countries currently included in
   * GeoGuessr.
   *
   * The GeoGuessr flag is stored directly on the world-country GeoJSON features.
   * Maps without that property naturally produce an empty set and therefore do
   * not expose any GeoGuessr-only filtering behavior.
   */
  const geoGuessrFeatureIds = useMemo(() => {
    const featureIds = new Set<string>();

    if (!featureCollection || !mapConfig.promoteId) {
      return featureIds;
    }

    for (const feature of featureCollection.features) {
      if (feature.properties?.geoguessr !== true) {
        continue;
      }

      const featureId = feature.properties?.[mapConfig.promoteId];

      if (
        typeof featureId === "string" ||
        typeof featureId === "number"
      ) {
        featureIds.add(String(featureId));
      }
    }

    return featureIds;
  }, [featureCollection, mapConfig.promoteId]);

  /**
   * Quiz answer values belonging to GeoGuessr-enabled geographic features.
   *
   * Question answers are matched using the quiz's configured answer property
   * rather than assuming the map feature ID is also the quiz answer.
   */
  const geoGuessrAnswers = useMemo(() => {
    const answers = new Set<string>();

    if (!featureCollection) {
      return answers;
    }

    for (const feature of featureCollection.features) {
      if (feature.properties?.geoguessr !== true) {
        continue;
      }

      const featureValue = feature.properties?.[quiz.answerProperty];
      const featureAnswers = getFeatureAnswers(featureValue);

      for (const answer of featureAnswers) {
        answers.add(answer);
      }
      // if (typeof answer === "string" || typeof answer === "number") {
      //   answers.add(String(answer));
      // }
    }

    return answers;
  }, [featureCollection, quiz.answerProperty]);

  /**
   * Quiz definition actually supplied to the interactive map.
   *
   * The active group is resolved first by `useActiveQuizGroup`. GeoGuessr Only
   * then acts as a second independent filter over that already-resolved question
   * set.
   */
  const filteredActiveQuiz = useMemo(() => {
    if (!isGeoGuessrOnly) {
      return activeQuiz;
    }

    return {
      ...activeQuiz,

      questions: activeQuiz.questions.filter((question) =>
        geoGuessrAnswers.has(String(question.answer)),
      ),
    };
  }, [activeQuiz, isGeoGuessrOnly, geoGuessrAnswers]);

  /**
   * Owns the temporary feature selection used while manually constructing or
   * editing a quiz group.
   */
  const {
    isSelecting,
    selectedFeatureIds,
    beginSelection,
    toggleFeature,
    removeFeature,
    clearSelection,
    selectAllFeatures,
    cancelSelection,
  } = useManualGroupSelection();

  /**
   * Manual-selection mode temporarily replaces normal quiz clicking with
   * feature-selection behavior.
   */
  const mapClickBehavior: QuizMapClickBehavior = isSelecting
    ? "select"
    : "quiz";

  /** Loads and persists user-created groups belonging to this quiz. */
  const { savedGroups, saveGroup, updateGroup, deleteGroup } =
    useSavedQuizGroups(countryId, quiz.id);

  /**
   * Feature IDs rendered by the map for the currently active group and optional
   * GeoGuessr-only filter.
   *
   * Without GeoGuessr filtering, Full Quiz continues to use `null` so MapLibre
   * removes all grouping filters. When GeoGuessr Only is enabled, even Full Quiz
   * supplies an explicit feature set because non-GeoGuessr countries must be
   * removed.
   */
  const activeFeatureIds = useMemo(() => {
    if (!isGeoGuessrOnly) {
      return activeGroup.type === "full"
        ? null
        : Array.from(resolvedGroup?.featureIds ?? []);
    }

    /* Full Quiz becomes every GeoGuessr-enabled feature. */
    if (activeGroup.type === "full") {
      return Array.from(geoGuessrFeatureIds);
    }

    /* Property and manual groups are intersected with the GeoGuessr feature set. */
    return Array.from(resolvedGroup?.featureIds ?? []).filter(
      (featureId) => geoGuessrFeatureIds.has(String(featureId)),
    );
  }, [
    activeGroup,
    resolvedGroup,
    isGeoGuessrOnly,
    geoGuessrFeatureIds,
  ]);

  /**
   * Whether the inactive quiz is currently displaying its normal Show Answers
   * view.
   *
   * This state lives alongside the grouping workflow because entering manual
   * feature selection explicitly leaves normal Show Answers mode.
   */
  const [isShowingAnswers, setIsShowingAnswers] = useState(false);

  /**
   * Whether quiz-answer labels are displayed while manually selecting map
   * features.
   */
  const [showManualSelectionAnswers, setShowManualSelectionAnswers] =
    useState(true);

  /** Controls whether the floating quiz Settings panel is currently visible. */
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);

  /** Controls whether the floating quiz Groups panel is currently visible. */
  const [isGroupsOpen, setIsGroupsOpen] = useState(false);

  /** Whether a quiz is currently running on the map. */
  const [isQuizRunning, setIsQuizRunning] = useState(false);

  /** Whether the user is currently being told why Groups cannot be opened. */
  const [isGroupsBlockedMessageOpen, setIsGroupsBlockedMessageOpen] =
    useState(false);

  /**
   * Toggles the normal inactive-quiz Show Answers view.
   */
  function toggleShowAnswers(): void {
    setIsShowingAnswers((wasShowingAnswers) => !wasShowingAnswers);
  }

  /**
   * Opens or closes the Settings panel.
   */
  function toggleSettingsPanel(): void {
    setIsSettingsOpen((wasOpen) => !wasOpen);
  }

  /**
   * Opens or closes the Groups panel.
   *
   * Grouping changes are blocked while a quiz is running because changing the
   * active feature and question subsets during an attempt would invalidate the
   * current quiz state.
   */
  function toggleGroupsPanel(): void {
    if (isQuizRunning) {
      setIsGroupsBlockedMessageOpen(true);

      return;
    }

    setIsGroupsBlockedMessageOpen(false);
    setIsGroupsOpen((wasOpen) => !wasOpen);
  }

  /**
   * Applies an unsaved group and clears any previously active saved group.
   *
   * @param group - Unsaved group that should become active.
   */
  function applyUnsavedGroup(group: ActiveQuizGroup): void {
    setActiveSavedGroupId(null);

    applyGroup(group);
  }

  /**
   * Applies a saved group without clearing its saved-group identity.
   *
   * This is used when creating, loading, or updating a persisted group.
   *
   * @param group - Saved group source that should become active.
   */
  function applySavedGroup(group: ActiveQuizGroup): void {
    applyGroup(group);
  }

  /**
   * Restores the complete quiz and clears any active saved-group selection.
   */
  function handleUseFullQuiz(): void {
    setActiveSavedGroupId(null);

    resetToFullQuiz();
  }

  /**
   * Synchronizes the map's quiz-running state with the surrounding quiz UI.
   *
   * Starting a quiz automatically closes the Groups panel because changing the
   * active grouping while a quiz is underway could invalidate its question and
   * feature state.
   *
   * @param isRunning - Whether a quiz is currently in progress.
   */
  function handleQuizRunningChange(isRunning: boolean): void {
    setIsQuizRunning(isRunning);

    if (!isRunning) {
      return;
    }

    setIsGroupsOpen(false);
    setIsGroupsBlockedMessageOpen(false);
  }

  /**
   * Starts a fresh manual feature-selection session.
   *
   * Manual selection always begins from Full Quiz so every geographic feature
   * is visible and selectable regardless of which property or saved group was
   * previously active.
   *
   * Entering this workflow also leaves the normal quiz Show Answers view because
   * manual selection provides its own independent answer-label control.
   */
  function beginManualSelection(): void {
    /*
     * Manual selection is a new unsaved grouping workflow, so any previously
     * active saved-group identity is cleared.
     */
    setActiveSavedGroupId(null);

    resetToFullQuiz();

    setIsShowingAnswers(false);
    setShowManualSelectionAnswers(true);

    beginSelection();
  }

  /**
   * Starts editing an existing manual saved group.
   *
   * The map returns to Full Quiz before selection begins so features outside the
   * saved group remain visible and can be added to the edit.
   *
   * Normal Show Answers is closed because manual editing provides its own
   * answer-label control.
   *
   * @param featureIds - Feature IDs currently stored by the saved manual group.
   */
  function beginEditingManualGroup(
    featureIds: Iterable<string>,
  ): void {
    resetToFullQuiz();

    setIsShowingAnswers(false);
    setShowManualSelectionAnswers(true);

    /* Start selection mode using the group's persisted feature IDs. */
    beginSelection(featureIds);
  }

  /**
   * Cancels the current manual-selection workflow.
   *
   * Answer visibility is reset to its default so the next manual-selection
   * session starts with labels visible.
   */
  function cancelManualSelection(): void {
    cancelSelection();

    setShowManualSelectionAnswers(true);
  }

  /**
   * Toggles answer-label visibility during manual feature selection.
   */
  function toggleManualSelectionAnswers(): void {
    setShowManualSelectionAnswers((previousValue) => !previousValue);
  }

  /**
   * Toggles a saved group between active and inactive.
   *
   * Selecting an inactive saved group applies its stored source. Selecting the
   * currently active saved group returns to Full Quiz.
   *
   * @param savedGroup - Saved group selected by the user.
   */
  function toggleSavedGroup(savedGroup: SavedQuizGroup): void {
    if (activeSavedGroupId === savedGroup.id) {
      setActiveSavedGroupId(null);

      resetToFullQuiz();

      return;
    }

    setActiveSavedGroupId(savedGroup.id);

    applyGroup(savedGroup.source);
  }

  return (
    <div className="relative h-full w-full">
      {/* Interactive quiz map */}
      <FeatureQuizMap
        mapConfig={mapConfig}
        quiz={filteredActiveQuiz}
        quizSettings={settings}
        areInactiveQuizActionsDisabled={isSelecting}
        clickBehavior={mapClickBehavior}
        activeFeatureIds={activeFeatureIds}
        onFeatureSelect={toggleFeature}
        manualSelectedFeatureIds={selectedFeatureIds}
        showManualSelectionAnswers={
          isSelecting && showManualSelectionAnswers
        }
        isShowingAnswers={isShowingAnswers}
        onToggleShowAnswers={toggleShowAnswers}
        onQuizRunningChange={handleQuizRunningChange}
      />

      {/* Floating Settings and Groups controls */}
      <FeatureQuizPanelControls
        isSettingsOpen={isSettingsOpen}
        isGroupsOpen={isGroupsOpen}
        isGroupsBlockedMessageOpen={isGroupsBlockedMessageOpen}
        onToggleSettings={toggleSettingsPanel}
        onToggleGroups={toggleGroupsPanel}
        onCloseGroupsBlockedMessage={() =>
          setIsGroupsBlockedMessageOpen(false)
        }
        settingsPanel={
          <FeatureQuizSettingsPanel
            settings={settings}
            onChange={setSettings}
          />
        }
        groupsPanel={
          <FeatureQuizGroupsPanel
            quiz={quiz}
            promoteId={mapConfig.promoteId}
            featureCollection={featureCollection}
            activeGroup={activeGroup}
            activeSavedGroupId={activeSavedGroupId}
            savedGroups={savedGroups}
            onApplyGroup={applyUnsavedGroup}
            onApplySavedGroup={applySavedGroup}
            onUseFullQuiz={handleUseFullQuiz}
            onGeoGuessrOnlyChange={setIsGeoGuessrOnly}
            onToggleSavedGroup={toggleSavedGroup}
            onSaveGroup={saveGroup}
            onUpdateGroup={updateGroup}
            onDeleteGroup={deleteGroup}
            isManualSelecting={isSelecting}
            isGeoGuessrOnly={isGeoGuessrOnly}
            manualSelectedFeatureIds={selectedFeatureIds}
            showManualSelectionAnswers={showManualSelectionAnswers}
            onBeginManualSelection={beginManualSelection}
            onBeginEditingManualGroup={beginEditingManualGroup}
            onRemoveManualFeature={removeFeature}
            onClearManualSelection={clearSelection}
            onSelectAllManualFeatures={selectAllFeatures}
            onCancelManualSelection={cancelManualSelection}
            onToggleManualSelectionAnswers={
              toggleManualSelectionAnswers
            }
            onSetActiveSavedGroup={setActiveSavedGroupId}
            isDisabled={false}
          />
        }
      />
    </div>
  );
}

/**
 * Temporary hydrated implementation for location-based town quizzes.
 *
 * The town interaction engine will be implemented separately from the existing
 * GeoJSON feature-selection engine. This placeholder establishes that boundary
 * while feature-quiz behavior remains unchanged.
 *
 * @param props - Town quiz map configuration.
 * @returns An empty map-sized container until the town quiz engine is added.
 */
function HydratedTownQuizMapClient({
  // countryId,
  quiz,
  townConfig,
}: TownQuizMapClientProps) {
  /**
   * Number of population-ranked towns currently participating in the quiz.
   *
   * The complete generated dataset is active initially.
   */
  const [activeTownCount, setActiveTownCount] = useState(
    quiz.towns.length,
  );

  /** Whether the floating town Filter panel is currently visible. */
  const [isFilterOpen, setIsFilterOpen] = useState(false);

  /**
   * Whether the user is currently being told why the Filter panel cannot be
   * opened.
   */
  const [isFilterBlockedMessageOpen, setIsFilterBlockedMessageOpen] =
    useState(false);

  /**
   * Town records consumed by both the quiz engine and Normal-mode label layer.
   *
   * Full Quiz preserves the generated dataset exactly. Numeric filters use the
   * shared population-group helper so the national capital is included even when
   * it falls outside the requested population cutoff.
   */
  const activeTowns = useMemo(() => {
    if (activeTownCount === quiz.towns.length) {
      return quiz.towns;
    }

    return getTownPopulationGroup(quiz.towns, activeTownCount);
  }, [quiz.towns, activeTownCount]);

  const {
    currentQuestion,
    lastResult,

    answeredCount,
    questionCount,

    averageScore,
    totalDistanceKm,

    isActive,
    isFinished,

    startQuiz,
    skipQuestion,
    stopQuiz,
    restartQuiz,

    submitGuess,
  } = useTownQuiz({
    towns: activeTowns,
    maxErrorKm: townConfig.maxErrorKm,
  });

  /**
   * Controls whether the town quiz displays GeoPedia's custom town labels.
   *
   * Mode intentionally resets to Normal whenever the page is recreated rather
   * than being persisted through the feature-quiz settings system.
   */
  const [townQuizMode, setTownQuizMode] =
    useState<TownQuizMode>("normal");

  /**
   * Applies the complete generated town dataset.
   */
  function useFullTownQuiz(): void {
    setActiveTownCount(quiz.towns.length);
  }

  /**
   * Applies a population-ranked town count.
   *
   * @param count - Number of towns that should participate in the quiz.
   */
  function applyTownCount(count: number): void {
    setActiveTownCount(count);
  }

  /**
   * Attempts to open or close the town Filter panel.
   *
   * Filtering cannot change while a quiz attempt is active because doing so would
   * change both the active question collection and the Normal-mode town labels
   * during gameplay.
   *
   * When filtering is blocked, display the same style of explanatory warning used
   * when feature quiz Groups cannot be opened.
   */
  function toggleFilterPanel(): void {
    if (isActive) {
      setIsFilterBlockedMessageOpen(true);

      return;
    }

    setIsFilterBlockedMessageOpen(false);
    setIsFilterOpen((wasOpen) => !wasOpen);
  }

  /**
   * Starts a town quiz after closing all Filter-related floating UI.
   */
  function handleStartQuiz(): void {
    setIsFilterOpen(false);
    setIsFilterBlockedMessageOpen(false);
    startQuiz();
  }

  return (
    <div className="relative h-full w-full">
      <TownQuizMap
        townConfig={townConfig}
        towns={activeTowns}
        mode={townQuizMode}
        isGuessingEnabled={isActive && currentQuestion !== undefined}
        onGuess={submitGuess}
      />

      {/* Town quiz map controls. */}
      <TownQuizPanelControls
        isFilterOpen={isFilterOpen}
        isFilterBlockedMessageOpen={isFilterBlockedMessageOpen}
        onToggleFilter={toggleFilterPanel}
        onCloseFilterBlockedMessage={() => {
          setIsFilterBlockedMessageOpen(false);
        }}
        modeControl={
          <TownQuizModeControl
            mode={townQuizMode}
            onModeChange={setTownQuizMode}
          />
        }
        filterPanel={
          <TownQuizFilterPanel
            availableTownCount={quiz.towns.length}
            activeTownCount={activeTownCount}
            onUseFullQuiz={useFullTownQuiz}
            onApplyTownCount={applyTownCount}
            onClose={() => {
              setIsFilterOpen(false);
            }}
          />
        }
      />

      <TownQuizOverlay
        quizName={quiz.name}
        currentTownName={currentQuestion?.name}

        answeredCount={answeredCount}
        questionCount={questionCount}

        lastScore={lastResult?.score}
        lastDistanceKm={lastResult?.distanceKm}

        averageScore={averageScore}
        totalDistanceKm={totalDistanceKm}

        isActive={isActive}
        isFinished={isFinished}

        onStart={handleStartQuiz}
        onSkip={skipQuestion}
        onStop={stopQuiz}
        onRestart={restartQuiz}
      />
    </div>
  );
}
