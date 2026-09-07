/**
 * Renders GeoPedia's Home world-country navigation map.
 *
 * This component is intentionally specific to the application's world
 * navigation experience. It is responsible for:
 *
 * - Creating the Home world-navigation map.
 * - Displaying all countries from the world-country geometry source.
 * - Displaying a legend for GeoGuessr and non-GeoGuessr country shading.
 * - Displaying a diagonal hatch over countries without quizzes.
 * - Showing country information beside the pointer.
 * - Showing `No quizzes available` for unavailable countries.
 * - Applying hover highlighting only to countries with quizzes.
 * - Navigating to available country pages when selected.
 *
 * Base country classification and MapLibre lifecycle behavior are handled by
 * `useWorldNavigationMap`, while quiz availability and runtime interaction
 * behavior are handled by `useWorldNavigationInteractions`.
 */

"use client";

import "maplibre-gl/dist/maplibre-gl.css";

import * as maplibregl from "maplibre-gl";
import { useRouter } from "next/navigation";
import { useCallback, useMemo, useRef, useState } from "react";

import {
  type HoveredNavigationCountry,
  useWorldNavigationInteractions,
} from "@/maps/hooks/useWorldNavigationInteractions";
import { useWorldNavigationMap } from "@/maps/hooks/useWorldNavigationMap";
import type { MapConfig } from "@/maps/types";

maplibregl.setWorkerUrl("/maplibre-gl-worker.mjs");

/**
 * Distance in pixels between the pointer and the floating country information
 * popup.
 */
const COUNTRY_HOVER_POPUP_OFFSET = 12;

/**
 * Props required by the Home world-navigation map.
 */
type BaseWorldNavigationMapProps = {
  /** World-country map configuration used by the navigation map. */
  mapConfig: MapConfig;

  /**
   * Country IDs containing at least one available feature or town quiz.
   *
   * Quiz availability controls navigation, hover highlighting, unavailable
   * hatching, and popup messaging independently from GeoGuessr classification.
   */
  countryIdsWithQuizzes: string[];
};

/**
 * Renders GeoPedia's interactive world-country navigation map.
 *
 * Country base colors indicate whether a country or territory belongs to the
 * GeoGuessr coverage set. Quiz availability separately determines whether the
 * country receives hover highlighting, can be selected, or displays an
 * unavailable hatch.
 *
 * @param props - World map configuration and quiz-enabled country IDs.
 * @returns Interactive Home world-navigation map.
 */
export default function BaseWorldNavigationMap({
  mapConfig,
  countryIdsWithQuizzes,
}: BaseWorldNavigationMapProps) {
  const router = useRouter();

  /**
   * Provides constant-time quiz availability checks for MapLibre interactions.
   *
   * IDs are normalized to lowercase so availability checks remain consistent
   * regardless of the casing used by incoming configuration data.
   */
  const countryQuizIds = useMemo(
    () =>
      new Set(
        countryIdsWithQuizzes.map((countryId) =>
          countryId.toLowerCase(),
        ),
      ),
    [countryIdsWithQuizzes],
  );

  /** DOM element into which MapLibre creates the world-navigation map. */
  const mapContainerRef = useRef<HTMLDivElement>(null);

  /** Country information displayed beside the pointer while hovering. */
  const [hoveredCountry, setHoveredCountry] =
    useState<HoveredNavigationCountry | null>(null);

  /**
   * Provides stable Next.js navigation behavior to the MapLibre click handler.
   *
   * @param countryId - Country route identifier selected on the map.
   */
  const navigateToCountry = useCallback(
    (countryId: string) => {
      router.push(`/${countryId}`);
    },
    [router],
  );

  /**
   * Creates the Home-specific MapLibre instance, loads world-country geometry,
   * and applies GeoGuessr/non-GeoGuessr base classification styling.
   */
  const { mapRef, isMapReady } = useWorldNavigationMap({
    containerRef: mapContainerRef,
    mapConfig,
  });

  /**
   * Adds quiz-availability styling, hover behavior, popup state, cursor
   * behavior, and country navigation.
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
      {/* GeoGuessr coverage legend */}
      <div
        className={[
          "pointer-events-none",
          "absolute right-3 top-3 z-10",
          "rounded-lg border border-border",
          "bg-surface/90 px-3 py-2",
          "shadow-sm backdrop-blur-sm",
        ].join(" ")}
      >
        <div className="flex items-center gap-2 text-xs font-medium text-text-secondary">
          <span className="h-3 w-3 shrink-0 rounded-sm bg-[#bae6fd]" />

          <span>GeoGuessr Countries / Territories</span>
        </div>

        <div className="mt-1.5 flex items-center gap-2 text-xs font-medium text-text-secondary">
          <span className="h-3 w-3 shrink-0 rounded-sm bg-[#cbd5e1]" />

          <span>Other Countries / Territories</span>
        </div>
      </div>

      {/* Floating country information displayed beside the pointer. */}
      {hoveredCountry && (
        <div
          className={[
            "pointer-events-none",
            "absolute",
            "z-10",
            "rounded-md",
            "bg-surface",
            "px-3",
            "py-2",
            "shadow-md",
          ].join(" ")}
          style={{
            left: hoveredCountry.x + COUNTRY_HOVER_POPUP_OFFSET,
            top: hoveredCountry.y + COUNTRY_HOVER_POPUP_OFFSET,
          }}
        >
          {/* Country name */}
          <div className="font-medium text-text">
            {hoveredCountry.name}
          </div>

          {/* Availability message for countries without quizzes */}
          {!hoveredCountry.hasQuizzes && (
            <div className="mt-0.5 text-sm text-text-secondary">
              No quizzes available
            </div>
          )}
        </div>
      )}

      {/* MapLibre world-navigation map container */}
      <div ref={mapContainerRef} className="h-full w-full" />
    </div>
  );
}
