"use client";

/**
 * Displays and updates the settings for a single quiz.
 *
 * The panel contains:
 *
 * - A three-position mode selector
 * - Boolean quiz settings shown as circular toggles
 *
 * Settings state is owned by the parent component and passed in through
 * props so persistence remains handled by useQuizSettings.
 */

import type { QuizMode, QuizSettings } from "@/types/quizSettings";

type QuizSettingsPanelProps = {
  settings: QuizSettings;

  onChange: (settings: QuizSettings) => void;
};

const modes: {
  value: QuizMode;
  label: string;
}[] = [
  {
    value: "normal",
    label: "Normal",
  },
  {
    value: "hard",
    label: "Hard",
  },
  {
    value: "show-answers",
    label: "Show Answers",
  },
];

type BooleanSettingKey =
  | "recycleMissedAnswers"
  | "showShading"
  | "showBorders"
  | "showBaseMapLabels"
  | "showIncorrectSelection";

const booleanSettings: {
  key: BooleanSettingKey;
  label: string;
}[] = [
  {
    key: "recycleMissedAnswers",
    label: "Recycle Missed Answers",
  },
  {
    key: "showShading",
    label: "Shading",
  },
  {
    key: "showBorders",
    label: "Borders",
  },
  {
    key: "showBaseMapLabels",
    label: "Labels",
  },
  {
    key: "showIncorrectSelection",
    label: "Show Incorrect Selection",
  },
];

/**
 * Returns the horizontal position of the selected-mode background.
 */
function getModePosition(mode: QuizMode) {
  switch (mode) {
    case "normal":
      return "translateX(0%)";

    case "hard":
      return "translateX(100%)";

    case "show-answers":
      return "translateX(200%)";
  }
}

export default function QuizSettingsPanel({
  settings,
  onChange,
}: QuizSettingsPanelProps) {
  function setMode(mode: QuizMode) {
    onChange({
      ...settings,
      mode,
    });
  }

  function toggleSetting(key: BooleanSettingKey) {
    onChange({
      ...settings,
      [key]: !settings[key],
    });
  }

  return (
    <div className="w-80 rounded-xl bg-white/95 p-4 shadow-lg backdrop-blur-md">
      <h2 className="mb-4 text-base font-bold text-gray-900">
        Quiz Settings
      </h2>

      {/* Quiz mode */}
      <div className="mb-5">
        <div className="mb-2 text-sm font-semibold text-gray-700">
          Mode
        </div>

        <div className="relative grid grid-cols-3 rounded-lg bg-gray-200 p-1">
          {/* Sliding selected-mode background */}
          <div
            className="absolute bottom-1 left-1 top-1 w-[calc((100%-0.5rem)/3)] rounded-md bg-white shadow-sm transition-transform duration-200 ease-out"
            style={{
              transform: getModePosition(settings.mode),
            }}
          />

          {modes.map((mode) => (
            <button
              key={mode.value}
              type="button"
              onClick={() => setMode(mode.value)}
              className="relative z-10 px-2 py-1.5 text-xs font-semibold text-gray-700 transition-colors"
            >
              {mode.label}
            </button>
          ))}
        </div>
      </div>

      {/* Boolean settings */}
      <div className="space-y-3">
        {booleanSettings.map(({ key, label }) => {
          const enabled = settings[key];

          return (
            <button
              key={key}
              type="button"
              onClick={() => toggleSetting(key)}
              className="flex w-full items-center justify-between gap-4 text-left"
            >
              <span className="text-sm font-medium text-gray-700">
                {label}
              </span>

              <span
                className={[
                  "h-4 w-4 shrink-0 rounded-full border-2 transition",
                  enabled
                    ? "border-gray-900 bg-gray-900"
                    : "border-gray-400 bg-transparent",
                ].join(" ")}
              />
            </button>
          );
        })}
      </div>
    </div>
  );
}
