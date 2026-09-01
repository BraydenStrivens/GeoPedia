/**
 * Loads and exposes the GeoJSON data required by GeoPedia's quiz-grouping
 * system.
 *
 * MapLibre loads the same GeoJSON independently for rendering. This hook loads
 * the dataset for React-side grouping logic so GeoPedia can:
 *
 * - Discover available property-group options.
 * - Resolve active groups into geographic feature IDs.
 * - Resolve active groups into eligible quiz answers.
 * - Build manual-selection display information.
 *
 * The browser may satisfy both MapLibre and React requests from its cache, so
 * this does not necessarily result in downloading the GeoJSON twice.
 */

"use client";

import type {
  FeatureCollection,
  GeoJsonProperties,
  Geometry,
} from "geojson";
import { useEffect, useState } from "react";

/**
 * GeoJSON feature collection consumed by the quiz-grouping system.
 */
export type QuizGroupingFeatureCollection = FeatureCollection<
  Geometry,
  GeoJsonProperties
>;

/**
 * Result returned by `useQuizGroupingData`.
 */
type UseQuizGroupingDataResult = {
  /** Loaded GeoJSON dataset, or `null` before loading completes. */
  featureCollection: QuizGroupingFeatureCollection | null;

  /** Whether the grouping GeoJSON request is currently in progress. */
  isLoading: boolean;

  /** Error encountered while loading the grouping data, or `null` on success. */
  error: Error | null;
};

/**
 * Loads a quiz map's complete GeoJSON dataset for React-side grouping logic.
 *
 * The request automatically restarts whenever the GeoJSON URL changes.
 * Previous requests are aborted during cleanup so a stale response cannot
 * overwrite data belonging to a newer map.
 *
 * @param geojsonUrl - URL of the GeoJSON dataset used by the quiz map.
 * @returns Loaded feature collection together with loading and error state.
 */
export function useQuizGroupingData(
  geojsonUrl: string,
): UseQuizGroupingDataResult {
  /** GeoJSON currently available to React-side grouping logic. */
  const [featureCollection, setFeatureCollection] =
    useState<QuizGroupingFeatureCollection | null>(null);

  /** Whether the current GeoJSON request is still in progress. */
  const [isLoading, setIsLoading] = useState(true);

  /** Most recent GeoJSON loading error, if one occurred. */
  const [error, setError] = useState<Error | null>(null);

  /**
   * Loads the GeoJSON whenever the map source URL changes.
   */
  useEffect(() => {
    const abortController = new AbortController();

    /**
     * Fetches and validates the quiz GeoJSON.
     */
    async function loadGeoJson(): Promise<void> {
      try {
        setIsLoading(true);

        setError(null);

        const response = await fetch(geojsonUrl, {
          signal: abortController.signal,
        });

        if (!response.ok) {
          throw new Error(
            `Failed to load quiz grouping GeoJSON: ${response.status} ${response.statusText}`,
          );
        }

        const geoJson =
          (await response.json()) as QuizGroupingFeatureCollection;

        /*
         * Perform the minimum structural validation required by the grouping
         * system before exposing the dataset to the rest of the application.
         */
        if (
          geoJson.type !== "FeatureCollection" ||
          !Array.isArray(geoJson.features)
        ) {
          throw new Error(
            "Quiz grouping GeoJSON is not a valid FeatureCollection.",
          );
        }

        setFeatureCollection(geoJson);
      } catch (caughtError) {
        /*
         * Aborted requests are expected during cleanup and should not surface
         * as application errors.
         */
        if (abortController.signal.aborted) {
          return;
        }

        const loadError =
          caughtError instanceof Error
            ? caughtError
            : new Error("Failed to load quiz grouping GeoJSON.");

        console.error(loadError);

        setError(loadError);
        setFeatureCollection(null);
      } finally {
        /*
         * An aborted request belongs to a component instance or URL that is no
         * longer current, so it should not update loading state.
         */
        if (!abortController.signal.aborted) {
          setIsLoading(false);
        }
      }
    }

    void loadGeoJson();

    return () => {
      abortController.abort();
    };
  }, [geojsonUrl]);

  return {
    featureCollection,
    isLoading,
    error,
  };
}
