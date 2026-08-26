/**
 * Displays the searchable list of values available for a property-based quiz
 * group.
 *
 * This component is presentation-focused. The parent owns the selected-value
 * set and is responsible for applying changes to the map and quiz.
 */

"use client";

import { useMemo, useState } from "react";

import type { QuizGroupingOption } from "@/quiz/groupings/utils/getGroupingOptions";

/**
 * Props required by the property-group option list.
 */
type PropertyGroupOptionsProps = {
  /** Raw property values currently selected by the user. */
  selectedValues: ReadonlySet<string>;

  /** All selectable values discovered from the current GeoJSON property. */
  groupingOptions: QuizGroupingOption[];

  /** Whether property-group controls are currently disabled. */
  isDisabled: boolean;

  /** Toggles one raw property value. */
  onToggleValue: (value: string) => void;

  /** Clears every currently selected property value. */
  onDeselectAll: () => void;
};

/**
 * Displays selection counts, search controls, and selectable property values.
 *
 * @param props - Available options, current selection, and selection callbacks.
 * @returns Searchable property-group option controls.
 */
export default function PropertyGroupOptions({
  selectedValues,
  groupingOptions,
  isDisabled,
  onToggleValue,
  onDeselectAll,
}: PropertyGroupOptionsProps) {
  /** Search text used to filter visible property-group options. */
  const [searchQuery, setSearchQuery] = useState("");

  /**
   * The search box is only displayed if the number of property-group
   * options exceeds 10.
   */
  const showSearchBox: boolean = groupingOptions.length > 10;

  /**
   * Property-group options matching the current search text.
   *
   * Matching is case-insensitive and checks the user-facing label rather than
   * the raw GeoJSON value.
   */
  const filteredGroupingOptions = useMemo(() => {
    const normalizedQuery = searchQuery.trim().toLowerCase();

    if (!normalizedQuery) {
      return groupingOptions;
    }

    return groupingOptions.filter((option) =>
      option.label.toLowerCase().includes(normalizedQuery),
    );
  }, [groupingOptions, searchQuery]);

  return (
    <>
      {/* Selection information */}
      <div className="mb-2 flex items-center justify-between">
        {/* Selected / total count */}
        <p className="text-xs font-medium text-gray-500">
          {selectedValues.size} / {groupingOptions.length}
        </p>

        {/* Deselect all property values */}
        <button
          type="button"
          disabled={isDisabled || selectedValues.size === 0}
          onClick={onDeselectAll}
          className={[
            "text-xs font-medium underline transition",

            isDisabled || selectedValues.size === 0
              ? "text-gray-400"
              : "text-gray-600 hover:text-gray-900",
          ].join(" ")}
        >
          Deselect All
        </button>
      </div>

      {/* Property-group search */}
      {showSearchBox && (
        <div className="mb-2">
          <input
            type="search"
            value={searchQuery}
            onChange={(event) => setSearchQuery(event.target.value)}
            placeholder="Search groups..."
            disabled={isDisabled}
            className="w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-gray-800 outline-none transition focus:border-gray-500"
          />
        </div>
      )}

      {/* Scrollable property values */}
      <div className="panel-scrollbar mt-2 max-h-64 space-y-2 overflow-y-auto overscroll-contain rounded-lg border border-gray-300/60 bg-transparent px-2 py-2 transition-colors hover:bg-gray-100/60">
        {filteredGroupingOptions.length === 0 ? (
          /* No matching property values */
          <p className="px-2 py-3 text-center text-xs text-gray-500">
            No matching groups
          </p>
        ) : (
          /* Filtered property-value list */
          filteredGroupingOptions.map(({ value, label }) => {
            const isSelected = selectedValues.has(value);

            return (
              <label
                key={value}
                className="flex cursor-pointer items-center gap-2 text-sm text-gray-700"
              >
                {/* Property-value checkbox */}
                <input
                  type="checkbox"
                  checked={isSelected}
                  disabled={isDisabled}
                  onChange={() => onToggleValue(value)}
                  className="h-4 w-4"
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
