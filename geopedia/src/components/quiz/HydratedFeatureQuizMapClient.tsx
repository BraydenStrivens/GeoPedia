/**
 * Coordinates GeoPedia's hydrated feature-based quiz experience.
 *
 * This component connects a feature quiz to its persisted settings, GeoJSON
 * grouping data, saved groups, manual feature-selection workflow, optional
 * GeoGuessr filtering, map interaction state, and floating quiz panels.
 *
 * Feature-specific orchestration lives here so the shared `QuizMapClient`
 * hydration boundary does not need to understand the internal state or
 * workflows of feature quizzes.
 */

"use client";

import { useMemo, useState } from "react";

import FeatureQuizMap from "@/components/map/FeatureQuizMap";
import FeatureQuizPanelControls from "@/components/quiz/controls/feature/FeatureQuizPanelControls";
import FeatureQuizGroupsPanel from "@/components/quiz/panel/feature/FeatureQuizGroupsPanel";
import FeatureQuizSettingsPanel from "@/components/quiz/panel/feature/FeatureQuizSettingsPanel";
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
import { useFeatureQuizSettings } from "@/quiz/hooks/useFeatureQuizSettings";
import type { FeatureQuiz } from "@/types/quiz";

/**
 * Props required by the hydrated feature quiz client.
 */
type HydratedFeatureQuizMapClientProps = {
  /** Country containing the quiz and its persisted user state. */
  countryId: string;

  /** Feature quiz displayed and controlled by the map. */
  quiz: FeatureQuiz;

  /** Geographic configuration rendered by the feature quiz map. */
  mapConfig: MapConfig;
};

/**
 * Coordinates a hydrated GeoJSON feature-based quiz and its surrounding UI.
 *
 * @param props - Feature quiz client properties.
 * @param props.countryId - Country used to identify persisted quiz data.
 * @param props.quiz - Feature quiz definition.
 * @param props.mapConfig - Geographic configuration rendered by the map.
 * @returns The hydrated feature quiz map and its floating controls.
 */
export default function HydratedFeatureQuizMapClient({
  countryId,
  quiz,
  mapConfig,
}: HydratedFeatureQuizMapClientProps) {
  /** Persisted settings belonging specifically to this feature quiz. */
  const { settings, setSettings } = useFeatureQuizSettings(
    countryId,
    quiz.id,
  );

  /** Loads the feature quiz's GeoJSON for React-side grouping logic. */
  const { featureCollection } = useQuizGroupingData(
    mapConfig.geojsonUrl,
  );

  /**
   * ID of the saved group currently applied to the feature quiz.
   *
   * `null` means Full Quiz or an unsaved temporary group is active.
   */
  const [activeSavedGroupId, setActiveSavedGroupId] = useState<
    string | null
  >(null);

  /**
   * Whether the current feature quiz should include only geographic features
   * available in GeoGuessr.
   *
   * This filter is independent of the active quiz group, allowing it to combine
   * with Full Quiz, property groups, saved groups, and manual groups.
   *
   * This feature is only available for global quizzes.
   */
  const [isGeoGuessrOnly, setIsGeoGuessrOnly] = useState(false);

  /**
   * Owns the group currently applied to the feature quiz and derives its
   * geographic feature and question subsets.
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
   * The GeoGuessr flag is stored directly on the world-country GeoJSON
   * features. Maps without that property naturally produce an empty set and
   * therefore do not expose GeoGuessr-only filtering behavior.
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
    }

    return answers;
  }, [featureCollection, quiz.answerProperty]);

  /**
   * Feature quiz definition actually supplied to the interactive map.
   *
   * The active group is resolved first by `useActiveQuizGroup`. GeoGuessr Only
   * then acts as a second independent filter over that already-resolved
   * question set.
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
   * Manual-selection mode temporarily replaces normal feature quiz clicking
   * with feature-selection behavior.
   */
  const mapClickBehavior: QuizMapClickBehavior = isSelecting
    ? "select"
    : "quiz";

  /** Loads and persists user-created groups belonging to this feature quiz. */
  const { savedGroups, saveGroup, updateGroup, deleteGroup } =
    useSavedQuizGroups(countryId, quiz.id);

  /**
   * Feature IDs rendered by the map for the currently active group and optional
   * GeoGuessr-only filter.
   *
   * Without GeoGuessr filtering, Full Quiz continues to use `null` so MapLibre
   * removes all grouping filters. When GeoGuessr Only is enabled, even Full
   * Quiz supplies an explicit feature set because non-GeoGuessr countries must
   * be removed.
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

    /*
     * Property and manual groups are intersected with the GeoGuessr feature
     * set.
     */
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
   * Whether the inactive feature quiz is currently displaying its normal Show
   * Answers view.
   *
   * This state lives alongside the grouping workflow because entering manual
   * feature selection explicitly leaves normal Show Answers mode.
   */
  const [isShowingAnswers, setIsShowingAnswers] = useState(false);

  /**
   * Whether feature quiz answer labels are displayed while manually selecting
   * map features.
   */
  const [showManualSelectionAnswers, setShowManualSelectionAnswers] =
    useState(true);

  /** Controls whether the feature quiz Settings panel is currently visible. */
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);

  /** Controls whether the feature quiz Groups panel is currently visible. */
  const [isGroupsOpen, setIsGroupsOpen] = useState(false);

  /** Whether the feature quiz is currently running on the map. */
  const [isQuizRunning, setIsQuizRunning] = useState(false);

  /** Whether the user is being told why feature Groups cannot be opened. */
  const [isGroupsBlockedMessageOpen, setIsGroupsBlockedMessageOpen] =
    useState(false);

  /**
   * Toggles the normal inactive feature quiz Show Answers view.
   */
  function toggleShowAnswers(): void {
    setIsShowingAnswers((wasShowingAnswers) => !wasShowingAnswers);
  }

  /**
   * Opens or closes the feature quiz Settings panel.
   */
  function toggleSettingsPanel(): void {
    setIsSettingsOpen((wasOpen) => !wasOpen);
  }

  /**
   * Opens or closes the feature quiz Groups panel.
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
   * Applies an unsaved feature group and clears any previously active saved
   * group.
   *
   * @param group - Unsaved feature group that should become active.
   */
  function applyUnsavedGroup(group: ActiveQuizGroup): void {
    setActiveSavedGroupId(null);

    applyGroup(group);
  }

  /**
   * Applies a saved feature group without clearing its saved-group identity.
   *
   * This is used when creating, loading, or updating a persisted group.
   *
   * @param group - Saved group source that should become active.
   */
  function applySavedGroup(group: ActiveQuizGroup): void {
    applyGroup(group);
  }

  /**
   * Restores the complete feature quiz and clears any active saved-group
   * selection.
   */
  function useFullQuiz(): void {
    setActiveSavedGroupId(null);

    resetToFullQuiz();
  }

  /**
   * Synchronizes the feature map's quiz-running state with the surrounding UI.
   *
   * Starting a quiz automatically closes the Groups panel because changing the
   * active grouping while a quiz is underway could invalidate its question and
   * feature state.
   *
   * @param isRunning - Whether the feature quiz is currently in progress.
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
   * Entering this workflow also leaves the normal quiz Show Answers view
   * because manual selection provides its own independent answer-label control.
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
   * The map returns to Full Quiz before selection begins so features outside
   * the saved group remain visible and can be added to the edit.
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
   * Toggles a saved feature group between active and inactive.
   *
   * Selecting an inactive saved group applies its stored source. Selecting the
   * currently active saved group returns to Full Quiz.
   *
   * @param savedGroup - Saved feature group selected by the user.
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
      {/* Interactive feature quiz map */}
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

      {/* Floating feature quiz Settings and Groups controls */}
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
            onUseFullQuiz={useFullQuiz}
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
          />
        }
      />
    </div>
  );
}
