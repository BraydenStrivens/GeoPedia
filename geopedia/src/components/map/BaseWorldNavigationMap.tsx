/**
 * Renders GeoPedia's Home world-country navigation map.
 *
 * This component is intentionally specific to the application's world
 * navigation experience. It is responsible for:
 *
 * - Creating the shared MapLibre map infrastructure.
 * - Displaying all countries from the world-country geometry source.
 * - Styling countries according to whether they currently contain quizzes.
 * - Displaying a diagonal hatch over countries without quizzes.
 * - Showing country information beside the pointer.
 * - Showing `No quizzes available` for unavailable countries.
 * - Applying hover highlighting only to navigable countries.
 * - Navigating to available country pages when selected.
 *
 * Feature and town quiz behavior is implemented separately by their dedicated
 * quiz-map components and interaction systems.
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
   * Quiz availability is resolved before this client-side map renders so
   * MapLibre interactions can perform synchronous availability checks.
   */
  countryIdsWithQuizzes: string[];
};

/**
 * Renders GeoPedia's interactive world-country navigation map.
 *
 * Available countries can be hovered and selected to navigate to their country
 * pages. Countries without quizzes remain visible but are visually marked as
 * unavailable and do not navigate when selected.
 *
 * @param props - World map configuration and available-country IDs.
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

  /*
   * The world-navigation map always displays geographic shading and borders.
   * Its style intentionally contains no base-map place labels.
   *
   * These stable refs satisfy the shared map lifecycle API without introducing
   * user-configurable quiz display settings into this component.
   */
  const showShadingRef = useRef(true);
  const showBordersRef = useRef(true);
  const showLabelsRef = useRef(false);

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
   * Creates the MapLibre instance and shared geographic source/layers used by
   * the world-navigation map.
   */
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
      {/* Floating country information displayed beside the pointer. */}
      {hoveredCountry && (
        <div
          className={[
            "pointer-events-none",
            "absolute",
            "z-10",
            "rounded-md",
            "bg-background-1",
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
