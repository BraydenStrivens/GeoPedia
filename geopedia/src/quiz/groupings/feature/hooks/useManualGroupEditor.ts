/**
 * Manages creation and editing of manually selected feature quiz groups.
 *
 * Manual groups are constructed directly from stable map feature IDs rather
 * than GeoJSON grouping-property values.
 *
 * This hook owns:
 *
 * - Selected-feature display information.
 * - Manual-group save metadata.
 * - Manual-group validation.
 * - Manual saved-group change detection.
 * - Saving and updating manual groups.
 * - Select-All feature IDs.
 *
 * The temporary feature selection itself remains owned by
 * useManualGroupSelection because HydratedFeatureQuizMapClient also needs that
 * state to control map interaction and selection presentation.
 */

"use client";

import { useMemo, useState } from "react";

import type { QuizGroupingFeatureCollection } from "@/quiz/groupings/feature/hooks/useQuizGroupingData";
import type {
  QuizGroupSource,
  SavedQuizGroup,
} from "@/quiz/groupings/feature/types";
import { getManualSelectionItems } from "@/quiz/groupings/feature/utils/getManualSelectionItems";
import type { FeatureQuiz } from "@/types/quiz";

/**
 * Parameters required by the manual-group editor.
 */
type UseManualGroupEditorParams = {
  /** Complete quiz definition. */
  quiz: FeatureQuiz;

  /** GeoJSON property promoted to stable map feature IDs. */
  promoteId?: string;

  /** Complete quiz GeoJSON dataset. */
  featureCollection: QuizGroupingFeatureCollection | null;

  /** Feature IDs currently selected by the manual-selection workflow. */
  selectedFeatureIds: ReadonlySet<string>;

  /** Saved group currently being edited, when applicable. */
  editingGroup: SavedQuizGroup | undefined;

  /** Current saved-group edit name. */
  editGroupName: string;

  /** Current saved-group edit description. */
  editGroupDescription: string;

  /** Creates and persists a new saved group. */
  onSaveGroup: (
    name: string,
    description: string | undefined,
    source: QuizGroupSource,
  ) => SavedQuizGroup;

  /** Updates an existing saved group. */
  onUpdateGroup: (
    groupId: string,
    name: string,
    description: string | undefined,
    source: QuizGroupSource,
  ) => void;

  /** Applies a saved group without clearing its saved identity. */
  onApplySavedGroup: (group: QuizGroupSource) => void;

  /** Marks a saved group as active. */
  onSetActiveSavedGroup: (groupId: string | null) => void;

  /** Clears temporary manual-selection state and exits select mode. */
  onCancelManualSelection: () => void;
};

/**
 * State and controls returned by the manual-group editor.
 */
type UseManualGroupEditorResult = {
  /** Selected features together with their displayed quiz answers. */
  selectionItems: ReturnType<typeof getManualSelectionItems>;

  /** Number of distinct quiz answers represented by the selection. */
  selectionAnswerCount: number;

  /** Stable IDs of every feature available to manual selection. */
  allFeatureIds: string[];

  /** Whether the current manual selection can be saved. */
  canSaveManualGroup: boolean;

  /** Whether the manual save metadata is valid. */
  canConfirmManualSave: boolean;

  /** Whether the current manual saved-group edit can be persisted. */
  canUpdateManualGroup: boolean;

  /** Whether a new manual group's metadata form is open. */
  isSavingManualGroup: boolean;

  /** Name draft for a new manual group. */
  newManualGroupName: string;

  /** Description draft for a new manual group. */
  newManualGroupDescription: string;

  /** Updates the new manual-group name. */
  setNewManualGroupName: (name: string) => void;

  /** Updates the new manual-group description. */
  setNewManualGroupDescription: (description: string) => void;

  /** Opens the new manual-group metadata form. */
  beginSavingManualGroup: () => void;

  /** Cancels new manual-group saving. */
  cancelSavingManualGroup: () => void;

  /** Persists the current manual selection as a new saved group. */
  saveCurrentManualGroup: () => void;

  /** Persists edits to the current manual saved group. */
  updateEditingManualGroup: () => void;
};

/**
 * Manages derived data, validation, saving, and updating for manual groups.
 *
 * @param params - Quiz data, manual selection, edit metadata, and callbacks.
 * @returns Manual-group editor state and controls.
 */
export function useManualGroupEditor({
  quiz,
  promoteId,
  featureCollection,
  selectedFeatureIds,

  editingGroup,
  editGroupName,
  editGroupDescription,

  onSaveGroup,
  onUpdateGroup,
  onApplySavedGroup,
  onSetActiveSavedGroup,
  onCancelManualSelection,
}: UseManualGroupEditorParams): UseManualGroupEditorResult {
  /** Whether the new manual saved-group metadata form is open. */
  const [isSavingManualGroup, setIsSavingManualGroup] =
    useState(false);

  /** Name draft for a new manually selected saved group. */
  const [newManualGroupName, setNewManualGroupName] = useState("");

  /** Description draft for a new manually selected saved group. */
  const [newManualGroupDescription, setNewManualGroupDescription] =
    useState("");

  /** Selected features together with their represented quiz answers. */
  const selectionItems = useMemo(
    () =>
      getManualSelectionItems(
        featureCollection,
        promoteId,
        quiz,
        selectedFeatureIds,
      ),
    [featureCollection, promoteId, quiz, selectedFeatureIds],
  );

  /** Number of distinct quiz answers represented by selected features. */
  const selectionAnswerCount = useMemo(() => {
    const answers = new Set<string>();

    for (const selectionItem of selectionItems) {
      for (const answer of selectionItem.answers) {
        answers.add(answer);
      }
    }

    return answers.size;
  }, [selectionItems]);

  /** Stable IDs of every feature available to manual grouping. */
  const allFeatureIds = useMemo(() => {
    if (!featureCollection || !promoteId) {
      return [];
    }

    return featureCollection.features
      .map((feature) => feature.properties?.[promoteId])
      .filter(
        (featureId): featureId is string | number =>
          typeof featureId === "string" ||
          typeof featureId === "number",
      )
      .map(String);
  }, [featureCollection, promoteId]);

  /**
   * Whether the current manual feature selection represents a meaningful saved
   * subset.
   *
   * A saved manual group must contain at least one feature while remaining
   * smaller than the complete quiz. Selecting every available feature would
   * duplicate Full Quiz.
   */
  const hasValidSavedManualSelection =
    selectedFeatureIds.size > 0 &&
    selectedFeatureIds.size < allFeatureIds.length;

  /** Whether the current manual selection can become a saved group. */
  const canSaveManualGroup = hasValidSavedManualSelection;

  /** Whether the new manual-group metadata is valid. */
  const canConfirmManualSave =
    canSaveManualGroup && newManualGroupName.trim().length > 0;

  /** Whether the saved group currently being edited is feature-based. */
  const isEditingManualGroup =
    editingGroup?.source.type === "features";

  /** Whether the manual edit draft differs from persisted saved-group data. */
  const hasManualEditChanges = useMemo(() => {
    if (!editingGroup || editingGroup.source.type !== "features") {
      return false;
    }

    const savedDescription = editingGroup.description ?? "";

    const nameChanged = editGroupName.trim() !== editingGroup.name;

    const descriptionChanged =
      editGroupDescription.trim() !== savedDescription;

    const featureIdsChanged =
      editingGroup.source.featureIds.length !==
        selectedFeatureIds.size ||
      !editingGroup.source.featureIds.every((featureId) =>
        selectedFeatureIds.has(featureId),
      );

    return nameChanged || descriptionChanged || featureIdsChanged;
  }, [
    editingGroup,
    editGroupName,
    editGroupDescription,
    selectedFeatureIds,
  ]);

  /**
   * Whether the manual saved-group edit may be persisted.
   *
   * Manual groups require a name, at least one selected feature, fewer than all
   * available features, and at least one actual change.
   */
  const canUpdateManualGroup =
    isEditingManualGroup &&
    editGroupName.trim().length > 0 &&
    selectedFeatureIds.size > 0 &&
    selectedFeatureIds.size < allFeatureIds.length &&
    hasManualEditChanges;

  /**
   * Opens the metadata form for the current manual selection.
   */
  function beginSavingManualGroup(): void {
    if (!canSaveManualGroup) {
      return;
    }

    setIsSavingManualGroup(true);
  }

  /**
   * Cancels manual-group saving while preserving the selected features.
   */
  function cancelSavingManualGroup(): void {
    setIsSavingManualGroup(false);
    setNewManualGroupName("");
    setNewManualGroupDescription("");
  }

  /**
   * Saves the current manual feature selection and makes it active.
   */
  function saveCurrentManualGroup(): void {
    if (!canConfirmManualSave) {
      return;
    }

    const source: QuizGroupSource = {
      type: "features",
      featureIds: Array.from(selectedFeatureIds),
    };

    const savedGroup = onSaveGroup(
      newManualGroupName,
      newManualGroupDescription.trim() || undefined,
      source,
    );

    onApplySavedGroup(savedGroup.source);
    onSetActiveSavedGroup(savedGroup.id);

    /*
     * The persisted group now owns the active feature subset. Temporary
     * selection state is no longer needed and its blue overlay should clear.
     */
    onCancelManualSelection();

    cancelSavingManualGroup();
  }

  /**
   * Persists edits made to the current manual saved group.
   */
  function updateEditingManualGroup(): void {
    if (
      !canUpdateManualGroup ||
      !editingGroup ||
      editingGroup.source.type !== "features"
    ) {
      return;
    }

    const updatedSource: QuizGroupSource = {
      type: "features",
      featureIds: Array.from(selectedFeatureIds),
    };

    onUpdateGroup(
      editingGroup.id,
      editGroupName,
      editGroupDescription.trim() || undefined,
      updatedSource,
    );

    onApplySavedGroup(updatedSource);
    onSetActiveSavedGroup(editingGroup.id);

    /*
     * Manual selection is editor-only state. Once Update succeeds, return to
     * the normal saved-group map presentation.
     */
    onCancelManualSelection();
  }

  return {
    selectionItems,
    selectionAnswerCount,
    allFeatureIds,

    canSaveManualGroup,
    canConfirmManualSave,
    canUpdateManualGroup,

    isSavingManualGroup,
    newManualGroupName,
    newManualGroupDescription,

    setNewManualGroupName,
    setNewManualGroupDescription,

    beginSavingManualGroup,
    cancelSavingManualGroup,
    saveCurrentManualGroup,
    updateEditingManualGroup,
  };
}
