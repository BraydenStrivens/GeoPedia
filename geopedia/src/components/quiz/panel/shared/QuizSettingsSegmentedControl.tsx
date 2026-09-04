/**
 * Displays a reusable two-option segmented control for quiz settings panels.
 *
 * The control renders a labeled pair of horizontally aligned options with a
 * sliding selected background. An optional contextual description can be
 * exposed through GeoPedia's standard help button.
 *
 * Feature and town quiz settings panels use this component for settings such
 * as quiz mode and town question language.
 *
 * Selection state is owned by the parent component. Contextual-help visibility
 * is local presentation state owned by this component.
 */

"use client";

import { useState } from "react";

/**
 * Describes one option displayed by a quiz settings segmented control.
 */
export type QuizSettingsSegmentedOption<TValue extends string> = {
  /** Stable value represented by the option. */
  value: TValue;

  /** User-facing text displayed inside the option. */
  label: string;
};

/**
 * Props required by the reusable quiz settings segmented control.
 */
type QuizSettingsSegmentedControlProps<TValue extends string> = {
  /** User-facing label displayed above the segmented control. */
  label: string;

  /**
   * Optional explanation displayed through the contextual help control.
   *
   * When omitted, no help button is displayed.
   */
  description?: string;

  /** Two options displayed by the control. */
  options: readonly [
    QuizSettingsSegmentedOption<TValue>,
    QuizSettingsSegmentedOption<TValue>,
  ];

  /** Currently selected option value. */
  value: TValue;

  /** Called when the user selects a different option. */
  onChange: (value: TValue) => void;
};

/**
 * Displays a reusable two-position segmented settings selector.
 *
 * @param props - Segmented-control properties.
 * @param props.label - Label displayed above the control.
 * @param props.description - Optional contextual help description.
 * @param props.options - Two selectable options.
 * @param props.value - Currently selected value.
 * @param props.onChange - Callback receiving the newly selected value.
 * @returns The segmented settings control.
 */
export default function QuizSettingsSegmentedControl<
  TValue extends string,
>({
  label,
  description,
  options,
  value,
  onChange,
}: QuizSettingsSegmentedControlProps<TValue>) {
  /**
   * Whether this control's contextual help description is currently visible.
   */
  const [isHelpOpen, setIsHelpOpen] = useState(false);

  const selectedOptionIndex = options.findIndex(
    (option) => option.value === value,
  );

  return (
    <div>
      {/* Setting label and optional contextual help */}
      <div className="mb-2 flex items-center gap-1.5">
        <span className="text-sm font-semibold text-text">
          {label}
        </span>

        {description && (
          <button
            type="button"
            onClick={() =>
              setIsHelpOpen((currentValue) => !currentValue)
            }
            aria-label={`About ${label}`}
            aria-expanded={isHelpOpen}
            className="flex h-4 w-4 shrink-0 items-center justify-center rounded-full border border-border text-[10px] font-bold leading-none text-text-secondary transition hover:border-border-hover hover:text-text"
          >
            ?
          </button>
        )}
      </div>

      {/* Segmented selector */}
      <div className="relative grid grid-cols-2 rounded-lg bg-background-3 p-1">
        {/* Sliding selected-option background */}
        <div
          aria-hidden="true"
          className="absolute bottom-1 left-1 top-1 w-[calc((100%-0.5rem)/2)] rounded-md bg-background-1 shadow-sm transition-transform duration-200 ease-out"
          style={{
            transform:
              selectedOptionIndex === 1
                ? "translateX(100%)"
                : "translateX(0%)",
          }}
        />

        {/* Selectable options */}
        {options.map((option) => (
          <button
            key={option.value}
            type="button"
            onClick={() => onChange(option.value)}
            aria-pressed={option.value === value}
            className="relative z-10 px-2 py-1.5 text-xs font-semibold text-text transition-colors"
          >
            {option.label}
          </button>
        ))}
      </div>

      {/* Optional contextual help description */}
      {description && isHelpOpen && (
        <div
          className="mt-2 rounded-lg border border-border bg-background-1 p-2.5 text-xs leading-relaxed text-text-secondary shadow-sm"
          role="note"
        >
          {description}
        </div>
      )}
    </div>
  );
}
