/**
 * Renders the town-count filtering panel used by GeoPedia town quizzes.
 *
 * Town quizzes do not use the geographic grouping system used by feature
 * quizzes. Instead, the player chooses how many population-ranked towns should
 * participate in the quiz.
 *
 * The panel supports:
 *
 * - Restoring the complete generated town dataset.
 * - Preset population-ranked counts of 10, 25, 50, and 100 when available.
 * - An arbitrary custom count between 1 and the country's available town count.
 *
 * Numeric town counts are applied explicitly. Custom input therefore does not
 * alter the quiz while the player is typing.
 *
 * This component owns only temporary input state. The active town count itself
 * is owned by the town quiz client so the map labels and quiz engine always
 * consume the same filtered town collection.
 */

"use client";

import { useMemo, useState } from "react";

import { TOWN_QUIZ_PRESET_COUNTS } from "@/quiz/groupings/town/townPopulationGroups";

/**
 * Props required by the town Filter panel.
 */
type TownQuizFilterPanelProps = {
  /** Number of towns available in the country's complete generated dataset. */
  availableTownCount: number;

  /**
   * Currently applied town count.
   *
   * When this equals `availableTownCount`, Full Quiz is active.
   */
  activeTownCount: number;

  /** Applies the complete generated town dataset. */
  onUseFullQuiz: () => void;

  /** Applies a population-ranked town count. */
  onApplyTownCount: (count: number) => void;

  /** Closes the floating panel. */
  onClose: () => void;
};

/**
 * Shared styling used by selectable preset rows.
 */
const PRESET_BUTTON_CLASSES = [
  "flex",
  "w-full",
  "items-center",
  "gap-3",
  "rounded-lg",
  "px-3",
  "py-2",
  "text-left",
  "text-sm",
  "font-medium",
  "transition",
  "hover:bg-gray-300",
].join(" ");

/**
 * Displays the town-count Filter panel.
 */
export default function TownQuizFilterPanel({
  availableTownCount,
  activeTownCount,
  onUseFullQuiz,
  onApplyTownCount,
  onClose,
}: TownQuizFilterPanelProps) {
  /**
   * Custom count currently typed by the user.
   *
   * It intentionally does not update when every keystroke occurs outside this
   * local state. The active quiz changes only after Apply is pressed.
   */
  const [customCountInput, setCustomCountInput] = useState(
    String(activeTownCount),
  );

  /**
   * Preset counts that actually exist for the current country.
   *
   * A country with 63 towns therefore exposes 10, 25, and 50 while omitting
   * the unavailable 100-town preset.
   */
  const availablePresetCounts = useMemo(
    () =>
      TOWN_QUIZ_PRESET_COUNTS.filter(
        (count) => count < availableTownCount,
      ),
    [availableTownCount],
  );

  /**
   * Parsed custom count, or `null` when the input is not a valid integer.
   */
  const parsedCustomCount = useMemo(() => {
    if (!/^\d+$/.test(customCountInput.trim())) {
      return null;
    }

    const value = Number(customCountInput);

    if (!Number.isSafeInteger(value)) {
      return null;
    }

    return value;
  }, [customCountInput]);

  /**
   * Whether Apply would produce a valid and meaningful filter change.
   */
  const canApplyCustomCount =
    parsedCustomCount !== null &&
    parsedCustomCount >= 1 &&
    parsedCustomCount <= availableTownCount &&
    parsedCustomCount !== activeTownCount;

  /**
   * Applies the custom town count after validation.
   */
  function applyCustomCount(): void {
    if (!canApplyCustomCount || parsedCustomCount === null) {
      return;
    }

    /*
     * Normalize the input before applying it. This keeps values such as "050"
     * displayed consistently as "50" after they are accepted.
     */
    setCustomCountInput(String(parsedCustomCount));

    onApplyTownCount(parsedCustomCount);
  }

  /**
   * Allows Enter to behave like pressing Apply without making every text change
   * immediately alter the quiz.
   */
  function handleCustomCountKeyDown(
    event: React.KeyboardEvent<HTMLInputElement>,
  ): void {
    if (event.key !== "Enter") {
      return;
    }

    applyCustomCount();
  }

  const isFullQuiz = activeTownCount === availableTownCount;

  return (
    <div className="w-72 rounded-xl border border-gray-300 bg-white p-4 shadow-lg">
      {/* Panel heading. */}
      <div className="mb-4 flex items-center justify-between">
        <div>
          <h2 className="text-lg font-bold text-gray-900">Filter</h2>

          <p className="text-sm text-gray-600">
            {availableTownCount.toLocaleString()} towns available
          </p>
        </div>

        <button
          type="button"
          aria-label="Close town filter"
          onClick={onClose}
          className="flex h-7 w-7 items-center justify-center rounded-md text-lg text-gray-500 transition hover:bg-gray-300 hover:text-gray-900"
        >
          ×
        </button>
      </div>
      {/* Restore every available town. */}
      <button
        type="button"
        onClick={() => {
          setCustomCountInput(String(availableTownCount));

          onUseFullQuiz();
        }}
        disabled={isFullQuiz}
        className={[
          "mb-4",
          "w-full",
          "rounded-lg",
          "px-4",
          "py-2",
          "text-sm",
          "font-semibold",
          "transition",

          isFullQuiz
            ? "cursor-default bg-gray-300 text-gray-500"
            : "bg-gray-900 text-white hover:bg-gray-700",
        ].join(" ")}
      >
        Use Full Quiz
      </button>
      {/* Population-ranked preset counts. */}
      {availablePresetCounts.length > 0 && (
        <div className="mb-5">
          <div className="mb-2 text-sm font-semibold text-gray-900">
            Town count
          </div>

          <div className="space-y-1">
            {availablePresetCounts.map((count) => {
              const isSelected = activeTownCount === count;

              return (
                <button
                  key={count}
                  type="button"
                  onClick={() => {
                    setCustomCountInput(String(count));

                    onApplyTownCount(count);
                  }}
                  className={[
                    PRESET_BUTTON_CLASSES,

                    isSelected
                      ? "bg-gray-300 text-gray-900"
                      : "text-gray-700",
                  ].join(" ")}
                >
                  {/* Checkbox-style active indicator. */}
                  <span
                    aria-hidden="true"
                    className={[
                      "flex",
                      "h-4",
                      "w-4",
                      "shrink-0",
                      "items-center",
                      "justify-center",
                      "rounded",
                      "border",
                      "text-[10px]",
                      "font-bold",

                      isSelected
                        ? "border-gray-900 bg-gray-900 text-white"
                        : "border-gray-400 bg-white",
                    ].join(" ")}
                  >
                    {isSelected ? "✓" : ""}
                  </span>

                  <span>Top {count}</span>
                </button>
              );
            })}
          </div>
        </div>
      )}
      {/* Arbitrary population-ranked count. */}
      <div>
        <label
          htmlFor="town-quiz-custom-count"
          className="mb-2 block text-sm font-semibold text-gray-900"
        >
          Custom town count
        </label>

        <div className="flex gap-2">
          <input
            id="town-quiz-custom-count"
            type="text"
            inputMode="numeric"
            value={customCountInput}
            onChange={(event) => {
              setCustomCountInput(event.target.value);
            }}
            onKeyDown={handleCustomCountKeyDown}
            className="min-w-0 flex-1 rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 outline-none transition focus:border-gray-500"
          />

          <button
            type="button"
            onClick={applyCustomCount}
            disabled={!canApplyCustomCount}
            className={[
              "rounded-lg",
              "px-4",
              "py-2",
              "text-sm",
              "font-semibold",
              "transition",

              canApplyCustomCount
                ? "bg-gray-900 text-white hover:bg-gray-700"
                : "cursor-default bg-gray-300 text-gray-500",
            ].join(" ")}
          >
            Apply
          </button>
        </div>

        <p className="mt-1 text-xs text-gray-500">
          Enter a number from 1 to{" "}
          {availableTownCount.toLocaleString()}.
        </p>
      </div>
    </div>
  );
}
