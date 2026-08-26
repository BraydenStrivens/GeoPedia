/**
 * Displays GeoPedia's property-based quiz-group editor.
 *
 * The section coordinates:
 *
 * - Selecting which configured GeoJSON property should define groups.
 * - Searching and selecting values from that property.
 * - Displaying the current grouping dimension.
 * - Saving new property groups.
 * - Updating or deleting existing saved property groups.
 *
 * Search and option-list rendering are delegated to PropertyGroupOptions.
 * Saved-group persistence controls are delegated to PropertyGroupActions.
 */

"use client";

import { useState } from "react";

import type { QuizGroupingProperty } from "@/quiz/groupings/types";
import type { QuizGroupingOption } from "@/quiz/groupings/utils/getGroupingOptions";

import PropertyGroupActions from "./PropertyGroupActions";
import PropertyGroupOptions from "./PropertyGroupOptions";

/**
 * Props required by the Property Groups section.
 */
type PropertyGroupsSectionProps = {
  /** Grouping properties supported by the current quiz. */
  groupingProperties: QuizGroupingProperty[];

  /** Grouping property currently displayed by the editor. */
  selectedGroupingProperty: QuizGroupingProperty | null;

  /** Raw property values currently selected. */
  selectedValues: Set<string>;

  /** Selectable values discovered from the current GeoJSON property. */
  groupingOptions: QuizGroupingOption[];

  /** Whether property-group controls are currently disabled. */
  isDisabled: boolean;

  /** Whether an existing saved property group is currently being edited. */
  isEditingGroup: boolean;

  /** Whether the current saved-group edit can be persisted. */
  canUpdateGroup: boolean;

  /** Whether creation of a new saved property group may begin. */
  canBeginSavingGroup: boolean;

  /** Whether the currently entered new saved group can be persisted. */
  canSaveGroup: boolean;

  /** Whether the new saved-group metadata form is open. */
  isSavingGroup: boolean;

  /** Name draft for a new saved property group. */
  saveGroupName: string;

  /** Description draft for a new saved property group. */
  saveGroupDescription: string;

  /** Changes the GeoJSON property used for grouping. */
  onChangeGroupingProperty: (propertyName: string) => void;

  /** Toggles one raw property value. */
  onToggleGroupingValue: (value: string) => void;

  /** Clears every selected property value. */
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
 * @returns Property-based grouping controls.
 */
export default function PropertyGroupsSection({
  groupingProperties,
  selectedGroupingProperty,
  selectedValues,
  groupingOptions,
  isDisabled,
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
   * Toggles whether the Property Groups controls are visible.
   *
   * Expanding requests that the containing Groups panel scroll the newly
   * revealed controls into view. Collapsing does not change the panel's scroll
   * position.
   */
  function toggleExpanded(): void {
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
    <section className="border-b border-gray-300 py-4">
      {/* Section heading and collapse control */}
      <div
        className={
          isExpanded
            ? "mb-2 flex items-center justify-between"
            : "flex items-center justify-between"
        }
      >
        {/* Section title */}
        <h3 className="text-sm font-semibold text-gray-800">
          Property Groups
        </h3>

        {/* Expand / collapse section */}
        <button
          type="button"
          onClick={toggleExpanded}
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
          className="flex h-6 w-6 items-center justify-center rounded-md text-gray-500 transition hover:bg-gray-300 hover:text-gray-900"
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
          {/* Grouping property selector */}
          {groupingProperties.length > 1 && (
            <select
              value={selectedGroupingProperty?.property ?? ""}
              disabled={isDisabled}
              onChange={(event) =>
                onChangeGroupingProperty(event.target.value)
              }
              className="mb-3 w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-gray-800"
            >
              {groupingProperties.map((property) => (
                <option
                  key={property.property}
                  value={property.property}
                >
                  {property.label}
                </option>
              ))}
            </select>
          )}

          {/* Current grouping dimension */}
          <div className="mb-2 text-xs font-medium text-gray-500">
            {selectedGroupingProperty
              ? `Group by ${selectedGroupingProperty.label}`
              : "Select a group"}
          </div>

          {/* Searchable property-value selection */}
          <PropertyGroupOptions
            selectedValues={selectedValues}
            groupingOptions={groupingOptions}
            isDisabled={isDisabled}
            onToggleValue={onToggleGroupingValue}
            onDeselectAll={onDeselectAll}
          />

          {/* Property-group persistence controls */}
          <PropertyGroupActions
            isEditingGroup={isEditingGroup}
            canUpdateGroup={canUpdateGroup}
            canBeginSavingGroup={canBeginSavingGroup}
            canSaveGroup={canSaveGroup}
            isSavingGroup={isSavingGroup}
            saveGroupName={saveGroupName}
            saveGroupDescription={saveGroupDescription}
            isDisabled={isDisabled}
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
