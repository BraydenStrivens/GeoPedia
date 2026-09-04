/**
 * Displays and updates user-configurable settings for a feature quiz.
 *
 * The panel presents the feature quiz's mode and boolean behavior/display
 * settings using GeoPedia's shared quiz-settings controls. Setting definitions
 * remain feature-specific while the segmented selector and toggle rows are
 * reusable across feature and town quiz settings panels.
 *
 * Settings state is owned by the parent component. This component only
 * presents the controls and reports updated `FeatureQuizSettings` values
 * through `onChange`, leaving persistence to `useFeatureQuizSettings`.
 */

"use client";

import QuizSettingsSegmentedControl from "@/components/quiz/panel/shared/QuizSettingsSegmentedControl";
import QuizSettingsToggleRow from "@/components/quiz/panel/shared/QuizSettingsToggleRow";
import type {
  FeatureQuizSettings,
  QuizMode,
} from "@/types/featureQuizSettings";

/**
 * Props required by the feature quiz settings panel.
 */
type FeatureQuizSettingsPanelProps = {
  /** Current feature quiz settings displayed by the panel. */
  settings: FeatureQuizSettings;

  /** Called whenever the user changes a feature quiz setting. */
  onChange: (settings: FeatureQuizSettings) => void;
};

/**
 * Boolean FeatureQuizSettings properties displayed as toggleable rows.
 */
type BooleanFeatureQuizSettingKey =
  | "recycleMissedAnswers"
  | "showShading"
  | "showBorders"
  | "showLabels"
  | "showIncorrectSelection";

/**
 * Describes one boolean feature quiz setting displayed by the panel.
 */
type BooleanFeatureQuizSettingOption = {
  /** FeatureQuizSettings property changed by the toggle. */
  key: BooleanFeatureQuizSettingKey;

  /** User-facing name of the setting. */
  label: string;

  /** Explanation displayed when the setting's help button is opened. */
  description: string;
};

/**
 * Quiz modes available through the feature quiz mode selector.
 */
const FEATURE_QUIZ_MODE_OPTIONS = [
  {
    value: "normal",
    label: "Normal",
  },
  {
    value: "hard",
    label: "Hard",
  },
] satisfies readonly [
  {
    value: QuizMode;
    label: string;
  },
  {
    value: QuizMode;
    label: string;
  },
];

/**
 * Boolean settings displayed beneath the feature quiz mode selector.
 *
 * The order of this array determines the order in which settings appear.
 * Keeping each setting's label and description together makes the panel easier
 * to maintain as settings are added, removed, or renamed.
 */
const BOOLEAN_FEATURE_QUIZ_SETTING_OPTIONS: BooleanFeatureQuizSettingOption[] =
  [
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
 * Displays controls for changing a feature quiz's behavior and appearance.
 *
 * @param props - Feature quiz settings panel properties.
 * @param props.settings - Current feature quiz settings.
 * @param props.onChange - Callback receiving complete updated settings.
 * @returns The feature quiz settings panel.
 */
export default function FeatureQuizSettingsPanel({
  settings,
  onChange,
}: FeatureQuizSettingsPanelProps) {
  /**
   * Updates the feature quiz presentation mode while preserving all other
   * settings.
   *
   * @param mode - Newly selected feature quiz mode.
   */
  function changeFeatureQuizMode(mode: QuizMode): void {
    onChange({
      ...settings,
      mode,
    });
  }

  /**
   * Toggles one boolean feature quiz setting while preserving all other
   * settings.
   *
   * @param settingKey - Boolean FeatureQuizSettings property to toggle.
   */
  function toggleFeatureQuizSetting(
    settingKey: BooleanFeatureQuizSettingKey,
  ): void {
    onChange({
      ...settings,
      [settingKey]: !settings[settingKey],
    });
  }

  return (
    <div className="w-80 rounded-xl bg-background-1/95 p-4 shadow-lg backdrop-blur-md">
      {/* Panel title */}
      <h2 className="mb-4 text-base font-bold text-text">
        Quiz Settings
      </h2>

      {/* Feature quiz mode selector */}
      <div className="mb-5">
        <QuizSettingsSegmentedControl
          label="Mode"
          description="Normal mode allows standard map feedback and interaction behavior. Hard mode removes quiz assistance intended to make identifying the correct feature more difficult."
          options={FEATURE_QUIZ_MODE_OPTIONS}
          value={settings.mode}
          onChange={changeFeatureQuizMode}
        />
      </div>

      {/* Boolean feature quiz settings */}
      <div className="space-y-3">
        {BOOLEAN_FEATURE_QUIZ_SETTING_OPTIONS.map(
          ({ key, label, description }) => (
            <QuizSettingsToggleRow
              key={key}
              label={label}
              isEnabled={settings[key]}
              description={description}
              onToggle={() => toggleFeatureQuizSetting(key)}
            />
          ),
        )}
      </div>
    </div>
  );
}
