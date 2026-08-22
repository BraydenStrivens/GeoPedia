"use client";

/**
 * Client-side wrapper for a quiz map.
 *
 * This component owns the saved settings for a specific quiz and derives
 * runtime map behavior from those settings before rendering the map.
 */

import { useState } from "react";

import Map from "@/components/Map";
import type { MapClickBehavior, MapConfig } from "@/maps/types";
import { useQuizSettings } from "@/quiz/useQuizSettings";
import type { Quiz } from "@/types/quiz";

import QuizSettingsPanel from "./QuizSettingsPanel";

type QuizMapClientProps = {
  countryId: string;
  quiz: Quiz;
  mapConfig: MapConfig;
};

export default function QuizMapClient({
  countryId,
  quiz,
  mapConfig,
}: QuizMapClientProps) {
  const { settings, setSettings } = useQuizSettings(countryId, quiz.id);
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);

  /*
   * Show Answers mode is informational rather than interactive, so map
   * features cannot submit quiz answers while that mode is active.
   */
  const clickBehavior: MapClickBehavior =
    settings.mode === "show-answers" ? "none" : "quiz";

  return (
    <div className="relative h-full w-full">
      <Map
        mapConfig={mapConfig}
        quiz={quiz}
        clickBehavior={clickBehavior}
      />

      <div className="absolute right-3 top-3 z-30 flex flex-col items-end">
        <button
          type="button"
          onClick={() => setIsSettingsOpen((previous) => !previous)}
          title="Quiz settings"
          className={[
            "flex h-10 w-10 items-center justify-center rounded-lg",
            "border border-white text-white shadow-sm backdrop-blur-md",
            "transition-all duration-200",
            isSettingsOpen
              ? "bg-white text-black hover:bg-white/40"
              : "bg-white/30 text-gray-800 hover:bg-white/70",
          ].join(" ")}
        >
          <svg
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.8"
            className="h-5 w-5 text-black"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M9.594 3.94c.09-.542.56-.94 1.11-.94h2.592c.55 0 1.02.398 1.11.94l.213 1.279c.063.379.313.696.645.889.09.052.18.107.268.164.325.21.72.275 1.082.139l1.223-.46a1.125 1.125 0 0 1 1.37.49l1.296 2.244a1.125 1.125 0 0 1-.26 1.431l-1.003.827a1.125 1.125 0 0 0-.38.95v.31c0 .374.137.735.38.95l1.003.827c.424.35.534.956.26 1.431l-1.296 2.244a1.125 1.125 0 0 1-1.37.49l-1.223-.46a1.125 1.125 0 0 0-1.082.139c-.088.057-.178.112-.268.164a1.125 1.125 0 0 0-.645.889l-.213 1.279c-.09.542-.56.94-1.11.94h-2.592c-.55 0-1.02-.398-1.11-.94l-.213-1.279a1.125 1.125 0 0 0-.645-.889 8.09 8.09 0 0 1-.268-.164 1.125 1.125 0 0 0-1.082-.139l-1.223.46a1.125 1.125 0 0 1-1.37-.49L3.447 15.3a1.125 1.125 0 0 1 .26-1.431l1.003-.827c.243-.2.38-.576.38-.95v-.31c0-.374-.137-.735-.38-.95l-1.003-.827a1.125 1.125 0 0 1-.26-1.431L4.743 6.33a1.125 1.125 0 0 1 1.37-.49l1.223.46c.362.136.757.071 1.082-.139.088-.057.178-.112.268-.164a1.125 1.125 0 0 0 .645-.889l.213-1.279Z"
            />

            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M15 12a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z"
            />
          </svg>
        </button>
        {isSettingsOpen && (
          <div className="mt-2">
            <QuizSettingsPanel
              settings={settings}
              onChange={setSettings}
            />
          </div>
        )}
      </div>
    </div>
  );
}
