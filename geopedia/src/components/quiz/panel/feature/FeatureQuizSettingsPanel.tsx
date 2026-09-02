/**
 * Displays and updates user-configurable settings for a single feature quiz.
 *
 * The panel contains:
 *
 * - A two-position Normal/Hard mode selector.
 * - Toggleable quiz-behavior settings.
 * - Toggleable map-display settings.
 * - Contextual help popups explaining each boolean setting.
 *
 * Settings state is owned by the parent component. This component only
 * presents the controls and reports updated `QuizSettings` values through
 * `onChange`, leaving persistence to `useQuizSettings`.
 */

"use client";

import { useState } from "react";

import type { QuizMode, QuizSettings } from "@/types/quizSettings";

/**
 * Props required by the quiz settings panel.
 */
type FeatureQuizSettingsPanelProps = {
  /** Current settings displayed by the panel. */
  settings: QuizSettings;

  /** Called whenever the user changes a quiz setting. */
  onChange: (settings: QuizSettings) => void;
};

/**
 * Describes one option displayed by the quiz-mode selector.
 */
type FeatureQuizModeOption = {
  /** Quiz mode represented by the option. */
  value: QuizMode;

  /** User-facing text displayed by the option. */
  label: string;
};

/**
 * Boolean QuizSettings properties displayed as toggleable rows.
 */
type BooleanSettingKey =
  | "recycleMissedAnswers"
  | "showShading"
  | "showBorders"
  | "showLabels"
  | "showIncorrectSelection";

/**
 * Describes one boolean setting displayed by the panel.
 */
type BooleanSettingOption = {
  /** QuizSettings property changed by the toggle. */
  key: BooleanSettingKey;

  /** User-facing name of the setting. */
  label: string;

  /** Explanation displayed when the setting's help button is opened. */
  description: string;
};

/**
 * Quiz modes available through the horizontal mode selector.
 */
const quizModeOptions: FeatureQuizModeOption[] = [
  {
    value: "normal",
    label: "Normal",
  },
  {
    value: "hard",
    label: "Hard",
  },
];

/**
 * Boolean settings displayed beneath the quiz-mode selector.
 *
 * The order of this array determines the order in which settings appear in
 * the panel. Keeping each setting's label and description together makes the
 * settings UI easier to maintain as options are added or renamed.
 */
const booleanSettingOptions: BooleanSettingOption[] = [
  {
    key: "recycleMissedAnswers",
    label: "Recycle Missed Answers",
    description:
      "When you answer incorrectly, the question is moved to the end of the queue instead of being completed. You must eventually answer it correctly to finish the quiz.",
  },
  {
    key: "showShading",
    label: "Shading",
    description:
      "Shows the map's default feature shading. Turning this off makes unanswered regions transparent while quiz-result colors can still appear.",
  },
  {
    key: "showBorders",
    label: "Borders",
    description:
      "Shows the borders between quiz features. Turning this off also removes border-revealing hover behavior during a normal quiz.",
  },
  {
    key: "showLabels",
    label: "Labels",
    description:
      "Shows labels from the base map, such as town, road, river, and other place names.",
  },
  {
    key: "showIncorrectSelection",
    label: "Show Incorrect Selection",
    description:
      "When you select the wrong feature, briefly displays the name of the feature you actually clicked.",
  },
];

/**
 * Returns the horizontal translation used by the mode selector's sliding
 * selection background.
 *
 * @param mode - Currently selected quiz mode.
 * @returns CSS transform that positions the selection background beneath the
 * selected option.
 */
function getModeBackgroundTransform(mode: QuizMode): string {
  return mode === "normal" ? "translateX(0%)" : "translateX(100%)";
}

/**
 * Displays controls for changing the current quiz's behavior and appearance.
 *
 * @param props - Quiz settings panel properties.
 * @param props.settings - Current settings displayed by the controls.
 * @param props.onChange - Callback receiving the complete updated settings.
 * @returns The quiz settings panel.
 */
export default function FeatureQuizSettingsPanel({
  settings,
  onChange,
}: FeatureQuizSettingsPanelProps) {
  /**
   * Setting whose contextual help popup is currently visible.
   *
   * `null` means that no help popup is open.
   */
  const [openHelpSetting, setOpenHelpSetting] =
    useState<BooleanSettingKey | null>(null);

  /**
   * Updates the quiz presentation mode while preserving all other settings.
   *
   * @param mode - Newly selected quiz mode.
   */
  function changeQuizMode(mode: QuizMode): void {
    onChange({
      ...settings,
      mode,
    });
  }

  /**
   * Toggles one boolean quiz setting while preserving all other settings.
   *
   * @param settingKey - Boolean QuizSettings property to toggle.
   */
  function toggleBooleanSetting(settingKey: BooleanSettingKey): void {
    onChange({
      ...settings,

      [settingKey]: !settings[settingKey],
    });
  }

  /**
   * Opens or closes the contextual help popup for a setting.
   *
   * Opening another setting automatically closes the previously visible
   * popup.
   *
   * @param settingKey - Setting whose help popup should be toggled.
   */
  function toggleSettingHelp(settingKey: BooleanSettingKey): void {
    setOpenHelpSetting((currentSetting) =>
      currentSetting === settingKey ? null : settingKey,
    );
  }

  return (
    <div className="w-80 rounded-xl bg-white/95 p-4 shadow-lg backdrop-blur-md">
      {/* Panel title */}
      <h2 className="mb-4 text-base font-bold text-gray-900">
        Quiz Settings
      </h2>

      {/* Quiz mode selector */}
      <div className="mb-5">
        <div className="mb-2 text-sm font-semibold text-gray-700">
          Mode
        </div>

        <div className="relative grid grid-cols-2 rounded-lg bg-gray-300 p-1">
          {/* Sliding selected-mode background */}
          <div
            className="absolute bottom-1 left-1 top-1 w-[calc((100%-0.5rem)/2)] rounded-md bg-white shadow-sm transition-transform duration-200 ease-out"
            style={{
              transform: getModeBackgroundTransform(settings.mode),
            }}
          />

          {/* Mode options */}
          {quizModeOptions.map((modeOption) => (
            <button
              key={modeOption.value}
              type="button"
              onClick={() => changeQuizMode(modeOption.value)}
              className="relative z-10 px-2 py-1.5 text-xs font-semibold text-gray-700 transition-colors"
            >
              {modeOption.label}
            </button>
          ))}
        </div>
      </div>

      {/* Boolean quiz settings */}
      <div className="space-y-3">
        {booleanSettingOptions.map(({ key, label, description }) => {
          const isEnabled = settings[key];

          const isHelpOpen = openHelpSetting === key;

          return (
            <div key={key} className="relative">
              {/* Setting row */}
              <div className="flex items-center justify-between gap-4">
                {/* Setting name and help button */}
                <div className="flex items-center gap-1.5">
                  <span className="text-sm font-medium text-gray-700">
                    {label}
                  </span>

                  <button
                    type="button"
                    onClick={() => toggleSettingHelp(key)}
                    aria-label={`About ${label}`}
                    aria-expanded={isHelpOpen}
                    className="flex h-4 w-4 shrink-0 items-center justify-center rounded-full border border-gray-400 text-[10px] font-bold leading-none text-gray-500 transition hover:border-gray-700 hover:text-gray-900"
                  >
                    ?
                  </button>
                </div>

                {/* Setting toggle */}
                <button
                  type="button"
                  onClick={() => toggleBooleanSetting(key)}
                  aria-label={`Toggle ${label}`}
                  aria-pressed={isEnabled}
                  className="shrink-0"
                >
                  <span
                    className={[
                      "block h-4 w-4 rounded-full border-2 transition",

                      isEnabled
                        ? "border-gray-900 bg-gray-900 hover:bg-gray-700"
                        : "border-gray-400 bg-transparent hover:border-gray-600",
                    ].join(" ")}
                  />
                </button>
              </div>

              {/* Setting help popup */}
              {isHelpOpen && (
                <div
                  className="mt-2 rounded-lg border border-gray-200 bg-white p-2.5 text-xs leading-relaxed text-gray-600 shadow-sm"
                  role="note"
                >
                  {description}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
