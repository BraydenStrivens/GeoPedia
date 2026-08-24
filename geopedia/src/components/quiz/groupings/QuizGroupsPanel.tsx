/**
 * Displays the controls used to choose which geographic features and
 * questions belong to the current quiz.
 *
 * The Groups panel supports:
 *
 * - Returning to the complete Full Quiz.
 * - Creating temporary groups from configured GeoJSON property values.
 * - Saving property groups with a name and optional description.
 * - Loading and unloading previously saved groups.
 *
 * Manual map selection and saved-group editing will be added as separate
 * grouping workflows.
 */

"use client";

import { useMemo, useState } from "react";

import { getGroupingOptions } from "@/quiz/groupings/getGroupingOptions";
import type {
  ActiveQuizGroup,
  QuizGroupingProperty,
  QuizGroupSource,
  SavedQuizGroup,
} from "@/quiz/groupings/types";
import type { QuizGroupingFeatureCollection } from "@/quiz/groupings/useQuizGroupingData";
import type { Quiz } from "@/types/quiz";

/**
 * Props required by the quiz Groups panel.
 */
type QuizGroupsPanelProps = {
  /** Complete quiz definition containing grouping configuration. */
  quiz: Quiz;

  /** Loaded GeoJSON used to discover available grouping values. */
  featureCollection: QuizGroupingFeatureCollection | null;

  /** Group currently applied to the quiz. */
  activeGroup: ActiveQuizGroup;

  /** Groups previously saved for this quiz. */
  savedGroups: SavedQuizGroup[];

  /** ID of the saved group currently applied to the quiz. */
  activeSavedGroupId: string | null;

  /**
   * Applies an unsaved group to the quiz.
   *
   * Applying through this callback clears any active saved-group identity.
   */
  onApplyGroup: (group: ActiveQuizGroup) => void;

  /** Updates an existing saved group's metadata and selection. */
  onUpdateGroup: (
    groupId: string,
    name: string,
    description: string | undefined,
    source: QuizGroupSource,
  ) => void;

  /** Permanently removes a saved group. */
  onDeleteGroup: (groupId: string) => void;

  /**
   * Applies the source of a saved group without clearing its saved-group
   * identity.
   */
  onApplySavedGroup: (group: ActiveQuizGroup) => void;

  /** Creates and persists a new saved group. */
  onSaveGroup: (
    name: string,
    description: string | undefined,
    source: QuizGroupSource,
  ) => SavedQuizGroup;

  /** Marks a saved group as the currently active saved group. */
  onSetActiveSavedGroup: (groupId: string | null) => void;

  /** Restores the complete unfiltered quiz. */
  onUseFullQuiz: () => void;

  /** Loads or unloads a saved group. */
  onToggleSavedGroup: (group: SavedQuizGroup) => void;

  /** Whether grouping changes are currently allowed. */
  isDisabled: boolean;
};

/**
 * Returns the property values that should initially appear selected in the
 * panel based on the currently active quiz group.
 *
 * Only property-based groups populate the checkbox selection. Full Quiz and
 * manually selected groups begin with no property values selected.
 *
 * @param activeGroup - Group currently applied to the quiz.
 * @param groupingProperty - Property currently shown by the panel.
 * @returns Raw GeoJSON values that should appear checked.
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
 * Displays the Groups sidebar for a quiz.
 *
 * @param props - Grouping configuration, current state, and group callbacks.
 * @returns Controls for Full Quiz, saved groups, and property-based groups.
 */
export default function QuizGroupsPanel({
  quiz,
  featureCollection,

  activeGroup,
  activeSavedGroupId,
  savedGroups,

  onApplyGroup,
  onApplySavedGroup,
  onUseFullQuiz,
  onToggleSavedGroup,
  onSaveGroup,
  onUpdateGroup,
  onDeleteGroup,
  onSetActiveSavedGroup,

  isDisabled,
}: QuizGroupsPanelProps) {
  /**
   * Property currently being used to construct a temporary group.
   *
   * The first supported grouping property is selected by default.
   */
  const [selectedGroupingProperty, setSelectedGroupingProperty] =
    useState<QuizGroupingProperty | null>(
      quiz.grouping?.properties[0] ?? null,
    );

  /**
   * Raw GeoJSON grouping values currently selected by the user.
   *
   * The initial values reflect the active property group so closing and
   * reopening the panel restores its current checkbox selection.
   */
  const [selectedValues, setSelectedValues] = useState<Set<string>>(
    () =>
      getInitialSelectedValues(activeGroup, selectedGroupingProperty),
  );

  /** Whether the Property Groups section is currently creating a saved group. */
  const [isSavingGroup, setIsSavingGroup] = useState(false);

  /** User-entered name for the saved group currently being created. */
  const [saveGroupName, setSaveGroupName] = useState("");

  /**
   * Optional user-entered description for the saved group currently being
   * created.
   */
  const [saveGroupDescription, setSaveGroupDescription] =
    useState("");

  /**
   * ID of the saved group currently being edited.
   *
   * `null` means the panel is not in saved-group edit mode.
   */
  const [editingGroupId, setEditingGroupId] = useState<string | null>(
    null,
  );

  /** Draft name belonging to the saved group currently being edited. */
  const [editGroupName, setEditGroupName] = useState("");

  /** Draft description belonging to the saved group currently being edited. */
  const [editGroupDescription, setEditGroupDescription] =
    useState("");

  /** Saved group currently being edited, or undefined when edit mode is inactive. */
  const editingGroup = useMemo(
    () => savedGroups.find((group) => group.id === editingGroupId),
    [savedGroups, editingGroupId],
  );

  const isEditingGroup = editingGroup !== undefined;

  /**
   * Whether the current edit draft differs from the saved group's persisted
   * name, description, grouping property, or selected property values.
   */
  const hasEditChanges = useMemo(() => {
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
   * Whether the current saved-group edit draft can be persisted.
   *
   * Update requires a valid name, at least one selected property value, and at
   * least one difference from the currently persisted saved group.
   */
  const canUpdateGroup =
    !isDisabled &&
    isEditingGroup &&
    editGroupName.trim().length > 0 &&
    selectedValues.size > 0 &&
    hasEditChanges;

  /**
   * Available checkbox options discovered from the actual GeoJSON dataset.
   *
   * Display mappings affect labels only. Option values remain the raw values
   * stored by the GeoJSON.
   */
  const groupingOptions = useMemo(() => {
    if (!featureCollection || !selectedGroupingProperty) {
      return [];
    }

    return getGroupingOptions(
      featureCollection,
      selectedGroupingProperty,
    );
  }, [featureCollection, selectedGroupingProperty]);

  /**
   * Whether the current property selection can be saved as a new group.
   *
   * A new group can only be created when at least two property values are
   * selected and the current selection does not already represent an active
   * saved group.
   */
  const canBeginSavingGroup =
    !isDisabled &&
    selectedValues.size > 1 &&
    activeSavedGroupId === null;

  /**
   * Whether the currently entered saved-group metadata is valid.
   */
  const canSaveGroup =
    canBeginSavingGroup && saveGroupName.trim().length > 0;

  /**
   * ID of the saved group whose optional description is currently expanded.
   *
   * `null` means no saved-group description is visible.
   */
  const [openDescriptionGroupId, setOpenDescriptionGroupId] =
    useState<string | null>(null);

  /**
   * Adds or removes one grouping value and immediately previews the resulting
   * group on the map and in the quiz question set.
   *
   * Ordinary property changes become an unsaved active group. Changes made
   * during saved-group editing preserve the saved group's active identity.
   *
   * @param value - Raw GeoJSON grouping value to toggle.
   */
  function toggleGroupingValue(value: string): void {
    const updatedValues = new Set(selectedValues);

    if (updatedValues.has(value)) {
      updatedValues.delete(value);
    } else {
      updatedValues.add(value);
    }

    setSelectedValues(updatedValues);

    applySelectedValues(updatedValues);
  }

  /**
   * Applies the currently selected property values as an unsaved active quiz
   * group.
   */
  function applyPropertyGroup(): void {
    if (!selectedGroupingProperty || selectedValues.size === 0) {
      return;
    }

    onApplyGroup({
      type: "property",

      property: selectedGroupingProperty.property,

      values: Array.from(selectedValues),
    });
  }

  /**
   * Restores the complete quiz and clears any temporary property selections
   * still shown in the panel.
   */
  function handleUseFullQuiz(): void {
    setSelectedValues(new Set());

    cancelSavingGroup();

    onUseFullQuiz();
  }

  /**
   * Clears every property-group selection and immediately updates the active
   * map and quiz.
   */
  function deselectAllGroupingValues(): void {
    const emptySelection = new Set<string>();

    setSelectedValues(emptySelection);

    applySelectedValues(emptySelection);
  }

  /**
   * Toggles a saved group and keeps the Property Groups editor synchronized
   * with the group being loaded.
   *
   * Loading a property-based saved group selects its grouping property and
   * restores its saved checkbox values. Toggling the currently active saved
   * group off returns to Full Quiz and clears the checkbox selection.
   *
   * @param savedGroup - Saved group selected by the user.
   */
  function handleToggleSavedGroup(savedGroup: SavedQuizGroup): void {
    const isCurrentlyActive = activeSavedGroupId === savedGroup.id;

    /*
     * Clicking the active saved group toggles it off and returns to Full Quiz.
     */
    if (isCurrentlyActive) {
      setSelectedValues(new Set());

      cancelSavingGroup();

      onToggleSavedGroup(savedGroup);

      return;
    }

    /*
     * Property groups populate the Property Groups editor when loaded.
     */
    if (savedGroup.source.type === "property") {
      const propertySource = savedGroup.source;

      const groupingProperty = quiz.grouping?.properties.find(
        (property) => property.property === propertySource.property,
      );

      if (groupingProperty) {
        setSelectedGroupingProperty(groupingProperty);

        setSelectedValues(new Set(propertySource.values));
      }
    } else {
      /*
       * Manual groups do not correspond to property checkboxes.
       */
      setSelectedValues(new Set());
    }

    cancelSavingGroup();

    onToggleSavedGroup(savedGroup);
  }

  /**
   * Handles changing which GeoJSON property is being used to construct a
   * temporary property group.
   *
   * Existing selections are cleared because values belong to a specific
   * grouping property.
   *
   * @param propertyName - GeoJSON grouping property selected by the user.
   */
  function changeGroupingProperty(propertyName: string): void {
    const property =
      quiz.grouping?.properties.find(
        (candidate) => candidate.property === propertyName,
      ) ?? null;

    setSelectedGroupingProperty(property);

    setSelectedValues(new Set());

    cancelSavingGroup();
  }

  /**
   * Opens or closes a saved group's description.
   *
   * Only one description is displayed at a time.
   *
   * @param groupId - ID of the saved group whose description should toggle.
   */
  function toggleSavedGroupDescription(groupId: string): void {
    setOpenDescriptionGroupId((currentGroupId) =>
      currentGroupId === groupId ? null : groupId,
    );
  }

  /**
   * Opens the saved-group creation form.
   */
  function beginSavingGroup(): void {
    if (!canBeginSavingGroup) {
      return;
    }

    setIsSavingGroup(true);
  }

  /**
   * Cancels saved-group creation and clears its temporary metadata.
   */
  function cancelSavingGroup(): void {
    setIsSavingGroup(false);

    setSaveGroupName("");

    setSaveGroupDescription("");
  }

  /**
   * Toggles edit mode for a saved group or switches the current edit session to
   * another saved group.
   *
   * Clicking the pencil for the group already being edited exits edit mode and
   * restores its persisted state. Clicking another group's pencil keeps edit
   * mode active but loads that group's metadata, property selections, and map
   * preview.
   *
   * @param savedGroup - Saved group whose edit state should be toggled.
   */
  function toggleSavedGroupEditing(savedGroup: SavedQuizGroup): void {
    /*
     * Clicking the pencil belonging to the group already being edited acts as
     * an alternate Cancel control.
     */
    if (editingGroupId === savedGroup.id) {
      cancelEditingSavedGroup();

      return;
    }

    /*
     * The current Property Groups editor only supports property-based saved
     * groups. Manual groups will use their own edit workflow later.
     */
    if (savedGroup.source.type !== "property") {
      return;
    }

    const propertySource = savedGroup.source;

    const groupingProperty = quiz.grouping?.properties.find(
      (property) => property.property === propertySource.property,
    );

    if (!groupingProperty) {
      return;
    }

    /*
     * If another group was being edited, its unsaved draft is discarded simply
     * by replacing the edit state with the newly selected saved group.
     */
    cancelSavingGroup();
    setEditingGroupId(savedGroup.id);
    setEditGroupName(savedGroup.name);
    setEditGroupDescription(savedGroup.description ?? "");
    setSelectedGroupingProperty(groupingProperty);
    setSelectedValues(new Set(propertySource.values));

    /*
     * The group being edited is also the active saved group and map preview.
     */
    onApplySavedGroup(propertySource);
    onSetActiveSavedGroup(savedGroup.id);
  }

  /**
   * Applies a property selection immediately to the map and quiz.
   *
   * Changes made during saved-group editing preserve the active saved-group
   * identity. Ordinary property changes become an unsaved active group.
   *
   * An empty ordinary selection returns to Full Quiz.
   *
   * @param values - Raw GeoJSON values that should currently be active.
   */
  function applySelectedValues(values: Set<string>): void {
    if (!selectedGroupingProperty) {
      return;
    }

    /*
     * Outside Edit mode, clearing every checkbox means there is no custom
     * grouping and therefore restores Full Quiz.
     */
    if (values.size === 0 && !isEditingGroup) {
      onUseFullQuiz();

      return;
    }

    const group: ActiveQuizGroup = {
      type: "property",

      property: selectedGroupingProperty.property,

      values: Array.from(values),
    };

    if (isEditingGroup) {
      onApplySavedGroup(group);

      return;
    }

    onApplyGroup(group);
  }

  /**
   * Cancels saved-group editing and restores the group's persisted selection.
   */
  function cancelEditingSavedGroup(): void {
    if (editingGroup?.source.type === "property") {
      /*
       * Store the narrowed source in a local variable so TypeScript preserves the
       * property-group type inside callbacks below.
       */
      const propertySource = editingGroup.source;

      const groupingProperty = quiz.grouping?.properties.find(
        (property) => property.property === propertySource.property,
      );

      if (groupingProperty) {
        setSelectedGroupingProperty(groupingProperty);
      }

      setSelectedValues(new Set(editingGroup.source.values));

      onApplySavedGroup(editingGroup.source);
    }

    setEditingGroupId(null);
    setEditGroupName("");
    setEditGroupDescription("");
  }

  /**
   * Commits the current edit draft to the active saved group and reapplies its
   * updated selection to the quiz.
   */
  function updateEditingSavedGroup(): void {
    if (
      !canUpdateGroup ||
      !editingGroup ||
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

    /*
     * The persisted saved group remains the active group after its definition
     * changes.
     */
    onApplySavedGroup(updatedSource);
    onSetActiveSavedGroup(editingGroup.id);

    setEditingGroupId(null);
    setEditGroupName("");
    setEditGroupDescription("");
  }

  /**
   * Deletes the saved group currently being edited and returns to Full Quiz.
   */
  function deleteEditingSavedGroup(): void {
    if (!editingGroup) {
      return;
    }

    onDeleteGroup(editingGroup.id);

    setEditingGroupId(null);
    setEditGroupName("");
    setEditGroupDescription("");
    setSelectedValues(new Set());

    onUseFullQuiz();
  }

  /**
   * Saves the current property selection, immediately applies the persisted
   * group, and marks it as the active saved group.
   */
  function saveCurrentPropertyGroup(): void {
    if (!canSaveGroup || !selectedGroupingProperty) {
      return;
    }

    const source: QuizGroupSource = {
      type: "property",

      property: selectedGroupingProperty.property,

      values: Array.from(selectedValues),
    };

    const savedGroup = onSaveGroup(
      saveGroupName,
      saveGroupDescription.trim() || undefined,
      source,
    );

    /*
     * Apply the persisted source without treating it as an unsaved group.
     * This keeps the newly created saved group active and highlighted.
     */
    onApplySavedGroup(savedGroup.source);

    onSetActiveSavedGroup(savedGroup.id);

    cancelSavingGroup();
  }

  return (
    <div className="max-h-[calc(100vh-9.5rem)] w-80 overflow-hidden rounded-xl bg-white/95 shadow-lg backdrop-blur-md">
      {/* Scrollable panel content */}
      <div className="panel-scrollbar max-h-[calc(100vh-9.5rem)] overflow-y-auto overscroll-contain p-4">
        {/* Panel heading */}
        <div className="mb-4">
          <h2 className="text-base font-bold text-gray-900">
            Groups
          </h2>

          <p className="mt-1 text-xs leading-relaxed text-gray-600">
            Practice part of a quiz at a time by limiting the map and
            question set to a smaller group.
          </p>
        </div>

        {/* Full Quiz */}
        <section className="border-b border-gray-300 pb-4">
          <h3 className="mb-2 text-sm font-semibold text-gray-800">
            Full Quiz
          </h3>

          <button
            type="button"
            disabled={isDisabled || activeGroup.type === "full"}
            onClick={handleUseFullQuiz}
            className={[
              "w-full rounded-lg border px-3 py-2 text-sm font-semibold transition",

              activeGroup.type === "full"
                ? "border-gray-900 bg-gray-900 text-white"
                : "border-gray-300 bg-white text-gray-800 hover:bg-gray-100",

              isDisabled ? "cursor-not-allowed opacity-50" : "",
            ].join(" ")}
          >
            Use Full Quiz
          </button>
        </section>

        {/* Saved Groups */}
        <section className="border-b border-gray-300 py-4">
          <h3 className="mb-2 text-sm font-semibold text-gray-800">
            Saved Groups
          </h3>

          {savedGroups.length === 0 ? (
            /* Empty saved-groups state */
            <p className="text-xs text-gray-500">
              Saved groups will appear here.
            </p>
          ) : (
            /* Saved group list */
            <div className="space-y-2">
              {savedGroups.map((savedGroup) => {
                const isActive = activeSavedGroupId === savedGroup.id;

                const isDescriptionOpen =
                  openDescriptionGroupId === savedGroup.id;

                const isBeingEdited =
                  editingGroupId === savedGroup.id;

                return (
                  <div
                    key={savedGroup.id}
                    className={[
                      "overflow-hidden rounded-lg border transition",

                      isActive
                        ? "border-gray-900 bg-gray-900 text-white"
                        : "border-gray-300 bg-white text-gray-800",
                    ].join(" ")}
                  >
                    {/* Saved group controls */}
                    <div className="flex items-center">
                      {/* Saved group toggle */}
                      <button
                        type="button"
                        disabled={isDisabled}
                        onClick={() =>
                          handleToggleSavedGroup(savedGroup)
                        }
                        className={[
                          "flex min-w-0 flex-1 items-center px-3 py-2 text-left transition",

                          !isActive ? "hover:bg-gray-100" : "",

                          isDisabled
                            ? "cursor-not-allowed opacity-50"
                            : "",
                        ].join(" ")}
                      >
                        <span className="truncate text-sm font-semibold">
                          {savedGroup.name}
                        </span>
                      </button>

                      {/* Saved group secondary controls */}
                      <div className="flex shrink-0 items-center gap-1 pr-2">
                        {/* Description toggle */}
                        {savedGroup.description && (
                          <button
                            type="button"
                            disabled={isDisabled}
                            onClick={() =>
                              toggleSavedGroupDescription(
                                savedGroup.id,
                              )
                            }
                            title="Show group description"
                            aria-label={`Show description for ${savedGroup.name}`}
                            aria-expanded={
                              openDescriptionGroupId === savedGroup.id
                            }
                            className={[
                              "flex h-6 w-6 items-center justify-center rounded-md text-xs font-bold transition",

                              isDescriptionOpen
                                ? isActive
                                  ? "bg-white/25 text-white"
                                  : "bg-gray-300 text-gray-900"
                                : isActive
                                  ? "text-white/80 hover:bg-white/20 hover:text-white"
                                  : "text-gray-500 hover:bg-gray-300 hover:text-gray-900",
                            ].join(" ")}
                          >
                            ?
                          </button>
                        )}
                        <button
                          type="button"
                          disabled={isDisabled}
                          onClick={() =>
                            toggleSavedGroupEditing(savedGroup)
                          }
                          title="Edit saved group"
                          aria-label={`Edit ${savedGroup.name}`}
                          className={[
                            "flex h-6 w-6 items-center justify-center rounded-md transition",

                            isBeingEdited
                              ? isActive
                                ? "bg-white/25 text-white"
                                : "bg-gray-300 text-gray-900"
                              : isActive
                                ? "text-white/80 hover:bg-white/20 hover:text-white"
                                : "text-gray-500 hover:bg-gray-300 hover:text-gray-900",
                          ].join(" ")}
                        >
                          {/* Pencil icon */}
                          <svg
                            viewBox="0 0 24 24"
                            fill="none"
                            stroke="currentColor"
                            strokeWidth="2"
                            className="h-3.5 w-3.5"
                            aria-hidden="true"
                          >
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              d="M16.862 3.487a2.1 2.1 0 0 1 2.97 2.97L8.25 18.04 4 19l.96-4.25L16.862 3.487Z"
                            />
                          </svg>
                        </button>
                      </div>
                    </div>

                    {/* Saved group description */}
                    {savedGroup.description &&
                      openDescriptionGroupId === savedGroup.id && (
                        <div
                          className={[
                            "border-t px-3 py-2 text-xs leading-relaxed",

                            isActive
                              ? "border-white/20 text-white/80"
                              : "border-gray-300 text-gray-600",
                          ].join(" ")}
                        >
                          {savedGroup.description}
                        </div>
                      )}
                  </div>
                );
              })}
            </div>
          )}
        </section>

        {/* Saved-group editing metadata */}
        {isEditingGroup && (
          <div className="mb-4 rounded-lg border border-gray-300 bg-white p-3">
            {/* Editable group name */}
            <label className="block">
              <span className="text-xs font-medium text-gray-600">
                Name
              </span>

              <input
                type="text"
                value={editGroupName}
                onChange={(event) =>
                  setEditGroupName(event.target.value)
                }
                className="mt-1 w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 outline-none"
              />
            </label>

            {/* Editable group description */}
            <label className="mt-3 block">
              <span className="text-xs font-medium text-gray-600">
                Description
                <span className="ml-1 font-normal text-gray-400">
                  Optional
                </span>
              </span>

              <textarea
                value={editGroupDescription}
                onChange={(event) =>
                  setEditGroupDescription(event.target.value)
                }
                rows={3}
                className="mt-1 w-full resize-none rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 outline-none"
              />
            </label>
          </div>
        )}

        {/* Property Groups */}
        {quiz.grouping?.properties.length ? (
          <section className="border-b border-gray-300 py-4">
            <h3 className="mb-2 text-sm font-semibold text-gray-800">
              Property Groups
            </h3>

            {/* Grouping property selector */}
            {quiz.grouping.properties.length > 1 && (
              <select
                value={selectedGroupingProperty?.property ?? ""}
                disabled={isDisabled}
                onChange={(event) =>
                  changeGroupingProperty(event.target.value)
                }
                className="mb-3 w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-gray-800"
              >
                {quiz.grouping.properties.map((property) => (
                  <option
                    key={property.property}
                    value={property.property}
                  >
                    {property.label}
                  </option>
                ))}
              </select>
            )}

            {/* Selected grouping dimension */}
            <div className="mb-2 flex items-center justify-between">
              <div className="text-xs font-medium text-gray-500">
                {selectedGroupingProperty
                  ? `Group by ${selectedGroupingProperty.label}`
                  : "Select a group"}
              </div>

              {/* Selected / total count */}
              <p className="text-xs font-medium text-gray-500">
                {selectedValues.size} / {groupingOptions.length}
              </p>

              {/* Deselect all selections button */}
              <button
                type="button"
                disabled={isDisabled || selectedValues.size === 0}
                onClick={deselectAllGroupingValues}
                className={[
                  "text-xs font-medium underline transition",

                  isDisabled || selectedValues.size === 0
                    ? "text-gray-400"
                    : "text-gray-600 hover:text-gray-900",
                ].join(" ")}
              >
                Deselect All
              </button>
            </div>

            {/* Available property values */}
            <div className="max-h-64 space-y-2 overflow-y-auto pr-1">
              {groupingOptions.map(({ value, label }) => {
                const isSelected = selectedValues.has(value);

                return (
                  <label
                    key={value}
                    className="flex cursor-pointer items-center gap-2 text-sm text-gray-700"
                  >
                    {/* Grouping value checkbox */}
                    <input
                      type="checkbox"
                      checked={isSelected}
                      disabled={isDisabled}
                      onChange={() => toggleGroupingValue(value)}
                      className="h-4 w-4"
                    />

                    {/* Grouping value label */}
                    <span>{label}</span>
                  </label>
                );
              })}
            </div>

            {/* Property-group actions */}
            <div className="mt-4 space-y-2">
              {isEditingGroup ? (
                <>
                  {/* Update / Delete saved group */}
                  <div className="flex gap-2">
                    {/* Update saved group */}
                    <button
                      type="button"
                      disabled={!canUpdateGroup}
                      onClick={updateEditingSavedGroup}
                      className={[
                        "flex-1 rounded-lg px-3 py-2 text-sm font-semibold transition",

                        canUpdateGroup
                          ? "bg-gray-900 text-white hover:bg-gray-700"
                          : "bg-gray-300 text-gray-500",
                      ].join(" ")}
                    >
                      Update
                    </button>

                    {/* Delete saved group */}
                    <button
                      type="button"
                      disabled={isDisabled}
                      onClick={deleteEditingSavedGroup}
                      title="Delete saved group"
                      aria-label="Delete saved group"
                      className={[
                        "flex h-9 w-9 shrink-0 items-center justify-center rounded-lg transition",

                        isDisabled
                          ? "bg-gray-300 text-gray-500"
                          : "bg-red-600 text-white hover:bg-red-700",
                      ].join(" ")}
                    >
                      {/* Trash icon */}
                      <svg
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="2"
                        className="h-4 w-4"
                        aria-hidden="true"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          d="M3 6h18"
                        />

                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          d="M8 6V4h8v2"
                        />

                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          d="M19 6l-1 14H6L5 6"
                        />
                      </svg>
                    </button>
                  </div>

                  {/* Cancel saved-group editing */}
                  <div className="flex justify-end">
                    <button
                      type="button"
                      onClick={cancelEditingSavedGroup}
                      className="text-xs font-medium text-gray-600 underline transition hover:text-gray-900"
                    >
                      Cancel
                    </button>
                  </div>
                </>
              ) : (
                <>
                  {/* Save property group */}
                  <button
                    type="button"
                    disabled={
                      isSavingGroup
                        ? !canSaveGroup
                        : !canBeginSavingGroup
                    }
                    onClick={
                      isSavingGroup
                        ? saveCurrentPropertyGroup
                        : beginSavingGroup
                    }
                    className={[
                      "w-full rounded-lg px-3 py-2 text-sm font-semibold transition",

                      (
                        isSavingGroup
                          ? canSaveGroup
                          : canBeginSavingGroup
                      )
                        ? "bg-gray-900 text-white hover:bg-gray-700"
                        : "bg-gray-300 text-gray-500",
                    ].join(" ")}
                  >
                    {isSavingGroup ? "Save" : "Save Group"}
                  </button>

                  {/* Saved-group creation fields */}
                  {isSavingGroup && (
                    <div className="rounded-lg border border-gray-300 bg-white p-3">
                      {/* Group name */}
                      <label className="block">
                        <span className="text-xs font-medium text-gray-600">
                          Name
                        </span>

                        <input
                          type="text"
                          value={saveGroupName}
                          onChange={(event) =>
                            setSaveGroupName(event.target.value)
                          }
                          placeholder="Group name"
                          className="mt-1 w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 outline-none"
                        />
                      </label>

                      {/* Optional group description */}
                      <label className="mt-3 block">
                        <span className="text-xs font-medium text-gray-600">
                          Description
                          <span className="ml-1 font-normal text-gray-400">
                            Optional
                          </span>
                        </span>

                        <textarea
                          value={saveGroupDescription}
                          onChange={(event) =>
                            setSaveGroupDescription(
                              event.target.value,
                            )
                          }
                          placeholder="Describe this group"
                          rows={3}
                          className="mt-1 w-full resize-none rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 outline-none"
                        />
                      </label>

                      {/* Cancel saved-group creation */}
                      <div className="mt-2 flex justify-end">
                        <button
                          type="button"
                          onClick={cancelSavingGroup}
                          className="text-xs font-medium text-gray-600 underline transition hover:text-gray-900"
                        >
                          Cancel
                        </button>
                      </div>
                    </div>
                  )}
                </>
              )}
            </div>
          </section>
        ) : null}

        {/* Manual feature selection */}
        <section className="pt-4">
          <h3 className="text-sm font-semibold text-gray-800">
            Manual Selection
          </h3>

          <p className="mt-1 text-xs leading-relaxed text-gray-500">
            Create a custom group by selecting individual geographic
            features on the map.
          </p>

          <button
            type="button"
            disabled
            className="mt-3 w-full cursor-not-allowed rounded-lg bg-gray-300 px-3 py-2 text-sm font-semibold text-gray-500"
          >
            Select Features
          </button>
        </section>
      </div>
    </div>
  );
}
