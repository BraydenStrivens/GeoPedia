/**
 * Coordinates GeoPedia's quiz-group selection interface.
 *
 * The panel connects:
 *
 * - Full Quiz.
 * - Saved groups.
 * - Property-based group creation and editing.
 * - Manual feature-selection group creation and editing.
 *
 * Property-specific and manual-specific editor state is delegated to focused
 * hooks. This component retains only state and transitions shared between
 * multiple grouping workflows.
 */

"use client";

import { useMemo, useRef, useState } from "react";

import { useManualGroupEditor } from "@/quiz/groupings/feature/hooks/useManualGroupEditor";
import { usePropertyGroupEditor } from "@/quiz/groupings/feature/hooks/usePropertyGroupEditor";
import type { QuizGroupingFeatureCollection } from "@/quiz/groupings/feature/hooks/useQuizGroupingData";
import type {
  ActiveQuizGroup,
  QuizGroupSource,
  SavedQuizGroup,
} from "@/quiz/groupings/feature/types";
import type { FeatureQuiz } from "@/types/quiz";

import ManualSelectionSection from "./manual/ManualSelectionSection";
import FullQuizSection from "./sections/FullQuizSection";
import PropertyGroupsSection from "./sections/property/PropertyGroupsSection";
import SavedGroupsSection from "./sections/SavedGroupsSection";
import GroupMetadataFields from "./shared/GroupMetadataFields";

/**
 * Props required by the quiz Groups panel.
 */
type FeatureQuizGroupsPanelProps = {
  /** Complete feature-quiz definition containing optional grouping configuration. */
  quiz: FeatureQuiz;

  /** GeoJSON property containing each feature's stable map ID. */
  promoteId?: string;

  /** Loaded GeoJSON used by property and manual grouping workflows. */
  featureCollection: QuizGroupingFeatureCollection | null;

  /** Group currently applied to the quiz. */
  activeGroup: ActiveQuizGroup;

  /** Groups previously saved for this quiz. */
  savedGroups: SavedQuizGroup[];

  /** ID of the saved group currently applied to the quiz. */
  activeSavedGroupId: string | null;

  /** Whether manual map-selection mode is active. */
  isManualSelecting: boolean;

  /** Feature IDs currently selected by manual grouping. */
  manualSelectedFeatureIds: ReadonlySet<string>;

  /** Whether answer labels are visible during manual selection. */
  showManualSelectionAnswers: boolean;

  /** Whether GeoGuessr-only filtering is currently enabled. */
  isGeoGuessrOnly: boolean;

  /** Applies an unsaved group to the quiz. */
  onApplyGroup: (group: ActiveQuizGroup) => void;

  /** Applies a saved group without clearing its saved-group identity. */
  onApplySavedGroup: (group: ActiveQuizGroup) => void;

  /** Begins a new manual feature-selection workflow. */
  onBeginManualSelection: () => void;

  /** Begins editing a saved manual group using its existing feature IDs. */
  onBeginEditingManualGroup: (featureIds: Iterable<string>) => void;

  /** Removes one manually selected feature. */
  onRemoveManualFeature: (featureId: string) => void;

  /** Clears every manually selected feature. */
  onClearManualSelection: () => void;

  /** Selects every supplied manual feature. */
  onSelectAllManualFeatures: (featureIds: Iterable<string>) => void;

  /** Cancels manual selection and clears its temporary state. */
  onCancelManualSelection: () => void;

  /** Toggles answer labels during manual feature selection. */
  onToggleManualSelectionAnswers: () => void;

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

  /** Permanently removes a saved group. */
  onDeleteGroup: (groupId: string) => void;

  /** Marks a saved group as active. */
  onSetActiveSavedGroup: (groupId: string | null) => void;

  /** Restores the complete unfiltered quiz. */
  onUseFullQuiz: () => void;

  /** Enables or disables GeoGuessr-only filtering. */
  onGeoGuessrOnlyChange: (isEnabled: boolean) => void;

  /** Loads or unloads a saved group. */
  onToggleSavedGroup: (group: SavedQuizGroup) => void;

  /** Whether grouping interactions are currently disabled. */
  isDisabled: boolean;
};

/**
 * Displays the Groups sidebar and coordinates transitions between grouping
 * workflows.
 *
 * @param props - Quiz data, current group state, manual-selection state, and
 * persistence callbacks.
 * @returns The complete Groups panel.
 */
export default function FeatureQuizGroupsPanel({
  quiz,
  promoteId,
  featureCollection,

  activeGroup,
  activeSavedGroupId,
  savedGroups,

  isManualSelecting,
  manualSelectedFeatureIds,
  showManualSelectionAnswers,
  isGeoGuessrOnly,

  onApplyGroup,
  onApplySavedGroup,
  onBeginManualSelection,
  onBeginEditingManualGroup,
  onRemoveManualFeature,
  onClearManualSelection,
  onSelectAllManualFeatures,
  onCancelManualSelection,
  onToggleManualSelectionAnswers,

  onSaveGroup,
  onUpdateGroup,
  onDeleteGroup,
  onSetActiveSavedGroup,
  onUseFullQuiz,
  onGeoGuessrOnlyChange,
  onToggleSavedGroup,

  isDisabled,
}: FeatureQuizGroupsPanelProps) {
  /**
   * Scrollable Groups panel element.
   *
   * Used to keep newly revealed forms and editing controls visible without
   * requiring the user to manually scroll after expanding the panel.
   */
  const panelScrollRef = useRef<HTMLDivElement>(null);

  /**
   * Smoothly scrolls the Groups panel to its newly expanded bottom content.
   *
   * requestAnimationFrame waits until React has committed the state change that
   * revealed the additional UI before measuring the panel's new scroll height.
   */
  function scrollPanelToBottom(): void {
    requestAnimationFrame(() => {
      const panel = panelScrollRef.current;

      if (!panel) {
        return;
      }

      panel.scrollTo({
        top: panel.scrollHeight,
        behavior: "smooth",
      });
    });
  }

  /** ID of the saved group currently being edited. */
  const [editingGroupId, setEditingGroupId] = useState<string | null>(
    null,
  );

  /** Name draft belonging to the saved group currently being edited. */
  const [editGroupName, setEditGroupName] = useState("");

  /** Description draft belonging to the saved group currently being edited. */
  const [editGroupDescription, setEditGroupDescription] =
    useState("");

  /** ID of the saved group whose optional description is expanded. */
  const [expandedDescriptionGroupId, setExpandedDescriptionGroupId] =
    useState<string | null>(null);

  /** Saved group currently being edited. */
  const editingGroup = useMemo(
    () => savedGroups.find((group) => group.id === editingGroupId),
    [savedGroups, editingGroupId],
  );

  /** Whether the current edit target is property-based. */
  const isEditingPropertyGroup =
    editingGroup?.source.type === "property";

  /** Whether the current edit target is manually feature-selected. */
  const isEditingManualGroup =
    editingGroup?.source.type === "features";

  /**
   * Whether the loaded map data provides GeoGuessr eligibility information.
   *
   * The GeoGuessr Only control is hidden completely for quizzes whose geographic
   * data does not define the `geoguessr` property.
   */
  const supportsGeoGuessrFilter = useMemo(() => {
    return (
      featureCollection?.features.some(
        (feature) =>
          typeof feature.properties?.geoguessr === "boolean",
      ) ?? false
    );
  }, [featureCollection]);

  /**
   * Property-group creation, selection, validation, and updating.
   */
  const propertyEditor = usePropertyGroupEditor({
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
  });

  /**
   * Manual-group derived data, validation, creation, and updating.
   */
  const manualEditor = useManualGroupEditor({
    quiz,
    promoteId,
    featureCollection,

    selectedFeatureIds: manualSelectedFeatureIds,

    editingGroup,
    editGroupName,
    editGroupDescription,
    isDisabled,

    onSaveGroup,
    onUpdateGroup,
    onApplySavedGroup,
    onSetActiveSavedGroup,
    onCancelManualSelection,
  });

  /**
   * Clears the metadata belonging to the current saved-group edit session.
   */
  function clearSavedGroupEditState(): void {
    setEditingGroupId(null);
    setEditGroupName("");
    setEditGroupDescription("");
  }

  /**
   * Restores Full Quiz and clears temporary property-group UI state.
   */
  function handleUseFullQuiz(): void {
    propertyEditor.clearPropertySelection();
    propertyEditor.cancelSavingPropertyGroup();

    onUseFullQuiz();
  }

  /**
   * Opens the property-group metadata form and keeps the newly revealed fields
   * visible.
   */
  function beginSavingPropertyGroup(): void {
    propertyEditor.beginSavingPropertyGroup();

    scrollPanelToBottom();
  }

  /**
   * Begins manual feature selection and keeps its expanded controls visible.
   */
  function beginManualSelection(): void {
    onBeginManualSelection();

    scrollPanelToBottom();
  }

  /**
   * Opens the manual-group metadata form and keeps the newly revealed fields
   * visible.
   */
  function beginSavingManualGroup(): void {
    manualEditor.beginSavingManualGroup();

    scrollPanelToBottom();
  }

  /**
   * Loads or unloads a saved group and synchronizes the appropriate editor.
   *
   * @param savedGroup - Saved group selected by the user.
   */
  function handleToggleSavedGroup(savedGroup: SavedQuizGroup): void {
    const isCurrentlyActive = activeSavedGroupId === savedGroup.id;

    if (isCurrentlyActive) {
      propertyEditor.clearPropertySelection();
      propertyEditor.cancelSavingPropertyGroup();

      onToggleSavedGroup(savedGroup);

      return;
    }

    /*
     * A saved group is replacing the current grouping workflow. Any temporary
     * manual selection must be discarded before the saved group becomes active.
     */
    if (isManualSelecting) {
      cancelManualSelection();
    }

    if (savedGroup.source.type === "property") {
      propertyEditor.loadPropertyGroup(savedGroup.source);
    } else {
      propertyEditor.clearPropertySelection();
    }

    propertyEditor.cancelSavingPropertyGroup();

    onToggleSavedGroup(savedGroup);
  }

  /**
   * Opens or closes a saved group's description.
   *
   * @param groupId - ID of the saved group whose description should toggle.
   */
  function toggleSavedGroupDescription(groupId: string): void {
    setExpandedDescriptionGroupId((currentGroupId) =>
      currentGroupId === groupId ? null : groupId,
    );
  }

  /**
   * Toggles edit mode for a saved group or switches editing to another group.
   *
   * Property groups load their saved property values into the Property Groups
   * editor. Manual groups enter feature-selection mode with their persisted
   * feature IDs preselected.
   *
   * @param savedGroup - Saved group whose editing state should toggle.
   */
  function toggleSavedGroupEditing(savedGroup: SavedQuizGroup): void {
    if (editingGroupId === savedGroup.id) {
      cancelEditingSavedGroup();

      return;
    }

    /*
     * Validate property groups before changing shared edit state so a missing
     * grouping configuration cannot leave the panel partially in edit mode.
     */
    if (savedGroup.source.type === "property") {
      const loaded = propertyEditor.loadPropertyGroup(
        savedGroup.source,
      );

      if (!loaded) {
        return;
      }
    }

    /*
     * Property editing replaces any temporary manual-selection workflow.
     */
    if (isManualSelecting) {
      cancelManualSelection();
    }

    propertyEditor.cancelSavingPropertyGroup();
    manualEditor.cancelSavingManualGroup();

    setEditingGroupId(savedGroup.id);
    setEditGroupName(savedGroup.name);
    setEditGroupDescription(savedGroup.description ?? "");

    if (savedGroup.source.type === "property") {
      onApplySavedGroup(savedGroup.source);
      onSetActiveSavedGroup(savedGroup.id);

      scrollPanelToBottom();

      return;
    }

    /*
     * Manual editing requires Full Quiz visibility so features outside the
     * persisted group remain available for selection.
     */
    propertyEditor.clearPropertySelection();

    onBeginEditingManualGroup(savedGroup.source.featureIds);
    onSetActiveSavedGroup(savedGroup.id);

    scrollPanelToBottom();
  }

  /**
   * Cancels saved-group editing and restores the group's persisted state.
   */
  function cancelEditingSavedGroup(): void {
    if (!editingGroup) {
      clearSavedGroupEditState();

      return;
    }

    if (editingGroup.source.type === "property") {
      const restored = propertyEditor.loadPropertyGroup(
        editingGroup.source,
      );

      if (restored) {
        onApplySavedGroup(editingGroup.source);
        onSetActiveSavedGroup(editingGroup.id);
      }

      clearSavedGroupEditState();

      return;
    }

    /*
     * Discard the temporary manual-selection draft and restore the persisted
     * manual saved group.
     */
    onCancelManualSelection();
    onApplySavedGroup(editingGroup.source);
    onSetActiveSavedGroup(editingGroup.id);

    clearSavedGroupEditState();
  }

  /**
   * Persists the current saved property-group edit and exits edit mode.
   */
  function updateEditingPropertyGroup(): void {
    if (!propertyEditor.canUpdatePropertyGroup) {
      return;
    }

    propertyEditor.updateEditingPropertyGroup();

    clearSavedGroupEditState();
  }

  /**
   * Persists the current saved manual-group edit and exits edit mode.
   */
  function updateEditingManualGroup(): void {
    if (!manualEditor.canUpdateManualGroup) {
      return;
    }

    manualEditor.updateEditingManualGroup();

    clearSavedGroupEditState();
  }

  /**
   * Deletes the saved group currently being edited and restores Full Quiz.
   */
  function deleteEditingSavedGroup(): void {
    if (!editingGroup) {
      return;
    }

    onDeleteGroup(editingGroup.id);

    /*
     * Only manual edit sessions own temporary map-selection state.
     */
    if (editingGroup.source.type === "features") {
      onCancelManualSelection();
    }

    propertyEditor.clearPropertySelection();

    clearSavedGroupEditState();

    onUseFullQuiz();
  }

  /**
   * Selects every feature available to manual grouping and keeps the expanded
   * manual-selection content visible in the Groups panel.
   */
  function selectAllManualFeatures(): void {
    onSelectAllManualFeatures(manualEditor.allFeatureIds);

    scrollPanelToBottom();
  }

  /**
   * Cancels the complete new manual-selection workflow.
   */
  function cancelManualSelection(): void {
    manualEditor.cancelSavingManualGroup();

    onCancelManualSelection();
  }

  return (
    <div className="max-h-[calc(100vh-9.5rem)] w-80 overflow-hidden rounded-xl bg-white/95 shadow-lg backdrop-blur-md">
      {/* Scrollable Groups panel content */}
      <div
        ref={panelScrollRef}
        className="panel-scrollbar max-h-[calc(100vh-9.5rem)] overflow-y-auto overscroll-contain px-5 py-4"
      >
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
        <FullQuizSection
          isActive={activeGroup.type === "full"}
          isDisabled={isDisabled}
          isGeoGuessrOnly={isGeoGuessrOnly}
          supportsGeoGuessrFilter={supportsGeoGuessrFilter}
          onUseFullQuiz={handleUseFullQuiz}
          onGeoGuessrOnlyChange={onGeoGuessrOnlyChange}
        />

        {/* Saved Groups */}
        <SavedGroupsSection
          savedGroups={savedGroups}
          activeSavedGroupId={activeSavedGroupId}
          editingGroupId={editingGroupId}
          openDescriptionGroupId={expandedDescriptionGroupId}
          isDisabled={isDisabled}
          onToggleGroup={handleToggleSavedGroup}
          onToggleDescription={toggleSavedGroupDescription}
          onToggleEditing={toggleSavedGroupEditing}
        />

        {/* Shared saved-group edit metadata */}
        {editingGroup && (
          <div className="my-4 rounded-lg border border-gray-300 bg-white p-3">
            <GroupMetadataFields
              name={editGroupName}
              description={editGroupDescription}
              onNameChange={setEditGroupName}
              onDescriptionChange={setEditGroupDescription}
            />
          </div>
        )}

        {/* Property Groups */}
        {quiz.grouping?.properties.length ? (
          <PropertyGroupsSection
            groupingProperties={quiz.grouping.properties}
            selectedGroupingProperty={
              propertyEditor.selectedGroupingProperty
            }
            selectedValues={propertyEditor.selectedValues}
            groupingOptions={propertyEditor.groupingOptions}
            isDisabled={isDisabled || isManualSelecting}
            isEditingGroup={isEditingPropertyGroup}
            canUpdateGroup={propertyEditor.canUpdatePropertyGroup}
            canBeginSavingGroup={
              propertyEditor.canBeginSavingPropertyGroup
            }
            canSaveGroup={propertyEditor.canSavePropertyGroup}
            isSavingGroup={propertyEditor.isSavingPropertyGroup}
            saveGroupName={propertyEditor.newPropertyGroupName}
            saveGroupDescription={
              propertyEditor.newPropertyGroupDescription
            }
            onChangeGroupingProperty={
              propertyEditor.changeGroupingProperty
            }
            onToggleGroupingValue={propertyEditor.togglePropertyValue}
            onDeselectAll={propertyEditor.clearPropertySelection}
            onBeginSaving={beginSavingPropertyGroup}
            onSave={propertyEditor.saveCurrentPropertyGroup}
            onCancelSaving={propertyEditor.cancelSavingPropertyGroup}
            onUpdate={updateEditingPropertyGroup}
            onDelete={deleteEditingSavedGroup}
            onCancelEditing={cancelEditingSavedGroup}
            onSaveGroupNameChange={
              propertyEditor.setNewPropertyGroupName
            }
            onSaveGroupDescriptionChange={
              propertyEditor.setNewPropertyGroupDescription
            }
            onRequestPanelScroll={scrollPanelToBottom}
          />
        ) : null}

        {/* Manual feature selection */}
        <ManualSelectionSection
          isSelecting={isManualSelecting}
          selectionItems={manualEditor.selectionItems}
          selectedAnswerCount={manualEditor.selectionAnswerCount}
          showAnswers={showManualSelectionAnswers}
          canSave={manualEditor.canSaveManualGroup}
          isSavingGroup={manualEditor.isSavingManualGroup}
          isEditingGroup={isEditingManualGroup}
          canUpdate={manualEditor.canUpdateManualGroup}
          groupName={manualEditor.newManualGroupName}
          groupDescription={manualEditor.newManualGroupDescription}
          canConfirmSave={manualEditor.canConfirmManualSave}
          onBeginSelection={beginManualSelection}
          onRemoveFeature={onRemoveManualFeature}
          onDeselectAll={onClearManualSelection}
          canSelectAll={
            manualSelectedFeatureIds.size <
            manualEditor.allFeatureIds.length
          }
          onSelectAll={selectAllManualFeatures}
          onToggleShowAnswers={onToggleManualSelectionAnswers}
          onBeginSaving={beginSavingManualGroup}
          onSave={manualEditor.saveCurrentManualGroup}
          onCancelSaving={manualEditor.cancelSavingManualGroup}
          onCancelEditing={cancelEditingSavedGroup}
          onGroupNameChange={manualEditor.setNewManualGroupName}
          onGroupDescriptionChange={
            manualEditor.setNewManualGroupDescription
          }
          onCancel={cancelManualSelection}
          onUpdate={updateEditingManualGroup}
          onDelete={deleteEditingSavedGroup}
          onRequestPanelScroll={scrollPanelToBottom}
        />
      </div>
    </div>
  );
}
