/**
 * Displays controls for constructing quiz groups by manually selecting
 * geographic map features.
 *
 * This section coordinates the high-level manual-selection workflow:
 *
 * - Entering map feature-selection mode.
 * - Expanding and collapsing the Manual Selection interface.
 * - Displaying the current selected-feature controls.
 * - Displaying creation or editing actions for manual saved groups.
 *
 * Selected-feature rendering is delegated to ManualSelectionList.
 * Persistence controls are delegated to ManualGroupActions.
 */

"use client";

import { useState } from "react";

import type { ManualSelectionItem } from "@/quiz/groupings/utils/getManualSelectionItems";

import ManualGroupActions from "./ManualGroupActions";
import ManualSelectionList from "./ManualSelectionList";

/**
 * Props required by the Manual Selection section.
 */
type ManualSelectionSectionProps = {
  /** Whether map clicks currently toggle manual feature selection. */
  isSelecting: boolean;

  /** Selected features together with the quiz answers they represent. */
  selectionItems: ManualSelectionItem[];

  /** Number of distinct quiz answers represented by selected features. */
  selectedAnswerCount: number;

  /** Whether answer labels should be displayed while selecting features. */
  showAnswers: boolean;

  /** Whether the current selection is eligible to be saved. */
  canSave: boolean;

  /** Whether the manual-group save form is currently open. */
  isSavingGroup: boolean;

  /** Whether the current selection is editing an existing manual saved group. */
  isEditingGroup: boolean;

  /** Whether the current saved-group edit can be persisted. */
  canUpdate: boolean;

  /** Current new manual saved-group name draft. */
  groupName: string;

  /** Current new manual saved-group description draft. */
  groupDescription: string;

  /** Whether the current new saved-group draft can be persisted. */
  canConfirmSave: boolean;

  /** Whether there are still unselected geographic features. */
  canSelectAll: boolean;

  /** Opens the new manual saved-group metadata form. */
  onBeginSaving: () => void;

  /** Persists the current manual selection as a new saved group. */
  onSave: () => void;

  /** Cancels the new manual saved-group metadata form. */
  onCancelSaving: () => void;

  /** Cancels editing of an existing manual saved group. */
  onCancelEditing: () => void;

  /** Updates the new manual saved-group name draft. */
  onGroupNameChange: (name: string) => void;

  /** Updates the new manual saved-group description draft. */
  onGroupDescriptionChange: (description: string) => void;

  /** Begins a new manual map feature-selection session. */
  onBeginSelection: () => void;

  /** Removes one feature from the current manual selection. */
  onRemoveFeature: (featureId: string) => void;

  /** Clears every manually selected feature. */
  onDeselectAll: () => void;

  /** Selects every available geographic feature. */
  onSelectAll: () => void;

  /** Toggles answer labels during manual feature selection. */
  onToggleShowAnswers: () => void;

  /** Cancels the complete manual-selection workflow. */
  onCancel: () => void;

  /** Persists changes to the manual saved group currently being edited. */
  onUpdate: () => void;

  /** Deletes the manual saved group currently being edited. */
  onDelete: () => void;

  /** Requests that the containing Groups panel scroll newly revealed content into view. */
  onRequestPanelScroll: () => void;
};

/**
 * Displays the collapsible Manual Selection section.
 *
 * @param props - Manual-selection state, validation, and interaction callbacks.
 * @returns Manual feature-selection controls.
 */
export default function ManualSelectionSection({
  isSelecting,
  selectionItems,
  selectedAnswerCount,
  showAnswers,
  canSave,
  canUpdate,
  canSelectAll,
  isSavingGroup,
  isEditingGroup,
  groupName,
  groupDescription,
  canConfirmSave,
  onBeginSelection,
  onRemoveFeature,
  onDeselectAll,
  onSelectAll,
  onToggleShowAnswers,
  onCancel,
  onBeginSaving,
  onSave,
  onUpdate,
  onDelete,
  onCancelEditing,
  onCancelSaving,
  onGroupNameChange,
  onGroupDescriptionChange,
  onRequestPanelScroll,
}: ManualSelectionSectionProps) {
  /** Whether the Manual Selection section content is currently expanded. */
  const [isExpanded, setIsExpanded] = useState(true);

  /**
   * Toggles whether the Manual Selection controls are visible.
   *
   * Expanding requests that the outer Groups panel follow the newly revealed
   * content. Collapsing preserves all workflow state without changing scroll
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
    <section className="pt-4">
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
          Manual Selection
        </h3>

        {/* Expand / collapse section */}
        <button
          type="button"
          onClick={toggleExpanded}
          title={
            isExpanded
              ? "Collapse Manual Selection"
              : "Expand Manual Selection"
          }
          aria-label={
            isExpanded
              ? "Collapse Manual Selection"
              : "Expand Manual Selection"
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

      {/* Expandable Manual Selection content */}
      {isExpanded && (
        <>
          {!isSelecting ? (
            /* Inactive manual-selection state */
            <>
              {/* Manual-selection explanation */}
              <p className="text-xs leading-relaxed text-gray-500">
                Create a custom group by selecting individual
                geographic features on the map.
              </p>

              {/* Begin manual feature selection */}
              <button
                type="button"
                onClick={onBeginSelection}
                className="mt-3 w-full rounded-lg bg-gray-900 px-3 py-2 text-sm font-semibold text-white transition hover:bg-gray-700"
              >
                Select Features
              </button>
            </>
          ) : (
            /* Active manual-selection workflow */
            <>
              {/* Current selected features and bulk-selection controls */}
              <ManualSelectionList
                selectionItems={selectionItems}
                selectedAnswerCount={selectedAnswerCount}
                showAnswers={showAnswers}
                canSelectAll={canSelectAll}
                onRemoveFeature={onRemoveFeature}
                onSelectAll={onSelectAll}
                onDeselectAll={onDeselectAll}
                onToggleShowAnswers={onToggleShowAnswers}
                onRequestPanelScroll={onRequestPanelScroll}
              />

              {/* Manual-group persistence and cancellation controls */}
              <ManualGroupActions
                canSave={canSave}
                canUpdate={canUpdate}
                isSavingGroup={isSavingGroup}
                isEditingGroup={isEditingGroup}
                groupName={groupName}
                groupDescription={groupDescription}
                canConfirmSave={canConfirmSave}
                onBeginSaving={onBeginSaving}
                onSave={onSave}
                onUpdate={onUpdate}
                onDelete={onDelete}
                onCancelEditing={onCancelEditing}
                onCancelSaving={onCancelSaving}
                onCancelSelection={onCancel}
                onGroupNameChange={onGroupNameChange}
                onGroupDescriptionChange={onGroupDescriptionChange}
              />
            </>
          )}
        </>
      )}
    </section>
  );
}
