/**
 * Displays GeoPedia's property-based feature quiz-group editor.
 *
 * The section coordinates:
 *
 * - Selecting which configured GeoJSON property defines the available groups.
 * - Searching and selecting values belonging to that property.
 * - Displaying the currently selected grouping dimension.
 * - Saving new property-based groups.
 * - Updating or deleting existing saved property groups.
 *
 * Property-value searching and selection are delegated to
 * `PropertyGroupOptions`. Saved-group persistence controls are delegated to
 * `PropertyGroupActions`.
 */

"use client";

import { useState } from "react";

import type { QuizGroupingProperty } from "@/quiz/groupings/feature/types";
import type { QuizGroupingOption } from "@/quiz/groupings/feature/utils/getGroupingOptions";

import PropertyGroupActions from "./PropertyGroupActions";
import PropertyGroupOptions from "./PropertyGroupOptions";

/**
 * Props required by the Property Groups section.
 */
type PropertyGroupsSectionProps = {
  /** Grouping properties supported by the current feature quiz. */
  groupingProperties: QuizGroupingProperty[];

  /** Grouping property currently displayed by the editor. */
  selectedGroupingProperty: QuizGroupingProperty | null;

  /** Raw grouping-property values currently selected. */
  selectedValues: Set<string>;

  /** Selectable values discovered from the current GeoJSON property. */
  groupingOptions: QuizGroupingOption[];

  /**
   * Whether property-group mutations are temporarily blocked because another
   * grouping workflow currently owns interaction.
   */
  isInteractionBlocked: boolean;

  /** Whether an existing saved property group is currently being edited. */
  isEditingGroup: boolean;

  /** Whether the current saved-group edit can be persisted. */
  canUpdateGroup: boolean;

  /** Whether creation of a new saved property group may begin. */
  canBeginSavingGroup: boolean;

  /** Whether the currently entered new saved group can be persisted. */
  canSaveGroup: boolean;

  /** Whether the new saved-group metadata form is currently open. */
  isSavingGroup: boolean;

  /** Name draft for a new saved property group. */
  saveGroupName: string;

  /** Description draft for a new saved property group. */
  saveGroupDescription: string;

  /** Changes the GeoJSON property used for grouping. */
  onChangeGroupingProperty: (propertyName: string) => void;

  /** Toggles one raw grouping-property value. */
  onToggleGroupingValue: (value: string) => void;

  /** Clears every selected grouping-property value. */
  onDeselectAll: () => void;

  /** Opens the new saved-group metadata form. */
  onBeginSaving: () => void;

  /** Persists the current new saved-group draft. */
  onSave: () => void;

  /** Cancels creation of a new saved property group. */
  onCancelSaving: () => void;

  /** Persists changes to the saved group currently being edited. */
  onUpdate: () => void;

  /** Deletes the saved group currently being edited. */
  onDelete: () => void;

  /** Cancels saved-group editing. */
  onCancelEditing: () => void;

  /** Updates the new saved-group name draft. */
  onSaveGroupNameChange: (name: string) => void;

  /** Updates the new saved-group description draft. */
  onSaveGroupDescriptionChange: (description: string) => void;

  /** Requests that the containing Groups panel follow newly revealed content. */
  onRequestPanelScroll: () => void;
};

/**
 * Displays the collapsible Property Groups section.
 *
 * @param props - Property-group state, validation, and interaction callbacks.
 * @returns Property-based feature grouping controls.
 */
export default function PropertyGroupsSection({
  groupingProperties,
  selectedGroupingProperty,
  selectedValues,
  groupingOptions,

  isInteractionBlocked,

  isEditingGroup,
  canUpdateGroup,

  canBeginSavingGroup,
  canSaveGroup,
  isSavingGroup,

  saveGroupName,
  saveGroupDescription,

  onChangeGroupingProperty,
  onToggleGroupingValue,
  onDeselectAll,

  onBeginSaving,
  onSave,
  onCancelSaving,

  onUpdate,
  onDelete,
  onCancelEditing,

  onSaveGroupNameChange,
  onSaveGroupDescriptionChange,

  onRequestPanelScroll,
}: PropertyGroupsSectionProps) {
  /** Whether the Property Groups section content is currently expanded. */
  const [isExpanded, setIsExpanded] = useState(true);

  /**
   * Toggles visibility of the Property Groups controls.
   *
   * Expanding requests that the containing Groups panel scroll newly revealed
   * controls into view. Collapsing does not alter the panel's scroll position.
   */
  function togglePropertyGroupsExpanded(): void {
    setIsExpanded((wasExpanded) => {
      const willExpand = !wasExpanded;

      if (willExpand) {
        requestAnimationFrame(() => {
          onRequestPanelScroll();
        });
      }

      return willExpand;
    });
  }

  return (
    <section className="border-b border-border py-4">
      {/* Section heading and collapse control */}
      <div
        className={[
          "flex items-center justify-between",
          isExpanded ? "mb-2" : "",
        ].join(" ")}
      >
        {/* Section title */}
        <h3 className="text-sm font-semibold text-text">
          Property Groups
        </h3>

        {/* Expand / collapse section */}
        <button
          type="button"
          onClick={togglePropertyGroupsExpanded}
          title={
            isExpanded
              ? "Collapse Property Groups"
              : "Expand Property Groups"
          }
          aria-label={
            isExpanded
              ? "Collapse Property Groups"
              : "Expand Property Groups"
          }
          aria-expanded={isExpanded}
          className="flex h-6 w-6 items-center justify-center rounded-md text-text-secondary transition hover:bg-background-3 hover:text-text"
        >
          {/* Chevron icon */}
          <svg
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            className={[
              "h-4 w-4 transition-transform duration-200",
              isExpanded ? "rotate-180" : "",
            ].join(" ")}
            aria-hidden="true"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="m6 9 6 6 6-6"
            />
          </svg>
        </button>
      </div>

      {/* Expandable Property Groups content */}
      {isExpanded && (
        <>
          {/* Grouping-property selector */}
          {groupingProperties.length > 1 && (
            <select
              value={selectedGroupingProperty?.property ?? ""}
              disabled={isInteractionBlocked}
              onChange={(event) =>
                onChangeGroupingProperty(event.target.value)
              }
              className={[
                "mb-3 w-full rounded-lg border px-3 py-2 text-sm outline-none transition",
                isInteractionBlocked
                  ? "cursor-not-allowed border-border bg-disabled text-disabled-text"
                  : "border-border bg-background-1 text-text focus:border-focus",
              ].join(" ")}
            >
              {groupingProperties.map((groupingProperty) => (
                <option
                  key={groupingProperty.property}
                  value={groupingProperty.property}
                >
                  {groupingProperty.label}
                </option>
              ))}
            </select>
          )}

          {/* Current grouping dimension */}
          <div className="mb-2 text-xs font-medium text-text-secondary">
            {selectedGroupingProperty
              ? `Group by ${selectedGroupingProperty.label}`
              : "Select a grouping property"}
          </div>

          {/* Searchable property-value selection */}
          <PropertyGroupOptions
            selectedValues={selectedValues}
            groupingOptions={groupingOptions}
            isInteractionBlocked={isInteractionBlocked}
            onToggleValue={onToggleGroupingValue}
            onDeselectAll={onDeselectAll}
          />

          {/* Property-group persistence controls */}
          <PropertyGroupActions
            isInteractionBlocked={isInteractionBlocked}
            isEditingGroup={isEditingGroup}
            canUpdateGroup={canUpdateGroup}
            canBeginSavingGroup={canBeginSavingGroup}
            canSaveGroup={canSaveGroup}
            isSavingGroup={isSavingGroup}
            saveGroupName={saveGroupName}
            saveGroupDescription={saveGroupDescription}
            onBeginSaving={onBeginSaving}
            onSave={onSave}
            onCancelSaving={onCancelSaving}
            onUpdate={onUpdate}
            onDelete={onDelete}
            onCancelEditing={onCancelEditing}
            onSaveGroupNameChange={onSaveGroupNameChange}
            onSaveGroupDescriptionChange={
              onSaveGroupDescriptionChange
            }
          />
        </>
      )}
    </section>
  );
}
