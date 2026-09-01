/**
 * Renders GeoPedia's home world-country navigation map.
 *
 * This component is intentionally specific to the application's base world
 * navigation experience. It is responsible for:
 *
 * - Creating the shared MapLibre map infrastructure through `useMap`.
 * - Displaying all countries from the world-country geometry source.
 * - Styling countries according to whether they currently contain quizzes.
 * - Displaying a diagonal hatch over countries without quizzes.
 * - Showing country names beside the pointer.
 * - Showing `No quizzes available` for unavailable countries.
 * - Applying hover highlighting only to navigable countries.
 * - Navigating to available country pages when selected.
 *
 * Quiz behavior belongs exclusively to `QuizMap`.
 */

"use client";

import "maplibre-gl/dist/maplibre-gl.css";

import * as maplibregl from "maplibre-gl";
import { useRouter } from "next/navigation";
import { useCallback, useMemo, useRef, useState } from "react";

import { useFeatureQuizMap } from "@/maps/hooks/feature/useFeatureQuizMap";
import {
  type HoveredNavigationCountry,
  useWorldNavigationInteractions,
} from "@/maps/hooks/useWorldNavigationInteractions";
import type { MapConfig } from "@/maps/types";

maplibregl.setWorkerUrl("/maplibre-gl-worker.mjs");

/**
 * Props required by the home world-navigation map.
 */
type BaseWorldNavigationMapProps = {
  /** World-country map configuration used by the navigation map. */
  mapConfig: MapConfig;

  /**
   * Country IDs containing at least one available feature or town quiz.
   *
   * Quiz availability is resolved by the server before this client-side map
   * renders so MapLibre interactions can perform synchronous availability
   * checks.
   */
  countryIdsWithQuizzes: string[];
};

/**
 * Renders the application's base world-country navigation experience.
 *
 * @param props - World map configuration.
 * @returns Interactive world navigation map.
 */
export default function BaseWorldNavigationMap({
  mapConfig,
  countryIdsWithQuizzes,
}: BaseWorldNavigationMapProps) {
  const router = useRouter();

  /** Provides constant-time quiz availability checks for MapLibre interactions. */
  const countryQuizIds = useMemo(
    () =>
      new Set(
        countryIdsWithQuizzes.map((countryId) =>
          countryId.toLowerCase(),
        ),
      ),
    [countryIdsWithQuizzes],
  );

  /** DOM element into which MapLibre creates its map. */
  const mapContainerRef = useRef<HTMLDivElement>(null);

  /** Country information displayed beside the pointer while hovering. */
  const [hoveredCountry, setHoveredCountry] =
    useState<HoveredNavigationCountry | null>(null);

  /*
   * The world navigation map always displays its geographic shading and borders.
   * Its style contains no base-map place labels.
   *
   * These stable refs satisfy the generic map lifecycle API without introducing
   * quiz display settings into this component.
   */
  const showShadingRef = useRef(true);
  const showBordersRef = useRef(true);
  const showLabelsRef = useRef(false);

  /** Provides stable Next.js navigation behavior to the MapLibre click handler. */
  const navigateToCountry = useCallback(
    (countryId: string) => {
      router.push(`/${countryId}`);
    },
    [router],
  );

  /** Creates the generic MapLibre map and geographic source/layers. */
  const { mapRef, isMapReady } = useFeatureQuizMap({
    containerRef: mapContainerRef,

    mapConfig,

    showShadingRef,
    showBordersRef,
    showLabelsRef,
  });

  /**
   * Adds world-navigation-specific availability styling, hover behavior, and
   * country navigation.
   */
  useWorldNavigationInteractions({
    mapRef,
    isMapReady,

    labelProperty: mapConfig.hover?.labelProperty ?? "name",
    countryIdsWithQuizzes: countryQuizIds,

    navigateToCountry,
    setHoveredCountry,
  });

  return (
    <div className="relative h-full w-full">
      {/* Floating country label displayed beside the pointer. */}
      {hoveredCountry && (
        <div
          className="
            pointer-events-none
            absolute
            z-10
            rounded-md
            bg-white
            px-3
            py-2
            shadow-md
          "
          style={{
            left: hoveredCountry.x + 12,
            top: hoveredCountry.y + 12,
          }}
        >
          <div className="font-medium text-black">
            {hoveredCountry.name}
          </div>

          {!hoveredCountry.hasQuizzes && (
            <div className="mt-0.5 text-sm text-gray-500">
              No quizzes available
            </div>
          )}
        </div>
      )}

      {/* MapLibre map container */}
      <div ref={mapContainerRef} className="h-full w-full" />
    </div>
  );
}
