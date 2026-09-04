/**
 * Displays the searchable list of values available for a property-based feature
 * quiz group.
 *
 * This component is presentation-focused. The parent owns the selected-value
 * set and is responsible for applying selection changes to the map and quiz.
 *
 * A search field is shown only when the grouping property exposes more than
 * ten selectable values.
 */

"use client";

import { useMemo, useState } from "react";

import type { QuizGroupingOption } from "@/quiz/groupings/feature/utils/getGroupingOptions";

/**
 * Props required by the property-group option list.
 */
type PropertyGroupOptionsProps = {
  /** Raw grouping-property values currently selected by the user. */
  selectedValues: ReadonlySet<string>;

  /** All selectable values discovered from the current GeoJSON property. */
  groupingOptions: QuizGroupingOption[];

  /**
   * Whether property-group mutations are temporarily blocked because another
   * grouping workflow currently owns interaction.
   */
  isInteractionBlocked: boolean;

  /** Toggles one raw grouping-property value. */
  onToggleValue: (value: string) => void;

  /** Clears every currently selected grouping-property value. */
  onDeselectAll: () => void;
};

/**
 * Displays selection counts, optional search, and selectable property values.
 *
 * @param props - Property-group option state and interaction callbacks.
 * @param props.selectedValues - Currently selected raw property values.
 * @param props.groupingOptions - Available grouping values and display labels.
 * @param props.onToggleValue - Callback for toggling one grouping value.
 * @param props.onDeselectAll - Callback for clearing the complete selection.
 * @returns Searchable property-group option controls.
 */
export default function PropertyGroupOptions({
  selectedValues,
  groupingOptions,
  isInteractionBlocked,
  onToggleValue,
  onDeselectAll,
}: PropertyGroupOptionsProps) {
  /** Search text used to filter visible property-group options. */
  const [searchQuery, setSearchQuery] = useState("");

  /**
   * Whether the grouping-property option count is large enough to justify a
   * search field.
   */
  const shouldShowSearch = groupingOptions.length > 10;

  /**
   * Property-group options matching the current search text.
   *
   * Matching is case-insensitive and checks the user-facing label rather than
   * the raw GeoJSON property value.
   */
  const visibleGroupingOptions = useMemo(() => {
    const normalizedQuery = searchQuery.trim().toLowerCase();

    if (!normalizedQuery) {
      return groupingOptions;
    }

    return groupingOptions.filter((groupingOption) =>
      groupingOption.label.toLowerCase().includes(normalizedQuery),
    );
  }, [groupingOptions, searchQuery]);

  /** Whether at least one property value is currently selected. */
  const hasSelectedValues = selectedValues.size > 0;

  return (
    <>
      {/* Selection information */}
      <div className="mb-2 flex items-center justify-between">
        {/* Selected / total count */}
        <p className="text-xs font-medium text-text-secondary">
          {selectedValues.size} / {groupingOptions.length}
        </p>

        {/* Deselect all property values */}
        <button
          type="button"
          disabled={isInteractionBlocked && !hasSelectedValues}
          onClick={onDeselectAll}
          className={[
            "text-xs font-medium underline transition",
            hasSelectedValues && !isInteractionBlocked
              ? "text-text-secondary hover:text-text"
              : "cursor-default text-disabled-text",
          ].join(" ")}
        >
          Deselect All
        </button>
      </div>

      {/* Property-group search */}
      {shouldShowSearch && (
        <div className="mb-2">
          <input
            type="search"
            value={searchQuery}
            onChange={(event) => setSearchQuery(event.target.value)}
            placeholder="Search groups..."
            disabled={isInteractionBlocked}
            className="w-full rounded-lg border border-border bg-background-1 px-3 py-2 text-sm text-text outline-none transition focus:border-focus"
          />
        </div>
      )}

      {/* Scrollable property values */}
      <div className="panel-scrollbar mt-2 max-h-64 space-y-2 overflow-y-auto overscroll-contain rounded-lg border border-border bg-transparent px-2 py-2 transition-colors hover:bg-background-2/60">
        {visibleGroupingOptions.length === 0 ? (
          /* No matching property values */
          <p className="px-2 py-3 text-center text-xs text-text-secondary">
            No matching groups
          </p>
        ) : (
          /* Filtered property-value list */
          visibleGroupingOptions.map(({ value, label }) => {
            const isSelected = selectedValues.has(value);

            return (
              <label
                key={value}
                className={[
                  "flex items-center gap-2 text-sm text-text",
                  isInteractionBlocked
                    ? "cursor-not-allowed opacity-50"
                    : "cursor-pointer",
                ].join(" ")}
              >
                {/* Property-value checkbox */}
                <input
                  type="checkbox"
                  checked={isSelected}
                  disabled={isInteractionBlocked}
                  onChange={() => onToggleValue(value)}
                  className="h-4 w-4 cursor-pointer"
                />

                {/* Property-value display label */}
                <span>{label}</span>
              </label>
            );
          })
        )}
      </div>
    </>
  );
}
