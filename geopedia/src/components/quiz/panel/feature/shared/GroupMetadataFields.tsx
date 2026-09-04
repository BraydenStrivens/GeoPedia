/**
 * Displays editable metadata fields shared by saved feature quiz-group
 * workflows.
 *
 * Property-based and manually selected groups use the same fields when
 * creating a new saved group or editing an existing saved group.
 *
 * Metadata state remains owned by the parent group workflow.
 */

"use client";

/**
 * Props required by the shared saved-group metadata fields.
 */
type GroupMetadataFieldsProps = {
  /** Current saved-group name draft. */
  name: string;

  /** Current optional saved-group description draft. */
  description: string;

  /** Updates the saved-group name draft. */
  onNameChange: (name: string) => void;

  /** Updates the saved-group description draft. */
  onDescriptionChange: (description: string) => void;
};

/**
 * Displays editable name and optional description fields for a saved feature
 * quiz group.
 *
 * @param props - Current metadata drafts and change callbacks.
 * @returns Shared saved-group metadata controls.
 */
export default function GroupMetadataFields({
  name,
  description,
  onNameChange,
  onDescriptionChange,
}: GroupMetadataFieldsProps) {
  return (
    <>
      {/* Group name */}
      <label className="block">
        <span className="text-xs font-medium text-text-secondary">
          Name
        </span>

        <input
          type="text"
          value={name}
          onChange={(event) => onNameChange(event.target.value)}
          placeholder="Group name"
          className="mt-1 w-full rounded-lg border border-border bg-background-1 px-3 py-2 text-sm text-text outline-none transition focus:border-focus"
        />
      </label>

      {/* Optional group description */}
      <label className="mt-3 block">
        <span className="text-xs font-medium text-text-secondary">
          Description
          <span className="ml-1 font-normal text-disabled-text">
            Optional
          </span>
        </span>

        <textarea
          value={description}
          onChange={(event) =>
            onDescriptionChange(event.target.value)
          }
          placeholder="Describe this group"
          rows={3}
          className="mt-1 w-full resize-none rounded-lg border border-border bg-background-1 px-3 py-2 text-sm text-text outline-none transition focus:border-focus"
        />
      </label>
    </>
  );
}
