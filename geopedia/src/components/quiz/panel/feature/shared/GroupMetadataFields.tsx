/**
 * Displays editable metadata fields shared by saved quiz-group workflows.
 *
 * Both property-based and manually selected groups use these fields when
 * creating a new saved group or editing an existing one.
 */

"use client";

/**
 * Props required by the saved-group metadata fields.
 */
type GroupMetadataFieldsProps = {
  /** Current group-name draft. */
  name: string;

  /** Current optional group-description draft. */
  description: string;

  /** Updates the group-name draft. */
  onNameChange: (name: string) => void;

  /** Updates the group-description draft. */
  onDescriptionChange: (description: string) => void;
};

/**
 * Displays editable name and optional description fields for a saved quiz
 * group.
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
        <span className="text-xs font-medium text-gray-600">
          Name
        </span>

        <input
          type="text"
          value={name}
          onChange={(event) => onNameChange(event.target.value)}
          placeholder="Group name"
          className="mt-1 w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 outline-none transition focus:border-gray-500"
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
          value={description}
          onChange={(event) =>
            onDescriptionChange(event.target.value)
          }
          placeholder="Describe this group"
          rows={3}
          className="mt-1 w-full resize-none rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 outline-none transition focus:border-gray-500"
        />
      </label>
    </>
  );
}
