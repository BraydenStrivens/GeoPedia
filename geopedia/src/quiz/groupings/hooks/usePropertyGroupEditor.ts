/**
 * Manages GeoPedia's property-based quiz-group creation and editing workflow.
 *
 * Property groups are constructed from values stored on GeoJSON properties,
 * such as:
 *
 * - Census regions.
 * - State abbreviations.
 * - Administrative regions.
 *
 * This hook owns:
 *
 * - The grouping property currently being edited.
 * - The selected raw GeoJSON property values.
 * - New property-group metadata.
 * - Property-group validation.
 * - Property-group creation and updating.
 * - Immediate map/quiz preview while property values change.
 *
 * Cross-workflow state, such as which saved group is currently being edited,
 * remains owned by QuizGroupsPanel.
 */

"use client";

import { useMemo, useState } from "react";

import type { QuizGroupingFeatureCollection } from "@/quiz/groupings/hooks/useQuizGroupingData";
import type {
  ActiveQuizGroup,
  PropertyQuizGroupSource,
  QuizGroupingProperty,
  QuizGroupSource,
  SavedQuizGroup,
} from "@/quiz/groupings/types";
import { getGroupingOptions } from "@/quiz/groupings/utils/getGroupingOptions";
import type { Quiz } from "@/types/quiz";

/**
 * Parameters required by the property-group editor.
 */
type UsePropertyGroupEditorParams = {
  /** Complete quiz definition containing optional grouping configuration. */
  quiz: Quiz;

  /** Loaded GeoJSON used to discover available grouping values. */
  featureCollection: QuizGroupingFeatureCollection | null;

  /** Group currently controlling the quiz. */
  activeGroup: ActiveQuizGroup;

  /** ID of the saved group currently controlling the quiz. */
  activeSavedGroupId: string | null;

  /** Saved group currently being edited, when applicable. */
  editingGroup: SavedQuizGroup | undefined;

  /** Current saved-group edit name. */
  editGroupName: string;

  /** Current saved-group edit description. */
  editGroupDescription: string;

  /** Whether grouping interactions are currently disabled. */
  isDisabled: boolean;

  /** Applies a temporary unsaved group. */
  onApplyGroup: (group: ActiveQuizGroup) => void;

  /** Applies a saved-group preview without clearing saved-group identity. */
  onApplySavedGroup: (group: ActiveQuizGroup) => void;

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

  /** Marks a saved group as active. */
  onSetActiveSavedGroup: (groupId: string | null) => void;

  /** Restores Full Quiz. */
  onUseFullQuiz: () => void;
};

/**
 * Values and controls returned by the property-group editor.
 */
type UsePropertyGroupEditorResult = {
  /** Property currently used to construct groups. */
  selectedGroupingProperty: QuizGroupingProperty | null;

  /** Raw GeoJSON values currently selected. */
  selectedValues: Set<string>;

  /** Options available for the selected grouping property. */
  groupingOptions: ReturnType<typeof getGroupingOptions>;

  /** Whether the new property-group form is currently open. */
  isSavingPropertyGroup: boolean;

  /** Name draft for a new property group. */
  newPropertyGroupName: string;

  /** Description draft for a new property group. */
  newPropertyGroupDescription: string;

  /** Whether a new property group may begin being saved. */
  canBeginSavingPropertyGroup: boolean;

  /** Whether the current new property group can be persisted. */
  canSavePropertyGroup: boolean;

  /** Whether the current property-group edit can be persisted. */
  canUpdatePropertyGroup: boolean;

  /** Updates the new property-group name draft. */
  setNewPropertyGroupName: (name: string) => void;

  /** Updates the new property-group description draft. */
  setNewPropertyGroupDescription: (description: string) => void;

  /** Toggles one grouping-property value. */
  togglePropertyValue: (value: string) => void;

  /** Clears every selected property value. */
  clearPropertySelection: () => void;

  /** Changes which GeoJSON property is used for grouping. */
  changeGroupingProperty: (propertyName: string) => void;

  /** Loads a saved property-group source into the editor. */
  loadPropertyGroup: (source: PropertyQuizGroupSource) => boolean;

  /** Opens the new property-group metadata form. */
  beginSavingPropertyGroup: () => void;

  /** Cancels new property-group creation. */
  cancelSavingPropertyGroup: () => void;

  /** Persists the current new property group. */
  saveCurrentPropertyGroup: () => void;

  /** Persists edits to the current saved property group. */
  updateEditingPropertyGroup: () => void;
};

/**
 * Returns property values that should initially appear checked.
 *
 * @param activeGroup - Group currently applied to the quiz.
 * @param groupingProperty - Property initially shown by the editor.
 * @returns Raw property values that should initially be selected.
 */
function getInitialSelectedValues(
  activeGroup: ActiveQuizGroup,
  groupingProperty: QuizGroupingProperty | null,
): Set<string> {
  if (
    activeGroup.type !== "property" ||
    !groupingProperty ||
    activeGroup.property !== groupingProperty.property
  ) {
    return new Set();
  }

  return new Set(activeGroup.values);
}

/**
 * Manages the complete property-group editor workflow.
 *
 * @param params - Quiz data, saved-group edit state, and persistence callbacks.
 * @returns Property-group state, derived validation, and controls.
 */
export function usePropertyGroupEditor({
  quiz,
  featureCollection,
  activeGroup,
  activeSavedGroupId,
  editingGroup,
  editGroupName,
  editGroupDescription,
  isDisabled,
  onApplyGroup,
  onApplySavedGroup,
  onSaveGroup,
  onUpdateGroup,
  onSetActiveSavedGroup,
  onUseFullQuiz,
}: UsePropertyGroupEditorParams): UsePropertyGroupEditorResult {
  /** Property currently being used to construct a property group. */
  const [selectedGroupingProperty, setSelectedGroupingProperty] =
    useState<QuizGroupingProperty | null>(
      quiz.grouping?.properties[0] ?? null,
    );

  /** Raw GeoJSON grouping values currently selected by the user. */
  const [selectedValues, setSelectedValues] = useState<Set<string>>(
    () =>
      getInitialSelectedValues(activeGroup, selectedGroupingProperty),
  );

  /** Whether the new property-group metadata form is open. */
  const [isSavingPropertyGroup, setIsSavingPropertyGroup] =
    useState(false);

  /** Name draft for a new property group. */
  const [newPropertyGroupName, setNewPropertyGroupName] =
    useState("");

  /** Description draft for a new property group. */
  const [
    newPropertyGroupDescription,
    setNewPropertyGroupDescription,
  ] = useState("");

  /** Available grouping options discovered from the current GeoJSON property. */
  const groupingOptions = useMemo(() => {
    if (!featureCollection || !selectedGroupingProperty) {
      return [];
    }

    return getGroupingOptions(
      featureCollection,
      selectedGroupingProperty,
    );
  }, [featureCollection, selectedGroupingProperty]);

  /** Whether the current saved group is a property-based group. */
  const isEditingPropertyGroup =
    editingGroup?.source.type === "property";

  /** Whether the property edit draft differs from persisted saved-group data. */
  const hasPropertyEditChanges = useMemo(() => {
    if (
      !editingGroup ||
      editingGroup.source.type !== "property" ||
      !selectedGroupingProperty
    ) {
      return false;
    }

    const savedDescription = editingGroup.description ?? "";

    const nameChanged = editGroupName.trim() !== editingGroup.name;

    const descriptionChanged =
      editGroupDescription.trim() !== savedDescription;

    const propertyChanged =
      selectedGroupingProperty.property !==
      editingGroup.source.property;

    const selectedValuesChanged =
      editingGroup.source.values.length !== selectedValues.size ||
      !editingGroup.source.values.every((value) =>
        selectedValues.has(value),
      );

    return (
      nameChanged ||
      descriptionChanged ||
      propertyChanged ||
      selectedValuesChanged
    );
  }, [
    editingGroup,
    editGroupName,
    editGroupDescription,
    selectedGroupingProperty,
    selectedValues,
  ]);

  /**
   * Whether the current property selection represents a meaningful new saved
   * group.
   *
   * A one-value property group remains easy to reconstruct directly from the
   * property list, while selecting every value would duplicate Full Quiz.
   */
  const canBeginSavingPropertyGroup =
    !isDisabled &&
    selectedValues.size > 1 &&
    selectedValues.size < groupingOptions.length &&
    activeSavedGroupId === null;

  /** Whether the new property-group metadata is valid. */
  const canSavePropertyGroup =
    canBeginSavingPropertyGroup &&
    newPropertyGroupName.trim().length > 0;

  /** Whether the current property saved-group edit can be persisted. */
  const canUpdatePropertyGroup =
    !isDisabled &&
    isEditingPropertyGroup &&
    editGroupName.trim().length > 0 &&
    selectedValues.size > 0 &&
    hasPropertyEditChanges;

  /**
   * Applies a property selection immediately to the map and quiz.
   *
   * Property changes made while editing a saved property group preserve its
   * saved-group identity. Normal changes become an unsaved active group.
   *
   * @param values - Raw property values that should become active.
   */
  function applyPropertySelection(values: Set<string>): void {
    if (!selectedGroupingProperty) {
      return;
    }

    if (values.size === 0 && !isEditingPropertyGroup) {
      onUseFullQuiz();

      return;
    }

    const group: ActiveQuizGroup = {
      type: "property",
      property: selectedGroupingProperty.property,
      values: Array.from(values),
    };

    if (isEditingPropertyGroup) {
      onApplySavedGroup(group);

      return;
    }

    onApplyGroup(group);
  }

  /**
   * Adds or removes one raw grouping value and immediately previews the result.
   *
   * @param value - Raw GeoJSON grouping value to toggle.
   */
  function togglePropertyValue(value: string): void {
    const updatedValues = new Set(selectedValues);

    if (updatedValues.has(value)) {
      updatedValues.delete(value);
    } else {
      updatedValues.add(value);
    }

    setSelectedValues(updatedValues);

    applyPropertySelection(updatedValues);
  }

  /**
   * Clears every property value and immediately updates the active quiz.
   */
  function clearPropertySelection(): void {
    const emptySelection = new Set<string>();

    setSelectedValues(emptySelection);

    applyPropertySelection(emptySelection);
  }

  /**
   * Changes which GeoJSON property is being used for grouping.
   *
   * Existing selections are cleared because their values belong to a different
   * grouping dimension.
   *
   * @param propertyName - GeoJSON property selected by the user.
   */
  function changeGroupingProperty(propertyName: string): void {
    const property =
      quiz.grouping?.properties.find(
        (candidate) => candidate.property === propertyName,
      ) ?? null;

    setSelectedGroupingProperty(property);
    setSelectedValues(new Set());

    cancelSavingPropertyGroup();
  }

  /**
   * Loads a saved property source into the Property Groups editor.
   *
   * @param source - Persisted property-group source to restore.
   * @returns Whether the source's grouping property exists in the quiz config.
   */
  function loadPropertyGroup(
    source: PropertyQuizGroupSource,
  ): boolean {
    const groupingProperty = quiz.grouping?.properties.find(
      (property) => property.property === source.property,
    );

    if (!groupingProperty) {
      return false;
    }

    setSelectedGroupingProperty(groupingProperty);
    setSelectedValues(new Set(source.values));

    return true;
  }

  /**
   * Opens the metadata form for a new property group.
   */
  function beginSavingPropertyGroup(): void {
    if (!canBeginSavingPropertyGroup) {
      return;
    }

    setIsSavingPropertyGroup(true);
  }

  /**
   * Cancels new property-group creation and clears its metadata draft.
   */
  function cancelSavingPropertyGroup(): void {
    setIsSavingPropertyGroup(false);
    setNewPropertyGroupName("");
    setNewPropertyGroupDescription("");
  }

  /**
   * Saves the current property selection and makes the new saved group active.
   */
  function saveCurrentPropertyGroup(): void {
    if (!canSavePropertyGroup || !selectedGroupingProperty) {
      return;
    }

    const source: QuizGroupSource = {
      type: "property",
      property: selectedGroupingProperty.property,
      values: Array.from(selectedValues),
    };

    const savedGroup = onSaveGroup(
      newPropertyGroupName,
      newPropertyGroupDescription.trim() || undefined,
      source,
    );

    onApplySavedGroup(savedGroup.source);
    onSetActiveSavedGroup(savedGroup.id);

    cancelSavingPropertyGroup();
  }

  /**
   * Persists edits made to the current saved property group.
   */
  function updateEditingPropertyGroup(): void {
    if (
      !canUpdatePropertyGroup ||
      !editingGroup ||
      editingGroup.source.type !== "property" ||
      !selectedGroupingProperty
    ) {
      return;
    }

    const updatedSource: QuizGroupSource = {
      type: "property",
      property: selectedGroupingProperty.property,
      values: Array.from(selectedValues),
    };

    onUpdateGroup(
      editingGroup.id,
      editGroupName,
      editGroupDescription.trim() || undefined,
      updatedSource,
    );

    onApplySavedGroup(updatedSource);
    onSetActiveSavedGroup(editingGroup.id);
  }

  return {
    selectedGroupingProperty,
    selectedValues,
    groupingOptions,

    isSavingPropertyGroup,
    newPropertyGroupName,
    newPropertyGroupDescription,

    canBeginSavingPropertyGroup,
    canSavePropertyGroup,
    canUpdatePropertyGroup,

    setNewPropertyGroupName,
    setNewPropertyGroupDescription,

    togglePropertyValue,
    clearPropertySelection,
    changeGroupingProperty,
    loadPropertyGroup,

    beginSavingPropertyGroup,
    cancelSavingPropertyGroup,
    saveCurrentPropertyGroup,
    updateEditingPropertyGroup,
  };
}
