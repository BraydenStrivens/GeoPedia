/**
 * Displays the geographic features currently included in a manual feature
 * quiz-group selection.
 *
 * The list provides:
 *
 * - The number of selected geographic features.
 * - The number of distinct quiz answers represented by those features.
 * - Optional answer-label visibility while selecting features.
 * - A scrollable list of selected feature answers.
 * - Per-feature removal controls.
 * - Select All and Deselect All bulk-selection controls.
 *
 * Newly added features automatically scroll into view when the selected-feature
 * list exceeds its visible height.
 *
 * Selection state remains owned by the parent manual-selection workflow.
 */

"use client";

import { useEffect, useRef } from "react";

import type { ManualSelectionItem } from "@/quiz/groupings/feature/utils/getManualSelectionItems";

/**
 * Props required by the manual-selection list.
 */
type ManualSelectionListProps = {
  /** Selected geographic features and the quiz answers they represent. */
  selectionItems: ManualSelectionItem[];

  /** Number of distinct quiz answers represented by selected features. */
  selectedAnswerCount: number;

  /** Whether answer labels are currently displayed on the map. */
  showAnswers: boolean;

  /** Whether at least one available geographic feature remains unselected. */
  canSelectAll: boolean;

  /** Removes one geographic feature from the current manual selection. */
  onRemoveFeature: (featureId: string) => void;

  /** Selects every available geographic feature. */
  onSelectAll: () => void;

  /** Clears every selected geographic feature. */
  onDeselectAll: () => void;

  /** Toggles answer labels during manual feature selection. */
  onToggleShowAnswers: () => void;

  /**
   * Requests that the containing Groups panel follow newly expanded manual
   * selection content.
   */
  onRequestPanelScroll: () => void;
};

/**
 * Displays the current manual feature selection and controls for modifying it.
 *
 * Selected features remain visually compact so large manual selections can
 * expose as many entries as possible before the inner list begins scrolling.
 * Brand color is reserved for interactive emphasis rather than per-row cards.
 *
 * @param props - Selection state, answer-display state, and interaction
 * callbacks.
 * @param props.selectionItems - Currently selected geographic features.
 * @param props.selectedAnswerCount - Number of represented quiz answers.
 * @param props.showAnswers - Whether answer labels are shown on the map.
 * @param props.canSelectAll - Whether additional features remain available.
 * @param props.onRemoveFeature - Callback for removing one selected feature.
 * @param props.onSelectAll - Callback for selecting every available feature.
 * @param props.onDeselectAll - Callback for clearing the complete selection.
 * @param props.onToggleShowAnswers - Callback for toggling answer labels.
 * @param props.onRequestPanelScroll - Callback requesting outer-panel scrolling.
 * @returns Manual feature-selection list and bulk controls.
 */
export default function ManualSelectionList({
  selectionItems,
  selectedAnswerCount,
  showAnswers,
  canSelectAll,

  onRemoveFeature,
  onSelectAll,
  onDeselectAll,
  onToggleShowAnswers,

  onRequestPanelScroll,
}: ManualSelectionListProps) {
  /** Scrollable container displaying the currently selected features. */
  const selectionListRef = useRef<HTMLDivElement>(null);

  /**
   * Number of selected features rendered during the previous update.
   *
   * This allows the component to distinguish newly added selections from
   * removals, because only additions should trigger automatic scrolling.
   */
  const previousSelectionCountRef = useRef(selectionItems.length);

  /** Whether at least one geographic feature is currently selected. */
  const hasSelectedFeatures = selectionItems.length > 0;

  /**
   * Keeps newly selected features visible in both the inner selected-feature
   * list and the surrounding Groups panel.
   *
   * The outer panel only needs to move while the selected-feature container is
   * still growing. Once that container reaches its maximum visible height,
   * additional selections are handled entirely by its own scrollbar.
   *
   * Removing features does not force either scroll position to change.
   */
  useEffect(() => {
    const previousSelectionCount = previousSelectionCountRef.current;

    const currentSelectionCount = selectionItems.length;

    previousSelectionCountRef.current = currentSelectionCount;

    /*
     * Only newly added selections should trigger automatic scrolling.
     */
    if (currentSelectionCount <= previousSelectionCount) {
      return;
    }

    const selectionList = selectionListRef.current;

    if (!selectionList) {
      return;
    }

    /*
     * Determine whether the selected-feature container has reached its maximum
     * visible height.
     *
     * Once scrollHeight exceeds clientHeight, the inner container can handle
     * later additions using its own scrollbar.
     */
    const isSelectionListOverflowing =
      selectionList.scrollHeight > selectionList.clientHeight;

    /*
     * Keep the newest selected feature visible inside the list.
     */
    selectionList.scrollTo({
      top: selectionList.scrollHeight,
      behavior: "smooth",
    });

    /*
     * While the inner container is still growing vertically, keep the outer
     * Groups panel following its additional height as well.
     */
    if (!isSelectionListOverflowing) {
      onRequestPanelScroll();
    }
  }, [selectionItems.length, onRequestPanelScroll]);

  return (
    <>
      {/* Selection summary */}
      <div className="mt-2 flex items-center justify-between text-xs font-medium text-text-secondary">
        <span>{selectionItems.length} Features</span>

        <span>{selectedAnswerCount} Answers</span>
      </div>

      {/* Show Answers toggle */}
      <button
        type="button"
        onClick={onToggleShowAnswers}
        aria-pressed={showAnswers}
        className="
          mt-3 flex w-full items-center justify-between
          text-left
          focus-visible:outline-none focus-visible:ring-2
          focus-visible:ring-focus
        "
      >
        <span className="text-sm font-medium text-text">
          Show Answers
        </span>

        {/* Toggle indicator */}
        <span
          className={[
            "h-4 w-4 shrink-0 rounded-full border-2",
            "transition-colors",
            showAnswers
              ? [
                  "border-selected-control bg-selected-control",
                  "hover:border-selected-control-hover",
                  "hover:bg-selected-control-hover",
                ].join(" ")
              : [
                  "border-border-strong bg-surface",
                  "hover:border-border-hover hover:bg-brand-soft",
                ].join(" "),
          ].join(" ")}
        />
      </button>

      {/* Selected-feature list */}
      <div
        ref={selectionListRef}
        className="
          panel-scrollbar mt-3 max-h-48 space-y-1
          overflow-y-auto overscroll-contain
          rounded-lg border border-border
          bg-surface-muted p-2
        "
      >
        {!hasSelectedFeatures ? (
          /* Empty selection */
          <p className="px-1 py-2 text-center text-xs text-text-secondary">
            Select features on the map.
          </p>
        ) : (
          /* Selected geographic features */
          selectionItems.map((selectionItem) => (
            <div
              key={selectionItem.featureId}
              className="
                flex items-center justify-between gap-2
                rounded-md px-2 py-1
                text-sm text-text
                transition-colors
                hover:text-brand
              "
            >
              {/* Quiz answers represented by the feature */}
              <span className="min-w-0 flex-1 truncate">
                {selectionItem.answers.length > 0
                  ? selectionItem.answers.join(", ")
                  : "Unknown Answer"}
              </span>

              {/* Remove selected feature */}
              <button
                type="button"
                onClick={() =>
                  onRemoveFeature(selectionItem.featureId)
                }
                title="Remove feature"
                aria-label="Remove selected feature"
                className="
                  flex h-5 w-5 shrink-0 items-center justify-center
                  rounded text-sm font-bold text-text-secondary
                  transition-colors
                  hover:bg-brand-soft hover:text-brand
                  focus-visible:outline-none focus-visible:ring-2
                  focus-visible:ring-focus
                "
              >
                ×
              </button>
            </div>
          ))
        )}
      </div>

      {/* Bulk-selection controls */}
      <div className="mt-2 flex items-center justify-between">
        {/* Select every available feature */}
        <button
          type="button"
          disabled={!canSelectAll}
          onClick={onSelectAll}
          className={[
            "rounded text-xs font-medium underline",
            "transition-colors",
            "focus-visible:outline-none focus-visible:ring-2",
            "focus-visible:ring-focus",
            canSelectAll
              ? "text-text-secondary hover:text-brand"
              : "cursor-default text-disabled-text",
          ].join(" ")}
        >
          Select All
        </button>

        {/* Deselect every selected feature */}
        <button
          type="button"
          disabled={!hasSelectedFeatures}
          onClick={onDeselectAll}
          className={[
            "rounded text-xs font-medium underline",
            "transition-colors",
            "focus-visible:outline-none focus-visible:ring-2",
            "focus-visible:ring-focus",
            hasSelectedFeatures
              ? "text-text-secondary hover:text-brand"
              : "cursor-default text-disabled-text",
          ].join(" ")}
        >
          Deselect All
        </button>
      </div>
    </>
  );
}
