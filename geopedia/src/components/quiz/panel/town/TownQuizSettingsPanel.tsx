/**
 * Displays and updates settings belonging specifically to GeoPedia town quizzes.
 *
 * The panel presents town quiz mode, optional question-language selection, and
 * contextual base-map label visibility using GeoPedia's shared quiz-settings
 * controls.
 *
 * The Language selector appears only when the active town subset contains at
 * least one distinct native settlement name. Town answer labels themselves are
 * controlled by quiz mode rather than the Show Labels setting.
 *
 * Settings state is owned by the parent component. This component only
 * presents controls and reports complete updated `TownQuizSettings` values
 * through `onChange`, leaving persistence to `useTownQuizSettings`.
 */

"use client";

import QuizSettingsSegmentedControl from "@/components/quiz/panel/shared/QuizSettingsSegmentedControl";
import QuizSettingsToggleRow from "@/components/quiz/panel/shared/QuizSettingsToggleRow";
import type {
  TownQuizQuestionLanguage,
  TownQuizSettings,
} from "@/types/townQuizSettings";

/**
 * Props required by the town quiz settings panel.
 */
type TownQuizSettingsPanelProps = {
  /** Current persisted town quiz settings. */
  settings: TownQuizSettings;

  /**
   * Whether at least one town in the active quiz subset has a distinct native
   * name.
   *
   * The Language setting is hidden when changing it could not affect any
   * question.
   */
  hasNativeNames: boolean;

  /** Called whenever the user changes a town quiz setting. */
  onChange: (settings: TownQuizSettings) => void;
};

/**
 * Quiz modes available through the town quiz mode selector.
 */
const TOWN_QUIZ_MODE_OPTIONS = [
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
    value: TownQuizSettings["mode"];
    label: string;
  },
  {
    value: TownQuizSettings["mode"];
    label: string;
  },
];

/**
 * Question languages available when the active town subset contains at least
 * one distinct native settlement name.
 */
const TOWN_QUIZ_LANGUAGE_OPTIONS = [
  {
    value: "english",
    label: "English",
  },
  {
    value: "native",
    label: "Native",
  },
] satisfies readonly [
  {
    value: TownQuizQuestionLanguage;
    label: string;
  },
  {
    value: TownQuizQuestionLanguage;
    label: string;
  },
];

/**
 * Displays controls for changing a town quiz's behavior and appearance.
 *
 * @param props - Town quiz settings panel properties.
 * @param props.settings - Current persisted town quiz settings.
 * @param props.hasNativeNames - Whether Native language selection can affect
 * the active town subset.
 * @param props.onChange - Callback receiving complete updated town settings.
 * @returns The town quiz settings panel.
 */
export default function TownQuizSettingsPanel({
  settings,
  hasNativeNames,
  onChange,
}: TownQuizSettingsPanelProps) {
  /**
   * Updates only the town quiz presentation mode while preserving every other
   * town setting.
   *
   * @param mode - Newly selected town quiz mode.
   */
  function changeTownQuizMode(mode: TownQuizSettings["mode"]): void {
    onChange({
      ...settings,
      mode,
    });
  }

  /**
   * Updates only the town quiz question language while preserving every other
   * town setting.
   *
   * @param questionLanguage - Newly selected question language.
   */
  function changeTownQuizQuestionLanguage(
    questionLanguage: TownQuizQuestionLanguage,
  ): void {
    onChange({
      ...settings,
      questionLanguage,
    });
  }

  /**
   * Toggles contextual base-map labels while preserving every other town quiz
   * setting.
   */
  function toggleTownQuizLabels(): void {
    onChange({
      ...settings,
      showLabels: !settings.showLabels,
    });
  }

  return (
    <div className="w-80 rounded-xl bg-background-1/95 p-4 shadow-lg backdrop-blur-md">
      {/* Panel title */}
      <h2 className="mb-4 text-base font-bold text-text">
        Quiz Settings
      </h2>

      {/* Town quiz answer-label mode */}
      <div className="mb-5">
        <QuizSettingsSegmentedControl
          label="Mode"
          description="Normal mode shows the towns included in the quiz on the map. Hard mode hides those town labels and markers until the town is revealed after an answer."
          options={TOWN_QUIZ_MODE_OPTIONS}
          value={settings.mode}
          onChange={changeTownQuizMode}
        />
      </div>

      {/*
       * Question language is useful only when the active town subset contains
       * at least one native name that differs from its English name.
       */}
      {hasNativeNames && (
        <div className="mb-5">
          <QuizSettingsSegmentedControl
            label="Language"
            description="Controls the names used for quiz questions. English uses each town's preferred English or international name, while Native uses the town's native name when one is available. This setting does not change the names displayed on the map."
            options={TOWN_QUIZ_LANGUAGE_OPTIONS}
            value={settings.questionLanguage}
            onChange={changeTownQuizQuestionLanguage}
          />
        </div>
      )}

      {/* Contextual base-map labels */}
      <div className="space-y-3">
        <QuizSettingsToggleRow
          label="Show Labels"
          description="Shows contextual labels from the base map, such as country, state, road, river, and other geographic names. This setting does not show or hide the towns included in the quiz."
          isEnabled={settings.showLabels}
          onToggle={toggleTownQuizLabels}
        />
      </div>
    </div>
  );
}
