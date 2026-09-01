/**
 * Displays the features currently included in a manual quiz-group selection.
 *
 * The list provides:
 *
 * - The number of selected geographic features.
 * - The number of distinct quiz answers represented by those features.
 * - Optional answer visibility during map selection.
 * - A scrollable list of selected feature answers.
 * - Per-feature removal controls.
 * - Select All and Deselect All bulk-selection controls.
 *
 * Newly selected features automatically scroll into view when the selected
 * feature list exceeds its visible height.
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
  /** Selected features together with the quiz answers they represent. */
  selectionItems: ManualSelectionItem[];

  /** Number of distinct quiz answers represented by selected features. */
  selectedAnswerCount: number;

  /** Whether answer labels are currently displayed on the map. */
  showAnswers: boolean;

  /** Whether there are still unselected map features. */
  canSelectAll: boolean;

  /** Removes one feature from the current manual selection. */
  onRemoveFeature: (featureId: string) => void;

  /** Selects every available geographic feature. */
  onSelectAll: () => void;

  /** Clears every selected geographic feature. */
  onDeselectAll: () => void;

  /** Toggles answer labels during manual feature selection. */
  onToggleShowAnswers: () => void;

  /**
   * Requests that the containing Groups panel scroll newly expanded manual
   * selection content into view.
   */
  onRequestPanelScroll: () => void;
};

/**
 * Displays the current manual selection and controls for modifying it.
 *
 * @param props - Selection state, answer-display state, and selection callbacks.
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
   * This lets the component distinguish a newly added selection from a
   * deselection, since only additions should automatically scroll downward.
   */
  const previousSelectionCountRef = useRef(selectionItems.length);

  /** Whether at least one geographic feature is currently selected. */
  const hasSelectedFeatures = selectionItems.length > 0;

  /**
   * Keeps newly selected features visible in both the inner selected-feature
   * list and the surrounding Groups panel.
   *
   * The outer panel only needs to move while the selected-feature container is
   * still growing. Once the container reaches its maximum height, additional
   * selections are handled entirely by its own scrolling.
   *
   * Removing features does not force either scroll position to change.
   */
  useEffect(() => {
    const previousCount = previousSelectionCountRef.current;

    const currentCount = selectionItems.length;

    previousSelectionCountRef.current = currentCount;

    /*
     * Only newly added selections should trigger automatic scrolling.
     */
    if (currentCount <= previousCount) {
      return;
    }

    const selectionList = selectionListRef.current;

    if (!selectionList) {
      return;
    }

    /*
     * Determine whether the selected-feature container is still growing.
     *
     * Once scrollHeight exceeds clientHeight, the container has reached its
     * maximum visible height and its own scrollbar handles later additions.
     */
    const isListOverflowing =
      selectionList.scrollHeight > selectionList.clientHeight;

    selectionList.scrollTo({
      top: selectionList.scrollHeight,
      behavior: "smooth",
    });

    /*
     * While the inner container is still expanding vertically, keep the outer
     * Groups panel following that additional height as well.
     */
    if (!isListOverflowing) {
      onRequestPanelScroll();
    }
  }, [selectionItems.length, onRequestPanelScroll]);

  return (
    <>
      {/* Selection summary */}
      <div className="mt-2 flex items-center justify-between text-xs font-medium text-gray-500">
        <span>{selectionItems.length} Features</span>

        <span>{selectedAnswerCount} Answers</span>
      </div>

      {/* Show Answers toggle */}
      <button
        type="button"
        onClick={onToggleShowAnswers}
        className="mt-3 flex w-full items-center justify-between text-left"
      >
        <span className="text-sm font-medium text-gray-700">
          Show Answers
        </span>

        {/* Toggle indicator */}
        <span
          className={[
            "h-4 w-4 shrink-0 rounded-full border-2 transition",

            showAnswers
              ? "border-gray-900 bg-gray-900"
              : "border-gray-400 bg-transparent",
          ].join(" ")}
        />
      </button>

      {/* Selected-feature list */}
      <div
        ref={selectionListRef}
        className="panel-scrollbar mt-3 max-h-48 space-y-1 overflow-y-auto overscroll-contain rounded-lg border border-gray-300/60 bg-transparent p-2 transition-colors hover:bg-gray-100/60"
      >
        {!hasSelectedFeatures ? (
          /* Empty selection */
          <p className="px-1 py-2 text-center text-xs text-gray-500">
            Select features on the map.
          </p>
        ) : (
          /* Selected geographic features */
          selectionItems.map((item) => (
            <div
              key={item.featureId}
              className="flex items-center justify-between gap-2 rounded-md px-2 py-1.5 text-sm text-gray-700 transition hover:bg-white"
            >
              {/* Quiz answers represented by the feature */}
              <span className="min-w-0 flex-1 truncate">
                {item.answers.length > 0
                  ? item.answers.join(", ")
                  : "Unknown Answer"}
              </span>

              {/* Remove selected feature */}
              <button
                type="button"
                onClick={() => onRemoveFeature(item.featureId)}
                title="Remove feature"
                aria-label="Remove selected feature"
                className="flex h-5 w-5 shrink-0 items-center justify-center rounded text-sm font-bold text-gray-400 transition hover:bg-gray-300 hover:text-gray-900"
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
            "text-xs font-medium underline transition",

            canSelectAll
              ? "text-gray-600 hover:text-gray-900"
              : "text-gray-400",
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
            "text-xs font-medium underline transition",

            hasSelectedFeatures
              ? "text-gray-600 hover:text-gray-900"
              : "text-gray-400",
          ].join(" ")}
        >
          Deselect All
        </button>
      </div>
    </>
  );
}
