/**
 * Renders the interactive geographic map used by GeoPedia town quizzes.
 *
 * Unlike feature quizzes, town quizzes are answered by clicking arbitrary
 * geographic coordinates rather than selecting predefined GeoJSON polygons.
 * This component therefore owns only the town-specific map surface and exposes
 * raw MapLibre click coordinates to the town quiz engine.
 *
 * Guess scoring, question progression, and result visualization are kept
 * outside this component so the map remains focused on rendering and geographic
 * input.
 */

"use client";

import type { MapMouseEvent } from "maplibre-gl";
import { useCallback, useEffect, useRef } from "react";

import { useTownQuizMap } from "@/maps/hooks/town/useTownQuizMap";
import type { TownCountryConfig } from "@/quiz/town/townCountryConfigs";
import { GeographicCoordinate } from "@/quiz/town/townScoring";

type TownQuizMapProps = {
  /** Country-specific geographic configuration for the town quiz. */
  townConfig: TownCountryConfig;

  /** Called whenever the user selects a geographic location on the map. */
  onGuess: (guess: GeographicCoordinate) => void;

  /** Determines whether map clicks should currently submit guesses. */
  isGuessingEnabled: boolean;
};

/**
 * Displays the town quiz map and converts MapLibre click events into geographic
 * guesses.
 *
 * @param props - Town quiz map configuration and guess callback.
 * @returns Interactive MapLibre town quiz surface.
 */
export default function TownQuizMap({
  townConfig,
  onGuess,
  isGuessingEnabled,
}: TownQuizMapProps) {
  const mapContainerRef = useRef<HTMLDivElement | null>(null);

  const { mapRef, isMapReady } = useTownQuizMap({
    containerRef: mapContainerRef,
    initialView: townConfig.initialView,
  });

  /**
   * Converts a MapLibre click into the coordinate representation consumed by
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

  useEffect(() => {
    const map = mapRef.current;

    if (!isMapReady || !map) {
      return;
    }

    map.on("click", handleMapClick);

    return () => {
      map.off("click", handleMapClick);
    };
  });

  return (
    <div className="relative h-full w-full">
      <div ref={mapContainerRef} className="h-full w-full" />
    </div>
  );
}
