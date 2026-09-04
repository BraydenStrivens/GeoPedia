/**
 * Provides GeoPedia's client-hydration boundary for interactive quiz maps.
 *
 * Quiz settings and other user-specific quiz state are persisted in
 * localStorage and therefore are unavailable during server rendering. This
 * component waits until React has hydrated in the browser before rendering the
 * feature- or town-specific quiz client.
 *
 * After hydration, the quiz kind determines which dedicated client coordinator
 * receives the resolved quiz and map configuration.
 */

"use client";

import { useSyncExternalStore } from "react";

import HydratedFeatureQuizMapClient from "@/components/quiz/HydratedFeatureQuizMapClient";
import HydratedTownQuizMapClient from "@/components/quiz/HydratedTownQuizMapClient";
import type { MapConfig } from "@/maps/types";
import type { TownCountryConfig } from "@/quiz/town/townCountryConfigs";
import type { FeatureQuiz, TownQuiz } from "@/types/quiz";

/**
 * Props required when rendering a feature-based quiz map.
 *
 * Feature quizzes operate on GeoJSON map features and therefore require a
 * complete `MapConfig` describing their geographic source and presentation.
 */
type FeatureQuizMapClientProps = {
  /** Identifies these props as belonging to a feature quiz. */
  kind: "feature";

  /** Country containing the quiz and its persisted user state. */
  countryId: string;

  /** Feature quiz displayed by the map. */
  quiz: FeatureQuiz;

  /** Geographic map configuration required by the feature quiz. */
  mapConfig: MapConfig;
};

/**
 * Props required when rendering a town-based quiz map.
 *
 * Town quizzes use their country-specific configuration for initial map
 * presentation and geographic scoring rather than a feature `MapConfig`.
 */
type TownQuizMapClientProps = {
  /** Identifies these props as belonging to a town quiz. */
  kind: "town";

  /** Country containing the quiz and its persisted user state. */
  countryId: string;

  /** Town quiz displayed by the map. */
  quiz: TownQuiz;

  /** Country-specific map and scoring configuration. */
  townConfig: TownCountryConfig;
};

/**
 * Props accepted by GeoPedia's shared quiz-map hydration boundary.
 *
 * The discriminated union guarantees that each quiz kind is paired with the
 * configuration required by its corresponding client implementation.
 */
type QuizMapClientProps =
  FeatureQuizMapClientProps | TownQuizMapClientProps;

/**
 * No-op subscription used by `useSyncExternalStore` to detect hydration.
 *
 * The server snapshot returns `false`, while the browser snapshot returns
 * `true`. No external value actually changes, so there is nothing to
 * subscribe to.
 *
 * @returns An empty cleanup function.
 */
function subscribeToHydration(): () => void {
  return () => {};
}

/**
 * Waits for browser hydration before rendering an interactive quiz client.
 *
 * @param props - Resolved quiz and map configuration.
 * @returns A map-sized placeholder before hydration, or the appropriate
 * hydrated quiz client afterward.
 */
export default function QuizMapClient(props: QuizMapClientProps) {
  const isHydrated = useSyncExternalStore(
    subscribeToHydration,

    // Browser snapshot.
    () => true,

    // Server snapshot.
    () => false,
  );

  if (!isHydrated) {
    return <div className="h-full w-full" />;
  }

  if (props.kind === "town") {
    return (
      <HydratedTownQuizMapClient
        countryId={props.countryId}
        quiz={props.quiz}
        townConfig={props.townConfig}
      />
    );
  }

  return (
    <HydratedFeatureQuizMapClient
      countryId={props.countryId}
      quiz={props.quiz}
      mapConfig={props.mapConfig}
    />
  );
}
