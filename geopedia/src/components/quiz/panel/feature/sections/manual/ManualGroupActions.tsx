/**
 * Adapts the manual feature-selection workflow to GeoPedia's shared saved-group
 * persistence controls.
 *
 * Manual selection adds one domain-specific action beyond the shared group
 * workflow: cancelling the complete manual-selection session when the new-group
 * metadata form is not open.
 */

"use client";

import QuizGroupActions from "../../shared/QuizGroupActions";

/**
 * Props required by the manual-group action controls.
 */
type ManualGroupActionsProps = {
  /** Whether the current feature selection can become a saved group. */
  canSave: boolean;

  /** Whether the current saved-group edit contains valid changes. */
  canUpdate: boolean;

  /** Whether the new saved-group metadata form is currently open. */
  isSavingGroup: boolean;

  /** Whether an existing manual saved group is currently being edited. */
  isEditingGroup: boolean;

  /** Current new manual-group name draft. */
  groupName: string;

  /** Current new manual-group description draft. */
  groupDescription: string;

  /** Whether the new manual-group metadata and selection are valid. */
  canConfirmSave: boolean;

  /** Opens the new manual saved-group metadata form. */
  onBeginSaving: () => void;

  /** Persists the current manual selection as a new saved group. */
  onSave: () => void;

  /** Persists changes to the manual saved group currently being edited. */
  onUpdate: () => void;

  /** Deletes the manual saved group currently being edited. */
  onDelete: () => void;

  /** Cancels saved manual-group editing. */
  onCancelEditing: () => void;

  /** Cancels the new manual saved-group metadata form. */
  onCancelSaving: () => void;

  /** Cancels the complete new manual-selection workflow. */
  onCancelSelection: () => void;

  /** Updates the new manual-group name draft. */
  onGroupNameChange: (name: string) => void;

  /** Updates the new manual-group description draft. */
  onGroupDescriptionChange: (description: string) => void;
};

/**
 * Displays shared saved-group actions configured for manual feature selection.
 *
 * @param props - Manual-group save/edit state and callbacks.
 * @returns Manual-group persistence controls.
 */
export default function ManualGroupActions({
  canSave,
  canUpdate,

  isSavingGroup,
  isEditingGroup,

  groupName,
  groupDescription,

  canConfirmSave,

  onBeginSaving,
  onSave,
  onUpdate,
  onDelete,

  onCancelEditing,
  onCancelSaving,
  onCancelSelection,

  onGroupNameChange,
  onGroupDescriptionChange,
}: ManualGroupActionsProps) {
  return (
    <div className="mt-3">
      <QuizGroupActions
        isEditingGroup={isEditingGroup}
        canUpdateGroup={canUpdate}
        canBeginSavingGroup={canSave}
        canConfirmSaveGroup={canConfirmSave}
        isSavingGroup={isSavingGroup}
        groupName={groupName}
        groupDescription={groupDescription}
        onBeginSaving={onBeginSaving}
        onSave={onSave}
        onCancelSaving={onCancelSaving}
        onUpdate={onUpdate}
        onDelete={onDelete}
        onCancelEditing={onCancelEditing}
        onGroupNameChange={onGroupNameChange}
        onGroupDescriptionChange={onGroupDescriptionChange}
        onCancelWorkflow={onCancelSelection}
      />
    </div>
  );
}
