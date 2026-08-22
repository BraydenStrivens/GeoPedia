"use client";

/**
 * Client-side wrapper for a quiz map.
 *
 * This component owns the saved settings for a specific quiz and derives
 * runtime map behavior from those settings before rendering the map.
 */

import Map from "@/components/Map";
import type { MapClickBehavior, MapConfig } from "@/maps/types";
import { useQuizSettings } from "@/quiz/useQuizSettings";
import type { Quiz } from "@/types/quiz";

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

  console.log("Quiz settings:", countryId, quiz.id, settings);
  /*
   * Show Answers mode is informational rather than interactive, so map
   * features cannot submit quiz answers while that mode is active.
   */
  const clickBehavior: MapClickBehavior =
    settings.mode === "show-answers" ? "none" : "quiz";

  return (
    <Map mapConfig={mapConfig} quiz={quiz} clickBehavior={clickBehavior} />
  );
}
