/**
 * Connects a quiz page to GeoPedia's reusable map and quiz-settings system.
 *
 * This component:
 *
 * - Delays rendering until the client has hydrated.
 * - Loads and persists settings for the current quiz.
 * - Renders the map with quiz interaction enabled.
 * - Owns the open/closed state of the quiz settings panel.
 * - Displays the settings control above the map.
 *
 * The hydration boundary prevents the map from briefly rendering with default
 * quiz settings before the user's saved localStorage settings are available.
 */

"use client";

import { useState, useSyncExternalStore } from "react";

import Map from "@/components/map/Map";
import QuizSettingsPanel from "@/components/quiz/QuizSettingsPanel";
import type { MapConfig } from "@/maps/types";
import { getGroupingOptions } from "@/quiz/groupings/getGroupingOptions";
import { resolveQuizGroup } from "@/quiz/groupings/resolveQuizGroup";
import { useActiveQuizGroup } from "@/quiz/groupings/useActiveQuizGroup";
import { useQuizGroupingData } from "@/quiz/groupings/useQuizGroupingData";
import { useQuizSettings } from "@/quiz/hooks/useQuizSettings";
import type { Quiz } from "@/types/quiz";

/**
 * Props required to render a client-side quiz map.
 */
type QuizMapClientProps = {
  /** Country containing the quiz. Used to identify its saved settings. */
  countryId: string;

  /** Quiz displayed and controlled by the map. */
  quiz: Quiz;

  /** Geographic map configuration used by the quiz. */
  mapConfig: MapConfig;
};

/**
 * Props required by the quiz settings button.
 */
type QuizSettingsButtonProps = {
  /** Whether the quiz settings panel is currently open. */
  isOpen: boolean;

  /** Opens or closes the quiz settings panel. */
  onClick: () => void;
};

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
 * Button used to open and close the quiz settings panel.
 *
 * @param props - Settings button properties.
 * @param props.isOpen - Whether the settings panel is currently open.
 * @param props.onClick - Callback that toggles the settings panel.
 * @returns The quiz settings button.
 */
function QuizSettingsButton({
  isOpen,
  onClick,
}: QuizSettingsButtonProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      title="Quiz settings"
      aria-label="Quiz settings"
      aria-expanded={isOpen}
      className={[
        "flex h-10 w-10 items-center justify-center rounded-lg",
        "border border-white shadow-sm backdrop-blur-md",
        "text-gray-900 transition-all duration-200",

        isOpen
          ? "bg-white hover:bg-white/50"
          : "bg-white/30 hover:bg-white/70",
      ].join(" ")}
    >
      {/* Settings gear icon */}
      <svg
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.8"
        className="h-5 w-5"
        aria-hidden="true"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          d="M9.594 3.94c.09-.542.56-.94 1.11-.94h2.592c.55 0 1.02.398 1.11.94l.213 1.279c.063.379.313.696.645.889.09.052.18.107.268.164.325.21.72.275 1.082.139l1.223-.46a1.125 1.125 0 0 1 1.37.49l1.296 2.244a1.125 1.125 0 0 1-.26 1.431l-1.003.827a1.125 1.125 0 0 0-.38.95v.31c0 .374.137.735.38.95l1.003.827c.424.35.534.956.26 1.431l-1.296 2.244a1.125 1.125 0 0 1-1.37.49l-1.223-.46a1.125 1.125 0 0 0-1.082.139c-.088.057-.178.112-.268.164a1.125 1.125 0 0 0-.645.889l-.213 1.279c-.09.542-.56.94-1.11.94h-2.592c-.55 0-1.02-.398-1.11-.94l-.213-1.279a1.125 1.125 0 0 0-.645-.889 8.09 8.09 0 0 1-.268-.164 1.125 1.125 0 0 0-1.082-.139l-1.223.46a1.125 1.125 0 0 1-1.37-.49L3.447 15.3a1.125 1.125 0 0 1 .26-1.431l1.003-.827c.243-.2.38-.576.38-.95v-.31c0-.374-.137-.735-.38-.95l-1.003-.827a1.125 1.125 0 0 1-.26-1.431L4.743 6.33a1.125 1.125 0 0 1 1.37-.49l1.223.46c.362.136.757.071 1.082-.139.088-.057.178-.112.268-.164a1.125 1.125 0 0 0 .645-.889l.213-1.279Z"
        />

        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          d="M15 12a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z"
        />
      </svg>
    </button>
  );
}

/**
 * Prevents the quiz map from rendering until React has hydrated on the client.
 *
 * Quiz settings are stored in localStorage, which is unavailable during
 * server rendering. Waiting for hydration ensures the map is first created
 * using the user's saved settings rather than briefly displaying the default
 * settings and then changing immediately afterward.
 *
 * @param props - Quiz map properties forwarded to the hydrated component.
 * @returns An empty map-sized placeholder before hydration, or the hydrated
 * quiz map afterward.
 */
export default function QuizMapClient(props: QuizMapClientProps) {
  const isHydrated = useSyncExternalStore(
    subscribeToHydration,

    // The component is hydrated whenever this snapshot runs in the browser.
    () => true,

    // Server rendering must treat the component as not yet hydrated.
    () => false,
  );

  if (!isHydrated) {
    return <div className="h-full w-full" />;
  }

  return <HydratedQuizMapClient {...props} />;
}

/**
 * Renders the interactive quiz map after client hydration has completed.
 *
 * This component owns the persisted settings for the current quiz and the
 * temporary UI state controlling whether the settings panel is open.
 *
 * Separating this component from `QuizMapClient` ensures `useQuizSettings`
 * does not run until the client-side hydration boundary has been crossed.
 *
 * @param props - Quiz map configuration.
 * @param props.countryId - Country used to identify the quiz's saved settings.
 * @param props.quiz - Quiz connected to the map.
 * @param props.mapConfig - Geographic configuration rendered by the map.
 * @returns The hydrated quiz map and its settings controls.
 */
function HydratedQuizMapClient({
  countryId,
  quiz,
  mapConfig,
}: QuizMapClientProps) {
  /** Persisted settings belonging specifically to this country and quiz. */
  const { settings, setSettings } = useQuizSettings(
    countryId,
    quiz.id,
  );

  /**
   * Loads the quiz's GeoJSON for React-side grouping logic.
   */
  const { featureCollection } = useQuizGroupingData(
    mapConfig.geojsonUrl,
  );

  /**
   * Owns the group currently applied to the quiz and derives its geographic
   * feature and question subsets.
   */
  const {
    activeGroup,
    resolvedGroup,
    activeQuiz,
    applyGroup,
    // useFullQuiz,
  } = useActiveQuizGroup({
    quiz,
    mapConfig,
    featureCollection,
  });

  /**
   * Feature IDs rendered by the map for the active group.
   *
   * Full Quiz uses null so MapLibre removes all grouping filters.
   */
  const activeFeatureIds =
    activeGroup.type === "full"
      ? null
      : Array.from(resolvedGroup?.featureIds ?? []);

  /** -----------------------------------------------------------------------------------------------------
   * Temporary development check for the property-grouping engine.
   *
   * This can be removed once the Groups UI consumes the grouping data.
   */
  if (featureCollection && quiz.grouping?.properties.length) {
    const groupingProperty = quiz.grouping.properties[0];

    const groupingOptions = getGroupingOptions(
      featureCollection,
      groupingProperty,
    );

    const testGroup = {
      type: "property" as const,
      property: groupingProperty.property,
      values: ["MN"],
    };

    const resolvedGroup = resolveQuizGroup(
      featureCollection,
      quiz,
      mapConfig,
      testGroup,
    );

    console.log("Resolved feature IDs:", resolvedGroup.featureIds);

    console.log("Resolved answers:", resolvedGroup.answers);

    console.log("Grouping options:", groupingOptions);
  }
  /** ----------------------------------------------------------------------------------------------------- */

  /** Controls whether the floating quiz settings panel is currently visible. */
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);

  /**
   * Opens the settings panel when closed and closes it when open.
   */
  function toggleSettingsPanel(): void {
    setIsSettingsOpen((wasOpen) => !wasOpen);
  }

  return (
    <div className="relative h-full w-full">
      {/* Interactive quiz map */}
      <Map
        mapConfig={mapConfig}
        quiz={activeQuiz}
        quizSettings={settings}
        clickBehavior="quiz"
        activeFeatureIds={activeFeatureIds}
      />

      {/* Quiz settings controls */}
      <div className="absolute right-3 top-3 z-30 flex flex-col items-end">
        {/* Settings panel toggle */}
        <QuizSettingsButton
          isOpen={isSettingsOpen}
          onClick={toggleSettingsPanel}
        />

        {/* Quiz settings panel */}
        {isSettingsOpen && (
          <div className="mt-2">
            <QuizSettingsPanel
              settings={settings}
              onChange={setSettings}
            />
          </div>
        )}
      </div>
    </div>
  );
}
