/**
 * Displays the quiz groups previously saved by the user.
 *
 * Saved-group rows support:
 *
 * - Activating or deactivating a saved group.
 * - Displaying an optional saved-group description.
 * - Entering or leaving saved-group edit mode.
 * - Visually identifying the active and currently edited groups.
 *
 * Persistence and editing logic are owned by QuizGroupsPanel. This component
 * is responsible only for presenting saved-group state and forwarding user
 * interactions.
 */

"use client";

import type { SavedQuizGroup } from "@/quiz/groupings/feature/types";

/**
 * Props required by the Saved Groups section.
 */
type SavedGroupsSectionProps = {
  /** Groups saved for the current quiz. */
  savedGroups: SavedQuizGroup[];

  /** ID of the saved group currently active on the quiz. */
  activeSavedGroupId: string | null;

  /** ID of the saved group currently being edited. */
  editingGroupId: string | null;

  /** ID of the saved group whose description is currently expanded. */
  openDescriptionGroupId: string | null;

  /** Whether saved-group controls are currently disabled. */
  isDisabled: boolean;

  /** Activates or deactivates a saved group. */
  onToggleGroup: (group: SavedQuizGroup) => void;

  /** Opens or closes a saved group's optional description. */
  onToggleDescription: (groupId: string) => void;

  /** Toggles edit mode or switches editing to another saved group. */
  onToggleEditing: (group: SavedQuizGroup) => void;
};

/**
 * Displays saved quiz groups and their activation, description, and editing
 * controls.
 *
 * @param props - Saved-group state and interaction callbacks.
 * @returns The Saved Groups section.
 */
export default function SavedGroupsSection({
  savedGroups,
  activeSavedGroupId,
  editingGroupId,
  openDescriptionGroupId,
  isDisabled,
  onToggleGroup,
  onToggleDescription,
  onToggleEditing,
}: SavedGroupsSectionProps) {
  /** Whether at least one saved group exists for the current quiz. */
  const hasSavedGroups = savedGroups.length > 0;

  return (
    <section className="border-b border-gray-300 py-4">
      {/* Section heading and saved-group count */}
      <div className="mb-2 flex items-center justify-between">
        <h3 className="text-sm font-semibold text-gray-800">
          Saved Groups
        </h3>

        {/* Saved-group count */}
        <span className="text-xs text-gray-600">
          {savedGroups.length}
        </span>
      </div>

      {!hasSavedGroups ? (
        /* Empty saved-groups state */
        <p className="text-xs text-gray-500">
          Saved groups will appear here.
        </p>
      ) : (
        /* Scrollable saved-group list */
        <div className="panel-scrollbar max-h-48 space-y-2 overflow-y-auto overscroll-contain rounded-lg border border-gray-300 bg-transparent p-2 transition-colors hover:bg-gray-300/60">
          {savedGroups.map((savedGroup) => {
            /** Whether this group currently controls the quiz. */
            const isActive = activeSavedGroupId === savedGroup.id;

            /** Whether this group's optional description is expanded. */
            const isDescriptionOpen =
              openDescriptionGroupId === savedGroup.id;

            /** Whether this saved group is currently being edited. */
            const isBeingEdited = editingGroupId === savedGroup.id;

            return (
              <div
                key={savedGroup.id}
                className={[
                  "overflow-hidden rounded-lg border transition-colors",

                  isActive
                    ? "border-gray-900 bg-gray-900 text-white hover:bg-gray-800"
                    : "border-gray-300 bg-white text-gray-800 hover:bg-gray-300/60",
                ].join(" ")}
              >
                {/* Saved-group primary and secondary controls */}
                <div className="flex items-center">
                  {/* Saved-group activation toggle */}
                  <button
                    type="button"
                    disabled={isDisabled}
                    onClick={() => onToggleGroup(savedGroup)}
                    className={[
                      "flex min-w-0 flex-1 items-center px-3 py-2 text-left transition",

                      isDisabled
                        ? "cursor-not-allowed opacity-50"
                        : "",
                    ].join(" ")}
                  >
                    <span className="truncate text-sm font-semibold">
                      {savedGroup.name}
                    </span>
                  </button>

                  {/* Saved-group secondary controls */}
                  <div className="flex shrink-0 items-center gap-1 pr-2">
                    {/* Optional description toggle */}
                    {savedGroup.description && (
                      <button
                        type="button"
                        disabled={isDisabled}
                        onClick={() =>
                          onToggleDescription(savedGroup.id)
                        }
                        title={
                          isDescriptionOpen
                            ? "Hide group description"
                            : "Show group description"
                        }
                        aria-label={
                          isDescriptionOpen
                            ? `Hide description for ${savedGroup.name}`
                            : `Show description for ${savedGroup.name}`
                        }
                        aria-expanded={isDescriptionOpen}
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

                    {/* Saved-group edit toggle */}
                    <button
                      type="button"
                      disabled={isDisabled}
                      onClick={() => onToggleEditing(savedGroup)}
                      title={
                        isBeingEdited
                          ? "Stop editing saved group"
                          : "Edit saved group"
                      }
                      aria-label={
                        isBeingEdited
                          ? `Stop editing ${savedGroup.name}`
                          : `Edit ${savedGroup.name}`
                      }
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

                {/* Expanded saved-group description */}
                {savedGroup.description && isDescriptionOpen && (
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
  );
}
