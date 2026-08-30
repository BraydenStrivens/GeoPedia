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

import QuizMap from "@/components/map/QuizMap";
import QuizPanelControls from "@/components/quiz/controls/QuizPanelControls";
import QuizGroupsPanel from "@/components/quiz/groupings/QuizGroupsPanel";
import QuizSettingsPanel from "@/components/quiz/QuizSettingsPanel";
import { getFeatureAnswers } from "@/maps/labels/featureAnswers";
import type { MapConfig, QuizMapClickBehavior } from "@/maps/types";
import { useActiveQuizGroup } from "@/quiz/groupings/hooks/useActiveQuizGroup";
import { useManualGroupSelection } from "@/quiz/groupings/hooks/useManualGroupSelection";
import { useQuizGroupingData } from "@/quiz/groupings/hooks/useQuizGroupingData";
import { useSavedQuizGroups } from "@/quiz/groupings/hooks/useSavedQuizGroups";
import type {
  ActiveQuizGroup,
  SavedQuizGroup,
} from "@/quiz/groupings/types";
import { useQuizSettings } from "@/quiz/hooks/useQuizSettings";
import type { Quiz } from "@/types/quiz";

/**
 * Props required to render a client-side quiz map.
 */
type QuizMapClientProps = {
  /** Country containing the quiz. Used to identify persisted user data. */
  countryId: string;

  /** Quiz displayed and controlled by the map. */
  quiz: Quiz;

  /** Geographic map configuration used by the quiz. */
  mapConfig: MapConfig;
};

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
 * Renders the interactive quiz map after client hydration has completed.
 *
 * This component coordinates persisted quiz settings, grouping state, saved
 * groups, manual feature selection, and temporary floating-panel state.
 *
 * @param props - Quiz map configuration.
 * @param props.countryId - Country used to identify persisted quiz data.
 * @param props.quiz - Complete quiz definition.
 * @param props.mapConfig - Geographic configuration rendered by the map.
 * @returns The hydrated quiz map and its floating controls.
 */
function HydratedQuizMapClient({
  countryId,
  quiz,
  mapConfig,
}: QuizMapClientProps) {
  /** Persisted settings belonging specifically to this country and quiz. */
  const { settings, setSettings } = useQuizSettings(
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
      <QuizMap
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
      <QuizPanelControls
        isSettingsOpen={isSettingsOpen}
        isGroupsOpen={isGroupsOpen}
        isGroupsBlockedMessageOpen={isGroupsBlockedMessageOpen}
        onToggleSettings={toggleSettingsPanel}
        onToggleGroups={toggleGroupsPanel}
        onCloseGroupsBlockedMessage={() =>
          setIsGroupsBlockedMessageOpen(false)
        }
        settingsPanel={
          <QuizSettingsPanel
            settings={settings}
            onChange={setSettings}
          />
        }
        groupsPanel={
          <QuizGroupsPanel
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
