/**
 * Loads and exposes the GeoJSON data required by GeoPedia's quiz-grouping
 * system.
 *
 * MapLibre loads the same GeoJSON independently for rendering. This hook
 * loads the dataset for React-side grouping logic so GeoPedia can:
 *
 * - Discover available property-group options.
 * - Resolve active groups into feature IDs.
 * - Resolve active groups into eligible quiz answers.
 *
 * The browser can cache the GeoJSON request, so this does not necessarily
 * result in a second network download.
 */

"use client";

import type {
  FeatureCollection,
  GeoJsonProperties,
  Geometry,
} from "geojson";
import { abort } from "process";
import { useEffect, useState } from "react";

/**
 * GeoJSON feature collection used by the grouping system.
 */
export type QuizGroupingFeatureCollection = FeatureCollection<
  Geometry,
  GeoJsonProperties
>;

/**
 * Result returned by `useQuizGroupingData`.
 */
type UseQuizGroupingDataResult = {
  /** Loaded GeoJSON dataset, or null before loading completes. */
  featureCollection: QuizGroupingFeatureCollection | null;

  /** Whether the grouping GeoJSON request is currently in progress. */
  isLoading: boolean;

  /** Error encountered while loading the grouping data, or null on success. */
  error: Error | null;
};

/**
 * Loads a quiz map's complete GeoJSON dataset for React-side grouping logic.
 *
 * The request automatically reruns when the GeoJSON URL changes. Previous
 * requests are aborted during cleanup so stale responses cannot overwrite
 * data belonging to a newer map.
 *
 * @param geojsonUrl - URL of the GeoJSON dataset used by the quiz map.
 * @returns Loaded feature collection together with loading and error state.
 */
export function useQuizGroupingData(
  geojsonUrl: string,
): UseQuizGroupingDataResult {
  const [featureCollection, setFeatureCollection] =
    useState<QuizGroupingFeatureCollection | null>(null);

  const [isLoading, setIsLoading] = useState(true);

  const [error, setError] = useState<Error | null>(null);

  /**
   * Loads the GeoJSON whenever the map's source URL changes.
   */
  useEffect(() => {
    const abortController = new AbortController();

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
        if (!abortController.signal.aborted) {
          setIsLoading(false);
        }
      }
    }

    loadGeoJson();

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
