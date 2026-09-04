/**
 * Adapts the property-based feature grouping workflow to GeoPedia's shared
 * saved-group persistence controls.
 *
 * Property-group interactions may be blocked while manual feature selection is
 * active so that the two grouping workflows cannot modify quiz state
 * simultaneously.
 */

"use client";

import QuizGroupActions from "../../shared/QuizGroupActions";

/**
 * Props required by the property-group action controls.
 */
type PropertyGroupActionsProps = {
  /** Whether an existing saved property group is currently being edited. */
  isEditingGroup: boolean;

  /** Whether the current saved-group edit can be persisted. */
  canUpdateGroup: boolean;

  /** Whether creation of a new saved property group may begin. */
  canBeginSavingGroup: boolean;

  /** Whether the completed new saved-group draft can be persisted. */
  canSaveGroup: boolean;

  /** Whether the new saved-group metadata form is currently open. */
  isSavingGroup: boolean;

  /** Name draft for a new saved property group. */
  saveGroupName: string;

  /** Description draft for a new saved property group. */
  saveGroupDescription: string;

  /**
   * Whether property-group mutations are temporarily blocked because another
   * grouping workflow currently owns interaction.
   */
  isInteractionBlocked: boolean;

  /** Opens the new saved-group metadata form. */
  onBeginSaving: () => void;

  /** Persists the current new saved property group. */
  onSave: () => void;

  /** Cancels creation of a new saved property group. */
  onCancelSaving: () => void;

  /** Persists changes to the saved property group currently being edited. */
  onUpdate: () => void;

  /** Deletes the saved property group currently being edited. */
  onDelete: () => void;

  /** Cancels editing of the current saved property group. */
  onCancelEditing: () => void;

  /** Updates the new saved-group name draft. */
  onSaveGroupNameChange: (name: string) => void;

  /** Updates the new saved-group description draft. */
  onSaveGroupDescriptionChange: (description: string) => void;
};

/**
 * Displays shared saved-group actions configured for property-based grouping.
 *
 * @param props - Property-group save/edit state and callbacks.
 * @returns Property-group persistence controls.
 */
export default function PropertyGroupActions({
  isEditingGroup,

  canUpdateGroup,
  canBeginSavingGroup,
  canSaveGroup,

  isSavingGroup,

  saveGroupName,
  saveGroupDescription,

  isInteractionBlocked,

  onBeginSaving,
  onSave,
  onCancelSaving,

  onUpdate,
  onDelete,
  onCancelEditing,

  onSaveGroupNameChange,
  onSaveGroupDescriptionChange,
}: PropertyGroupActionsProps) {
  return (
    <div className="mt-4">
      <QuizGroupActions
        isEditingGroup={isEditingGroup}
        canUpdateGroup={canUpdateGroup}
        canBeginSavingGroup={canBeginSavingGroup}
        canConfirmSaveGroup={canSaveGroup}
        isSavingGroup={isSavingGroup}
        groupName={saveGroupName}
        groupDescription={saveGroupDescription}
        isInteractionBlocked={isInteractionBlocked}
        onBeginSaving={onBeginSaving}
        onSave={onSave}
        onCancelSaving={onCancelSaving}
        onUpdate={onUpdate}
        onDelete={onDelete}
        onCancelEditing={onCancelEditing}
        onGroupNameChange={onSaveGroupNameChange}
        onGroupDescriptionChange={onSaveGroupDescriptionChange}
      />
    </div>
  );
}
