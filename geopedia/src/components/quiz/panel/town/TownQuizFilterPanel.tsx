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
 * Numeric town counts are applied explicitly. Editing the custom count does not
 * alter the active quiz until the player selects Apply or presses Enter.
 *
 * This component owns only temporary custom-input state. The active town count
 * itself remains owned by the hydrated town quiz client so the map labels and
 * quiz engine always consume the same filtered town collection.
 */

"use client";

import { useMemo, useState } from "react";

import { TOWN_QUIZ_PRESET_COUNTS } from "@/quiz/groupings/town/townPopulationGroups";

/**
 * Props required by the town quiz Filter panel.
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
};

/**
 * Props required by one preset town-count button.
 */
type TownCountPresetButtonProps = {
  /** Population-ranked town count represented by the preset. */
  count: number;

  /** Whether this preset is currently applied. */
  isSelected: boolean;

  /** Called when the preset should become active. */
  onSelect: () => void;
};

/**
 * Displays the checkbox-style selection indicator used by town-count presets.
 *
 * @param props - Selection-indicator properties.
 * @param props.isSelected - Whether the associated preset is active.
 * @returns The preset selection indicator.
 */
function TownCountSelectionIndicator({
  isSelected,
}: {
  isSelected: boolean;
}) {
  return (
    <span
      aria-hidden="true"
      className={[
        "flex h-4 w-4 shrink-0 items-center justify-center rounded border",
        "text-[10px] font-bold transition-colors",
        isSelected
          ? "border-selected-control bg-selected-control text-button-text"
          : "border-border-strong bg-surface",
      ].join(" ")}
    >
      {isSelected ? "✓" : ""}
    </span>
  );
}

/**
 * Displays one selectable population-ranked town-count preset.
 *
 * Selected presets use GeoPedia's soft selected surface so the active count is
 * clearly distinguished without giving an entire list row the visual weight
 * of a primary action button.
 *
 * @param props - Preset-button properties.
 * @param props.count - Number of towns represented by the preset.
 * @param props.isSelected - Whether this preset is currently active.
 * @param props.onSelect - Callback for applying the preset.
 * @returns One town-count preset row.
 */
function TownCountPresetButton({
  count,
  isSelected,
  onSelect,
}: TownCountPresetButtonProps) {
  return (
    <button
      type="button"
      onClick={onSelect}
      aria-pressed={isSelected}
      className={[
        "flex w-full items-center gap-3 rounded-lg border px-3 py-2",
        "text-left text-sm font-medium transition-colors",
        "focus-visible:outline-none focus-visible:ring-2",
        "focus-visible:ring-focus",
        isSelected
          ? [
              "border-selected-surface-border",
              "bg-selected-surface text-selected-surface-text",
              "hover:bg-selected-surface-hover",
            ].join(" ")
          : [
              "border-transparent bg-transparent text-text",
              "hover:border-brand-muted hover:bg-brand-soft",
            ].join(" "),
      ].join(" ")}
    >
      <TownCountSelectionIndicator isSelected={isSelected} />

      <span>Top {count}</span>
    </button>
  );
}

/**
 * Displays the town-count Filter panel.
 *
 * @param props - Town Filter panel properties.
 * @param props.availableTownCount - Number of towns in the complete dataset.
 * @param props.activeTownCount - Currently applied population-ranked count.
 * @param props.onUseFullQuiz - Callback for restoring the complete dataset.
 * @param props.onApplyTownCount - Callback for applying a numeric town count.
 * @returns The town quiz Filter panel.
 */
export default function TownQuizFilterPanel({
  availableTownCount,
  activeTownCount,
  onUseFullQuiz,
  onApplyTownCount,
}: TownQuizFilterPanelProps) {
  /**
   * Custom town count currently typed by the player.
   *
   * This is intentionally local state. The active town quiz changes only after
   * the value is explicitly applied.
   */
  const [customTownCountInput, setCustomTownCountInput] = useState(
    String(activeTownCount),
  );

  /**
   * Preset counts available for the current country's generated dataset.
   *
   * A country with 63 towns therefore exposes 10, 25, and 50 while omitting
   * the unavailable 100-town preset.
   *
   * Counts equal to the complete dataset size are also omitted because they
   * would duplicate Full Quiz.
   */
  const availablePresetCounts = useMemo(
    () =>
      TOWN_QUIZ_PRESET_COUNTS.filter(
        (count) => count < availableTownCount,
      ),
    [availableTownCount],
  );

  /**
   * Parsed custom town count.
   *
   * `null` indicates that the current input is not a valid safe integer.
   */
  const parsedCustomTownCount = useMemo(() => {
    const trimmedInput = customTownCountInput.trim();

    if (!/^\d+$/.test(trimmedInput)) {
      return null;
    }

    const value = Number(trimmedInput);

    if (!Number.isSafeInteger(value)) {
      return null;
    }

    return value;
  }, [customTownCountInput]);

  /**
   * Whether the current custom input represents a valid and meaningful change.
   */
  const canApplyCustomTownCount =
    parsedCustomTownCount !== null &&
    parsedCustomTownCount >= 1 &&
    parsedCustomTownCount <= availableTownCount &&
    parsedCustomTownCount !== activeTownCount;

  /** Whether the complete generated town dataset is currently active. */
  const isFullQuizActive = activeTownCount === availableTownCount;

  /**
   * Restores the complete generated town dataset and synchronizes the custom
   * input with the resulting active count.
   */
  function useFullTownQuiz(): void {
    setCustomTownCountInput(String(availableTownCount));

    onUseFullQuiz();
  }

  /**
   * Applies one population-ranked preset and synchronizes the custom input.
   *
   * @param count - Preset town count that should become active.
   */
  function applyTownCountPreset(count: number): void {
    setCustomTownCountInput(String(count));

    onApplyTownCount(count);
  }

  /**
   * Applies the custom town count after validation.
   */
  function applyCustomTownCount(): void {
    if (!canApplyCustomTownCount || parsedCustomTownCount === null) {
      return;
    }

    /*
     * Normalize the accepted input so values such as "050" become "50".
     */
    setCustomTownCountInput(String(parsedCustomTownCount));

    onApplyTownCount(parsedCustomTownCount);
  }

  /**
   * Allows Enter to behave like selecting Apply without making every text
   * change immediately alter the town quiz.
   *
   * @param event - Keyboard event originating from the custom-count input.
   */
  function handleCustomTownCountKeyDown(
    event: React.KeyboardEvent<HTMLInputElement>,
  ): void {
    if (event.key !== "Enter") {
      return;
    }

    applyCustomTownCount();
  }

  return (
    <div
      className="
        w-72 rounded-xl border border-border
        bg-surface p-4 shadow-lg
      "
    >
      {/* Panel heading */}
      <div className="mb-4 border-b border-brand-muted pb-3">
        <h2 className="text-lg font-bold text-text">Filter Towns</h2>

        <p className="mt-0.5 text-sm text-text-secondary">
          {availableTownCount.toLocaleString()} towns available
        </p>
      </div>

      {/* Restore every available town */}
      <button
        type="button"
        onClick={useFullTownQuiz}
        disabled={isFullQuizActive}
        className={[
          "mb-4 w-full rounded-lg border px-4 py-2",
          "text-sm font-semibold transition-colors",
          "focus-visible:outline-none focus-visible:ring-2",
          "focus-visible:ring-focus",
          isFullQuizActive
            ? [
                "cursor-default border-border",
                "bg-disabled text-disabled-text",
              ].join(" ")
            : [
                "border-brand bg-button text-button-text",
                "hover:border-brand-hover-strong hover:bg-button-hover",
              ].join(" "),
        ].join(" ")}
      >
        Use Full Quiz
      </button>

      {/* Population-ranked preset counts */}
      {availablePresetCounts.length > 0 && (
        <div className="mb-5">
          <div className="mb-2 text-sm font-semibold text-text">
            Town count
          </div>

          <div className="space-y-1">
            {availablePresetCounts.map((count) => (
              <TownCountPresetButton
                key={count}
                count={count}
                isSelected={activeTownCount === count}
                onSelect={() => applyTownCountPreset(count)}
              />
            ))}
          </div>
        </div>
      )}

      {/* Arbitrary population-ranked town count */}
      <div>
        <label
          htmlFor="town-quiz-custom-count"
          className="mb-2 block text-sm font-semibold text-text"
        >
          Custom town count
        </label>

        <div className="flex gap-2">
          <input
            id="town-quiz-custom-count"
            type="text"
            inputMode="numeric"
            value={customTownCountInput}
            onChange={(event) => {
              setCustomTownCountInput(event.target.value);
            }}
            onKeyDown={handleCustomTownCountKeyDown}
            className="
              min-w-0 flex-1 rounded-lg
              border border-border bg-surface
              px-3 py-2 text-sm text-text
              outline-none transition-colors
              hover:border-border-strong
              focus:border-focus focus:ring-1 focus:ring-focus
            "
          />

          <button
            type="button"
            onClick={applyCustomTownCount}
            disabled={!canApplyCustomTownCount}
            className={[
              "rounded-lg border px-4 py-2",
              "text-sm font-semibold transition-colors",
              "focus-visible:outline-none focus-visible:ring-2",
              "focus-visible:ring-focus",
              canApplyCustomTownCount
                ? [
                    "border-brand bg-button text-button-text",
                    "hover:border-brand-hover-strong hover:bg-button-hover",
                  ].join(" ")
                : [
                    "cursor-default border-border",
                    "bg-disabled text-disabled-text",
                  ].join(" "),
            ].join(" ")}
          >
            Apply
          </button>
        </div>

        <p className="mt-1 text-xs text-text-secondary">
          Enter a number from 1 to{" "}
          {availableTownCount.toLocaleString()}.
        </p>
      </div>
    </div>
  );
}
