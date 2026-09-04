/**
 * Renders the interactive geographic map used by GeoPedia town quizzes.
 *
 * Town quizzes are answered by clicking arbitrary geographic coordinates rather
 * than selecting predefined GeoJSON features. This component therefore owns
 * the town-specific MapLibre surface, forwards raw map clicks to the town quiz
 * runtime, and synchronizes GeoPedia-controlled town labels and result
 * visualization.
 *
 * MapTiler's own settlement labels are suppressed by the town-map
 * infrastructure so GeoPedia can fully control which quiz towns are visible.
 * Normal mode displays towns belonging to the currently active quiz set, while
 * Hard mode hides those custom town labels until quiz feedback reveals them.
 *
 * This component remains focused on map presentation and interaction. Town
 * filtering, question progression, scoring logic, and quiz lifecycle state are
 * managed outside the map and supplied through props.
 */

"use client";

import type { MapMouseEvent } from "maplibre-gl";
import { useCallback, useEffect, useRef } from "react";

import { useTownQuizLabels } from "@/maps/hooks/town/useTownQuizLabels";
import { useTownQuizMap } from "@/maps/hooks/town/useTownQuizMap";
import { useTownQuizResult } from "@/maps/hooks/town/useTownQuizResult";
import type { TownQuizGuessResult } from "@/quiz/hooks/useTownQuiz";
import type { TownCountryConfig } from "@/quiz/town/townCountryConfigs";
import type { GeographicCoordinate } from "@/quiz/town/townScoring";
import type { TownQuizTown } from "@/types/quiz";
import type { TownQuizSettings } from "@/types/townQuizSettings";

/**
 * Props required by GeoPedia's town quiz map.
 */
type TownQuizMapProps = {
  /** Country-specific camera and geographic scoring configuration. */
  townConfig: TownCountryConfig;

  /** Towns currently included in the active quiz/filter. */
  towns: TownQuizTown[];

  /** Persisted settings controlling the town quiz map. */
  settings: TownQuizSettings;

  /**
   * Result of the most recently answered town question.
   *
   * `undefined` indicates that no question has yet produced result feedback.
   */
  lastResult: TownQuizGuessResult | undefined;

  /** Called whenever the user submits a map coordinate as their answer. */
  onGuess: (guess: GeographicCoordinate) => void;

  /** Whether map clicks should currently submit town guesses. */
  isGuessingEnabled: boolean;
};

/**
 * Renders the MapLibre surface used by a GeoPedia town quiz.
 *
 * The component creates the country-specific town map, synchronizes quiz-town
 * labels and previous-answer result visualization, and converts enabled map
 * clicks into the geographic-coordinate shape expected by the town quiz
 * engine.
 *
 * @param props - Town map configuration, quiz towns, settings, result state,
 * and guess callback.
 * @returns Interactive town quiz map.
 */
export default function TownQuizMap({
  townConfig,
  towns,
  settings,
  lastResult,
  onGuess,
  isGuessingEnabled,
}: TownQuizMapProps) {
  /** DOM element into which MapLibre creates the town quiz map. */
  const mapContainerRef = useRef<HTMLDivElement | null>(null);

  /**
   * Creates and owns the country-specific MapLibre town quiz map.
   */
  const { mapRef, isMapReady } = useTownQuizMap({
    containerRef: mapContainerRef,

    initialView: townConfig.initialView,

    showLabels: settings.showLabels,
  });

  /**
   * Synchronizes GeoPedia-controlled quiz-town labels with the active town set,
   * quiz mode, and most recent answer result.
   */
  useTownQuizLabels({
    mapRef,
    isMapReady,

    towns,

    mode: settings.mode,

    lastResult,
  });

  /**
   * Synchronizes map visualization for the most recently answered town
   * question.
   */
  useTownQuizResult({
    mapRef,
    isMapReady,

    lastResult,
  });

  /**
   * Converts an enabled MapLibre click into the geographic-coordinate shape
   * consumed by the town quiz engine.
   *
   * Clicks are ignored whenever the parent has disabled guess submission.
   *
   * @param event - MapLibre click event containing the selected longitude and
   * latitude.
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
   * Registers the town-guess click handler once the MapLibre map is ready and
   * removes the listener whenever its dependencies change or the component is
   * unmounted.
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
      {/* MapLibre town quiz map container */}
      <div ref={mapContainerRef} className="h-full w-full" />
    </div>
  );
}
