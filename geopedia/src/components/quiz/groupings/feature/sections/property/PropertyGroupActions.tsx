/**
 * Displays persistence controls for property-based quiz groups.
 *
 * Normal mode allows the current property selection to be saved as a new
 * group. Edit mode replaces that workflow with Update, Delete, and Cancel
 * controls for the saved group currently being edited.
 */

"use client";

import GroupMetadataFields from "../../shared/GroupMetadataFields";

/**
 * Props required by the property-group action controls.
 */
type PropertyGroupActionsProps = {
  /** Whether an existing saved property group is currently being edited. */
  isEditingGroup: boolean;

  /** Whether the current saved-group edit can be persisted. */
  canUpdateGroup: boolean;

  /** Whether creation of a new saved group may begin. */
  canBeginSavingGroup: boolean;

  /** Whether the current new saved-group draft can be persisted. */
  canSaveGroup: boolean;

  /** Whether the new saved-group metadata form is currently open. */
  isSavingGroup: boolean;

  /** Name draft for a new saved property group. */
  saveGroupName: string;

  /** Description draft for a new saved property group. */
  saveGroupDescription: string;

  /** Whether persistence controls are currently disabled. */
  isDisabled: boolean;

  /** Opens the new saved-group metadata form. */
  onBeginSaving: () => void;

  /** Persists the current new saved group. */
  onSave: () => void;

  /** Cancels creation of a new saved group. */
  onCancelSaving: () => void;

  /** Persists changes to the saved group currently being edited. */
  onUpdate: () => void;

  /** Deletes the saved group currently being edited. */
  onDelete: () => void;

  /** Cancels editing and restores the saved group's persisted state. */
  onCancelEditing: () => void;

  /** Updates the new saved-group name draft. */
  onSaveGroupNameChange: (name: string) => void;

  /** Updates the new saved-group description draft. */
  onSaveGroupDescriptionChange: (description: string) => void;
};

/**
 * Displays Save controls for new groups or Update/Delete controls while
 * editing an existing saved group.
 *
 * @param props - Current save/edit state and persistence callbacks.
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
  isDisabled,
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
    <div className="mt-4 space-y-2">
      {isEditingGroup ? (
        /* Existing saved-group editing */
        <>
          {/* Update / Delete saved group */}
          <div className="flex gap-2">
            {/* Update saved group */}
            <button
              type="button"
              disabled={!canUpdateGroup}
              onClick={onUpdate}
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
              onClick={onDelete}
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
              onClick={onCancelEditing}
              className="text-xs font-medium text-gray-600 underline transition hover:text-gray-900"
            >
              Cancel
            </button>
          </div>
        </>
      ) : (
        /* New saved-group creation */
        <>
          {/* Save property group */}
          <button
            type="button"
            disabled={
              isSavingGroup ? !canSaveGroup : !canBeginSavingGroup
            }
            onClick={isSavingGroup ? onSave : onBeginSaving}
            className={[
              "w-full rounded-lg px-3 py-2 text-sm font-semibold transition",

              (isSavingGroup ? canSaveGroup : canBeginSavingGroup)
                ? "bg-gray-900 text-white hover:bg-gray-700"
                : "bg-gray-300 text-gray-500",
            ].join(" ")}
          >
            {isSavingGroup ? "Save" : "Save Group"}
          </button>

          {/* New saved-group metadata */}
          {isSavingGroup && (
            <div className="rounded-lg border border-gray-300 bg-white p-3">
              <GroupMetadataFields
                name={saveGroupName}
                description={saveGroupDescription}
                onNameChange={onSaveGroupNameChange}
                onDescriptionChange={onSaveGroupDescriptionChange}
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
        </>
      )}
    </div>
  );
}
