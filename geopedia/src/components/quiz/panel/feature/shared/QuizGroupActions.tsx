/**
 * Displays shared persistence controls used by feature quiz-group editors.
 *
 * The component supports two workflows:
 *
 * - Creating a new saved group from the editor's current selection.
 * - Updating or deleting an existing saved group.
 *
 * New-group creation optionally displays shared name and description fields.
 * Domain-specific editors remain responsible for determining whether each
 * action is valid and for performing persistence.
 */

"use client";

import GroupMetadataFields from "./GroupMetadataFields";

/**
 * Props required by the shared quiz-group action controls.
 */
type QuizGroupActionsProps = {
  /** Whether an existing saved group is currently being edited. */
  isEditingGroup: boolean;

  /** Whether the current saved-group edit can be persisted. */
  canUpdateGroup: boolean;

  /** Whether creation of a new saved group may begin. */
  canBeginSavingGroup: boolean;

  /** Whether the completed new saved-group draft can be persisted. */
  canConfirmSaveGroup: boolean;

  /** Whether the new saved-group metadata form is currently open. */
  isSavingGroup: boolean;

  /** Name draft for the new saved group. */
  groupName: string;

  /** Description draft for the new saved group. */
  groupDescription: string;

  /**
   * Whether all mutating group actions are temporarily blocked by another
   * grouping workflow.
   */
  isInteractionBlocked?: boolean;

  /** Begins creation of a new saved group. */
  onBeginSaving: () => void;

  /** Persists the completed new saved group. */
  onSave: () => void;

  /** Cancels creation of the new saved group. */
  onCancelSaving: () => void;

  /** Persists changes to the saved group currently being edited. */
  onUpdate: () => void;

  /** Deletes the saved group currently being edited. */
  onDelete: () => void;

  /** Cancels editing of the current saved group. */
  onCancelEditing: () => void;

  /** Updates the new saved-group name draft. */
  onGroupNameChange: (name: string) => void;

  /** Updates the new saved-group description draft. */
  onGroupDescriptionChange: (description: string) => void;

  /**
   * Optional action displayed beneath creation controls while the metadata
   * form is closed.
   */
  onCancelWorkflow?: () => void;

  /** Label used by the optional complete-workflow cancellation action. */
  cancelWorkflowLabel?: string;
};

/**
 * Displays shared saved-group creation and editing actions.
 *
 * @param props - Shared group persistence state and callbacks.
 * @returns Quiz-group persistence controls.
 */
export default function QuizGroupActions({
  isEditingGroup,

  canUpdateGroup,
  canBeginSavingGroup,
  canConfirmSaveGroup,

  isSavingGroup,

  groupName,
  groupDescription,

  isInteractionBlocked = false,

  onBeginSaving,
  onSave,
  onCancelSaving,

  onUpdate,
  onDelete,
  onCancelEditing,

  onGroupNameChange,
  onGroupDescriptionChange,

  onCancelWorkflow,
  cancelWorkflowLabel = "Cancel",
}: QuizGroupActionsProps) {
  /** Whether the current saved-group edit may be persisted. */
  const canPerformUpdate = canUpdateGroup && !isInteractionBlocked;

  /**
   * Whether the primary creation action may currently be performed.
   *
   * Before the metadata form opens, this represents whether creation may begin.
   * Once the form is open, this represents whether the completed draft may be
   * saved.
   */
  const canPerformSaveAction =
    !isInteractionBlocked &&
    (isSavingGroup ? canConfirmSaveGroup : canBeginSavingGroup);

  return (
    <div className="space-y-2">
      {isEditingGroup ? (
        /* Existing saved-group editing */
        <>
          {/* Update / Delete saved group */}
          <div className="flex gap-2">
            {/* Update saved group */}
            <button
              type="button"
              disabled={!canPerformUpdate}
              onClick={onUpdate}
              className={[
                "flex-1 rounded-lg px-3 py-2",
                "text-sm font-semibold transition",
                canPerformUpdate
                  ? "bg-button text-button-text hover:bg-selected-control-hover"
                  : "cursor-default bg-disabled text-disabled-text",
              ].join(" ")}
            >
              Update
            </button>

            {/* Delete saved group */}
            <button
              type="button"
              disabled={isInteractionBlocked}
              onClick={onDelete}
              title="Delete saved group"
              aria-label="Delete saved group"
              className={[
                "flex h-9 w-9 shrink-0 items-center justify-center",
                "rounded-lg transition",
                isInteractionBlocked
                  ? "cursor-default bg-disabled text-disabled-text"
                  : "bg-danger text-button-text hover:bg-danger-hover",
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
              onClick={onCancelEditing}
              className="text-xs font-medium text-text-secondary underline transition hover:text-text"
            >
              Cancel
            </button>
          </div>
        </>
      ) : (
        /* New saved-group creation */
        <>
          {/* Begin or confirm saved-group creation */}
          <button
            type="button"
            disabled={!canPerformSaveAction}
            onClick={isSavingGroup ? onSave : onBeginSaving}
            className={[
              "w-full rounded-lg px-3 py-2",
              "text-sm font-semibold transition",
              canPerformSaveAction
                ? "bg-button text-button-text hover:bg-selected-control-hover"
                : "cursor-default bg-disabled text-disabled-text",
            ].join(" ")}
          >
            {isSavingGroup ? "Save" : "Save Group"}
          </button>

          {/* New saved-group metadata */}
          {isSavingGroup && (
            <div className="rounded-lg border border-border bg-background-1 p-3">
              <GroupMetadataFields
                name={groupName}
                description={groupDescription}
                onNameChange={onGroupNameChange}
                onDescriptionChange={onGroupDescriptionChange}
              />

              {/* Cancel saved-group creation */}
              <div className="mt-2 flex justify-end">
                <button
                  type="button"
                  onClick={onCancelSaving}
                  className="text-xs font-medium text-text-secondary underline transition hover:text-text"
                >
                  Cancel
                </button>
              </div>
            </div>
          )}

          {/* Optional complete-workflow cancellation */}
          {!isSavingGroup && onCancelWorkflow && (
            <div className="flex justify-end">
              <button
                type="button"
                onClick={onCancelWorkflow}
                className="text-xs font-medium text-text-secondary underline transition hover:text-text"
              >
                {cancelWorkflowLabel}
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
