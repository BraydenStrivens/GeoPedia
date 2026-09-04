/**
 * Displays controls for constructing feature quiz groups by manually selecting
 * geographic map features.
 *
 * The section coordinates the high-level manual-selection workflow:
 *
 * - Entering map feature-selection mode.
 * - Expanding and collapsing the Manual Selection interface.
 * - Displaying controls for the currently selected geographic features.
 * - Displaying creation or editing actions for manual saved groups.
 *
 * Selected-feature rendering and bulk-selection controls are delegated to
 * `ManualSelectionList`. Saved-group persistence controls are delegated to
 * `ManualGroupActions`.
 */

"use client";

import { useState } from "react";

import type { ManualSelectionItem } from "@/quiz/groupings/feature/utils/getManualSelectionItems";

import ManualGroupActions from "./ManualGroupActions";
import ManualSelectionList from "./ManualSelectionList";

/**
 * Props required by the Manual Selection section.
 */
type ManualSelectionSectionProps = {
  /** Whether map clicks currently toggle manual geographic-feature selection. */
  isSelecting: boolean;

  /** Selected features together with the quiz answers they represent. */
  selectionItems: ManualSelectionItem[];

  /** Number of distinct quiz answers represented by selected features. */
  selectedAnswerCount: number;

  /** Whether answer labels are displayed while selecting features. */
  showAnswers: boolean;

  /** Whether the current manual selection is eligible to begin saving. */
  canSave: boolean;

  /** Whether the manual-group metadata form is currently open. */
  isSavingGroup: boolean;

  /** Whether the current selection is editing an existing saved manual group. */
  isEditingGroup: boolean;

  /** Whether changes to the saved manual group can currently be persisted. */
  canUpdate: boolean;

  /** Name draft for a new saved manual group. */
  groupName: string;

  /** Description draft for a new saved manual group. */
  groupDescription: string;

  /** Whether the completed new saved-group draft can be persisted. */
  canConfirmSave: boolean;

  /** Whether at least one available geographic feature remains unselected. */
  canSelectAll: boolean;

  /** Opens the new manual saved-group metadata form. */
  onBeginSaving: () => void;

  /** Persists the current manual selection as a new saved group. */
  onSave: () => void;

  /** Cancels the new manual saved-group metadata form. */
  onCancelSaving: () => void;

  /** Cancels editing of an existing saved manual group. */
  onCancelEditing: () => void;

  /** Updates the new manual saved-group name draft. */
  onGroupNameChange: (name: string) => void;

  /** Updates the new manual saved-group description draft. */
  onGroupDescriptionChange: (description: string) => void;

  /** Begins a new manual map feature-selection session. */
  onBeginSelection: () => void;

  /** Removes one geographic feature from the current manual selection. */
  onRemoveFeature: (featureId: string) => void;

  /** Clears every manually selected geographic feature. */
  onDeselectAll: () => void;

  /** Selects every available geographic feature. */
  onSelectAll: () => void;

  /** Toggles answer labels during manual feature selection. */
  onToggleShowAnswers: () => void;

  /** Cancels the complete manual-selection workflow. */
  onCancel: () => void;

  /** Persists changes to the saved manual group currently being edited. */
  onUpdate: () => void;

  /** Deletes the saved manual group currently being edited. */
  onDelete: () => void;

  /** Requests that the containing Groups panel follow newly revealed content. */
  onRequestPanelScroll: () => void;
};

/**
 * Displays the collapsible Manual Selection section.
 *
 * @param props - Manual-selection state, validation, and interaction callbacks.
 * @returns Manual geographic-feature selection controls.
 */
export default function ManualSelectionSection({
  isSelecting,

  selectionItems,
  selectedAnswerCount,
  showAnswers,
  canSelectAll,

  canSave,
  canUpdate,
  canConfirmSave,

  isSavingGroup,
  isEditingGroup,

  groupName,
  groupDescription,

  onBeginSelection,

  onRemoveFeature,
  onDeselectAll,
  onSelectAll,
  onToggleShowAnswers,

  onBeginSaving,
  onSave,
  onCancelSaving,

  onUpdate,
  onDelete,
  onCancelEditing,

  onGroupNameChange,
  onGroupDescriptionChange,

  onCancel,

  onRequestPanelScroll,
}: ManualSelectionSectionProps) {
  /** Whether the Manual Selection section content is currently expanded. */
  const [isExpanded, setIsExpanded] = useState(true);

  /**
   * Toggles visibility of the Manual Selection controls.
   *
   * Expanding requests that the containing Groups panel follow the newly
   * revealed content. Collapsing preserves the complete manual-selection
   * workflow without changing the panel's scroll position.
   */
  function toggleManualSelectionExpanded(): void {
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
        className={[
          "flex items-center justify-between",
          isExpanded ? "mb-2" : "",
        ].join(" ")}
      >
        {/* Section title */}
        <h3 className="text-sm font-semibold text-text">
          Manual Selection
        </h3>

        {/* Expand / collapse section */}
        <button
          type="button"
          onClick={toggleManualSelectionExpanded}
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

      {/* Expandable Manual Selection content */}
      {isExpanded && (
        <>
          {!isSelecting ? (
            /* Inactive manual-selection state */
            <>
              {/* Manual-selection explanation */}
              <p className="text-xs leading-relaxed text-text-secondary">
                Create a custom group by selecting individual
                geographic features on the map.
              </p>

              {/* Begin manual feature selection */}
              <button
                type="button"
                onClick={onBeginSelection}
                className="mt-3 w-full rounded-lg bg-button px-3 py-2 text-sm font-semibold text-button-text transition hover:bg-selected-control-hover"
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
                canConfirmSave={canConfirmSave}
                isSavingGroup={isSavingGroup}
                isEditingGroup={isEditingGroup}
                groupName={groupName}
                groupDescription={groupDescription}
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
