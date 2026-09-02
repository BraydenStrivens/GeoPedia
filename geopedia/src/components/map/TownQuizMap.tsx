/**
 * Renders the interactive geographic map used by GeoPedia town quizzes.
 *
 * Town quizzes are answered by clicking arbitrary geographic coordinates rather
 * than selecting predefined GeoJSON polygons. This component therefore owns the
 * town-specific map surface, forwards raw MapLibre click coordinates to the quiz
 * runtime, and synchronizes GeoPedia-controlled town labels.
 *
 * MapTiler's own settlement labels are always suppressed for town quizzes.
 * Normal mode renders only towns belonging to the currently active quiz set,
 * while Hard mode hides those custom labels.
 *
 * Guess scoring, question progression, filtering, and result visualization
 * remain outside the map component.
 */

"use client";

import type { MapMouseEvent } from "maplibre-gl";
import { useCallback, useEffect, useRef } from "react";

import type { TownQuizMode } from "@/components/quiz/controls/town/TownQuizModeControl";
import { useTownQuizLabels } from "@/maps/hooks/town/useTownQuizLabels";
import { useTownQuizMap } from "@/maps/hooks/town/useTownQuizMap";
import { useTownQuizResult } from "@/maps/hooks/town/useTownQuizResult";
import { TownQuizGuessResult } from "@/quiz/hooks/useTownQuiz";
import type { TownCountryConfig } from "@/quiz/town/townCountryConfigs";
import type { GeographicCoordinate } from "@/quiz/town/townScoring";
import type { TownQuizTown } from "@/types/quiz";

/**
 * Props required by the town quiz map.
 */
type TownQuizMapProps = {
  /** Country-specific camera and geographic scoring configuration. */
  townConfig: TownCountryConfig;

  /** Towns currently included in the active quiz/filter. */
  towns: TownQuizTown[];

  /** Current learner-friendly or recall-only display mode. */
  mode: TownQuizMode;

  /**
   * Object containing data about the last question and the user's answer
   * or `undefined` if no previous question has been answered.
   */
  lastResult: TownQuizGuessResult | undefined;

  /** Called whenever the user submits a map coordinate as their answer. */
  onGuess: (guess: GeographicCoordinate) => void;

  /** Whether map clicks should currently submit town guesses. */
  isGuessingEnabled: boolean;
};

/**
 * Renders the shared MapLibre town quiz surface.
 */
export default function TownQuizMap({
  townConfig,
  towns,
  mode,
  lastResult,
  onGuess,
  isGuessingEnabled,
}: TownQuizMapProps) {
  /** DOM element into which MapLibre creates the map. */
  const mapContainerRef = useRef<HTMLDivElement | null>(null);

  /** Creates and owns the country-specific town map. */
  const { mapRef, isMapReady } = useTownQuizMap({
    containerRef: mapContainerRef,

    initialView: townConfig.initialView,
  });

  /** Ensures only GeoPedia-controlled quiz-town labels are available. */
  useTownQuizLabels({
    mapRef,
    isMapReady,
    towns,
    mode,
    lastResult,
  });

  useTownQuizResult({
    mapRef,
    isMapReady,
    lastResult,
  });

  /**
   * Converts a MapLibre click into the geographic-coordinate shape consumed by
   * the town quiz engine.
   */
  const handleMapClick = useCallback(
    (event: MapMouseEvent): void => {
      if (!isGuessingEnabled) {
        return;
      }

      onGuess({
        longitude: event.lngLat.lng,
        latitude: event.lngLat.lat,
      });
    },
    [isGuessingEnabled, onGuess],
  );

  /**
   * Registers the town-guess click handler while preserving one listener across
   * each React render.
   */
  useEffect(() => {
    const map = mapRef.current;

    if (!isMapReady || !map) {
      return;
    }

    map.on("click", handleMapClick);

    return () => {
      map.off("click", handleMapClick);
    };
  }, [isMapReady, mapRef, handleMapClick]);

  return (
    <div className="relative h-full w-full">
      <div ref={mapContainerRef} className="h-full w-full" />
    </div>
  );
}
