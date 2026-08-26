/**
 * Displays persistence and cancellation controls for manual quiz groups.
 *
 * During creation, the component allows the current feature selection to be
 * named, optionally described, and saved.
 *
 * During saved-group editing, creation controls are replaced with Update,
 * Delete, and Cancel actions.
 */

"use client";

import GroupMetadataFields from "../../shared/GroupMetadataFields";

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
 * Displays Save controls during creation or Update/Delete controls during
 * editing.
 *
 * @param props - Current manual-group save/edit state and callbacks.
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
    <div className="mt-3 space-y-2">
      {isEditingGroup ? (
        /* Existing manual saved-group editing */
        <>
          {/* Update / Delete saved group */}
          <div className="flex gap-2">
            {/* Update saved group */}
            <button
              type="button"
              disabled={!canUpdate}
              onClick={onUpdate}
              className={[
                "flex-1 rounded-lg px-3 py-2 text-sm font-semibold transition",

                canUpdate
                  ? "bg-gray-900 text-white hover:bg-gray-700"
                  : "bg-gray-300 text-gray-500",
              ].join(" ")}
            >
              Update
            </button>

            {/* Delete saved group */}
            <button
              type="button"
              onClick={onDelete}
              title="Delete saved group"
              aria-label="Delete saved group"
              className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-red-600 text-white transition hover:bg-red-700"
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

          {/* Cancel manual saved-group editing */}
          <div className="flex justify-end">
            <button
              type="button"
              onClick={onCancelEditing}
              className="text-xs font-medium text-gray-600 underline transition hover:text-gray-900"
            >
              Cancel
            </button>
          </div>
        </>
      ) : (
        /* New manual saved-group creation */
        <>
          {/* Save manual group */}
          <button
            type="button"
            disabled={isSavingGroup ? !canConfirmSave : !canSave}
            onClick={isSavingGroup ? onSave : onBeginSaving}
            className={[
              "w-full rounded-lg px-3 py-2 text-sm font-semibold transition",

              (isSavingGroup ? canConfirmSave : canSave)
                ? "bg-gray-900 text-white hover:bg-gray-700"
                : "bg-gray-300 text-gray-500",
            ].join(" ")}
          >
            {isSavingGroup ? "Save" : "Save Group"}
          </button>

          {/* New manual saved-group metadata */}
          {isSavingGroup && (
            <div className="rounded-lg border border-gray-300 bg-white p-3">
              <GroupMetadataFields
                name={groupName}
                description={groupDescription}
                onNameChange={onGroupNameChange}
                onDescriptionChange={onGroupDescriptionChange}
              />

              {/* Cancel new saved-group creation */}
              <div className="mt-2 flex justify-end">
                <button
                  type="button"
                  onClick={onCancelSaving}
                  className="text-xs font-medium text-gray-600 underline transition hover:text-gray-900"
                >
                  Cancel
                </button>
              </div>
            </div>
          )}

          {/* Cancel complete manual-selection workflow */}
          {!isSavingGroup && (
            <div className="flex justify-end">
              <button
                type="button"
                onClick={onCancelSelection}
                className="text-xs font-medium text-gray-600 underline transition hover:text-gray-900"
              >
                Cancel
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
