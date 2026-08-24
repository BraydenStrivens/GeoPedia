/**
 * Connects a quiz page to GeoPedia's reusable map, quiz settings, and quiz
 * grouping systems.
 *
 * This component:
 *
 * - Delays rendering until the client has hydrated.
 * - Loads and persists settings for the current quiz.
 * - Loads GeoJSON used by the quiz-grouping system.
 * - Owns the currently active quiz group.
 * - Loads and persists user-created saved groups.
 * - Renders the map with quiz interaction enabled.
 * - Owns the open/closed state of the Settings and Groups panels.
 *
 * The hydration boundary prevents the map from briefly rendering with default
 * quiz settings before the user's saved localStorage values are available.
 */

"use client";

import { useState, useSyncExternalStore } from "react";

import Map from "@/components/map/Map";
import QuizGroupsPanel from "@/components/quiz/groupings/QuizGroupsPanel";
import QuizSettingsPanel from "@/components/quiz/QuizSettingsPanel";
import type { MapConfig } from "@/maps/types";
import type {
  ActiveQuizGroup,
  SavedQuizGroup,
} from "@/quiz/groupings/types";
import { useActiveQuizGroup } from "@/quiz/groupings/useActiveQuizGroup";
import { useQuizGroupingData } from "@/quiz/groupings/useQuizGroupingData";
import { useSavedQuizGroups } from "@/quiz/groupings/useSavedQuizGroups";
import { useQuizSettings } from "@/quiz/hooks/useQuizSettings";
import type { Quiz } from "@/types/quiz";

/**
 * Props required to render a client-side quiz map.
 */
type QuizMapClientProps = {
  /** Country containing the quiz. Used to identify persisted user data. */
  countryId: string;

  /** Quiz displayed and controlled by the map. */
  quiz: Quiz;

  /** Geographic map configuration used by the quiz. */
  mapConfig: MapConfig;
};

/**
 * Props shared by the Settings and Groups panel toggle buttons.
 */
type QuizButtonProps = {
  /** Whether the button's associated panel is currently open. */
  isOpen: boolean;

  /** Opens or closes the associated panel. */
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
 * Returns the shared Tailwind styling used by the Settings and Groups buttons.
 *
 * @param isOpen - Whether the button's associated panel is currently open.
 * @returns Tailwind className string for the button.
 */
function generateButtonStyle(isOpen: boolean): string {
  return [
    "flex h-10 p-3 items-center justify-center rounded-lg",
    "border border-white shadow-sm backdrop-blur-md",
    "text-gray-900 transition-all duration-200",

    isOpen
      ? "bg-white hover:bg-white/50"
      : "bg-white/30 hover:bg-white/70",
  ].join(" ");
}

/**
 * Button used to open and close the quiz Settings panel.
 *
 * @param props - Settings button properties.
 * @param props.isOpen - Whether the Settings panel is currently open.
 * @param props.onClick - Callback that toggles the Settings panel.
 * @returns The quiz Settings button.
 */
function QuizSettingsButton({ isOpen, onClick }: QuizButtonProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      title="Quiz settings"
      aria-label="Quiz settings"
      aria-expanded={isOpen}
      className={generateButtonStyle(isOpen)}
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
 * Button used to open and close the quiz Groups panel.
 *
 * @param props - Groups button properties.
 * @param props.isOpen - Whether the Groups panel is currently open.
 * @param props.onClick - Callback that toggles the Groups panel.
 * @returns The quiz Groups button.
 */
function QuizGroupsButton({ isOpen, onClick }: QuizButtonProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      title="Quiz groups"
      aria-label="Quiz groups"
      aria-expanded={isOpen}
      className={generateButtonStyle(isOpen)}
    >
      Groups
    </button>
  );
}

/**
 * Prevents the quiz map from rendering until React has hydrated on the client.
 *
 * Quiz settings and saved groups are stored in localStorage, which is
 * unavailable during server rendering. Waiting for hydration ensures the map
 * is first created using the user's persisted state.
 *
 * @param props - Quiz map properties forwarded to the hydrated component.
 * @returns An empty map-sized placeholder before hydration, or the hydrated
 * quiz map afterward.
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

  return <HydratedQuizMapClient {...props} />;
}

/**
 * Renders the interactive quiz map after client hydration has completed.
 *
 * This component owns persisted quiz settings, grouping data, saved groups,
 * the currently active group, and the temporary visibility state of the
 * Settings and Groups panels.
 *
 * @param props - Quiz map configuration.
 * @param props.countryId - Country used to identify persisted quiz data.
 * @param props.quiz - Complete quiz definition.
 * @param props.mapConfig - Geographic configuration rendered by the map.
 * @returns The hydrated quiz map and its floating controls.
 */
function HydratedQuizMapClient({
  countryId,
  quiz,
  mapConfig,
}: QuizMapClientProps) {
  /**
   * Persisted settings belonging specifically to this country and quiz.
   */
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
   * ID of the saved group currently applied to the quiz.
   *
   * `null` means Full Quiz or an unsaved temporary group is active.
   */
  const [activeSavedGroupId, setActiveSavedGroupId] = useState<
    string | null
  >(null);

  /**
   * Owns the group currently applied to the quiz and derives its geographic
   * feature and question subsets.
   */
  const {
    activeGroup,
    resolvedGroup,
    activeQuiz,
    applyGroup,
    resetToFullQuiz,
  } = useActiveQuizGroup({
    quiz,
    mapConfig,
    featureCollection,
  });

  /**
   * Loads and persists user-created groups belonging to this quiz.
   *
   * Update and delete will be wired into the Groups panel when edit mode is
   * implemented.
   */
  const { savedGroups, saveGroup, updateGroup, deleteGroup } =
    useSavedQuizGroups(countryId, quiz.id);

  /**
   * Feature IDs rendered by the map for the active group.
   *
   * Full Quiz uses `null` so MapLibre removes all grouping filters.
   */
  const activeFeatureIds =
    activeGroup.type === "full"
      ? null
      : Array.from(resolvedGroup?.featureIds ?? []);

  /**
   * Controls whether the floating quiz Settings panel is currently visible.
   */
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);

  /**
   * Controls whether the floating quiz Groups panel is currently visible.
   */
  const [isGroupsOpen, setIsGroupsOpen] = useState(false);

  /**
   * Opens or closes the Settings panel.
   */
  function toggleSettingsPanel(): void {
    setIsSettingsOpen((wasOpen) => !wasOpen);
  }

  /**
   * Opens or closes the Groups panel.
   */
  function toggleGroupsPanel(): void {
    setIsGroupsOpen((wasOpen) => !wasOpen);
  }

  /**
   * Applies an unsaved group and clears any previously active saved group.
   *
   * @param group - Unsaved group that should become active.
   */
  function applyUnsavedGroup(group: ActiveQuizGroup): void {
    setActiveSavedGroupId(null);

    applyGroup(group);
  }

  /**
   * Applies a saved group without clearing its saved-group identity.
   *
   * This is used when creating, loading, or later updating a persisted group.
   *
   * @param group - Saved group source that should become active.
   */
  function applySavedGroup(group: ActiveQuizGroup): void {
    applyGroup(group);
  }

  /**
   * Restores the complete quiz and clears any active saved-group selection.
   */
  function handleUseFullQuiz(): void {
    setActiveSavedGroupId(null);

    resetToFullQuiz();
  }

  /**
   * Toggles a saved group between active and inactive.
   *
   * Selecting an inactive saved group applies its stored source. Selecting the
   * currently active saved group returns to Full Quiz.
   *
   * @param savedGroup - Saved group selected by the user.
   */
  function toggleSavedGroup(savedGroup: SavedQuizGroup): void {
    if (activeSavedGroupId === savedGroup.id) {
      setActiveSavedGroupId(null);

      resetToFullQuiz();

      return;
    }

    setActiveSavedGroupId(savedGroup.id);

    applyGroup(savedGroup.source);
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

      {/* Quiz Settings and Groups controls */}
      <div className="absolute right-3 top-3 z-30 flex max-w-[calc(100vw-1.5rem)] flex-col items-end gap-5">
        {/* Panel toggle buttons */}
        <div className="relative z-30 flex max-w-full flex-row items-start gap-5">
          {/* Settings panel toggle */}
          <QuizSettingsButton
            isOpen={isSettingsOpen}
            onClick={toggleSettingsPanel}
          />

          {/* Groups panel toggle */}
          <QuizGroupsButton
            isOpen={isGroupsOpen}
            onClick={toggleGroupsPanel}
          />
        </div>

        {/* Floating panels */}
        <div className="relative z-30 flex flex-row items-start gap-5">
          {/* Quiz Settings panel */}
          {isSettingsOpen && (
            <div className="mt-2">
              <QuizSettingsPanel
                settings={settings}
                onChange={setSettings}
              />
            </div>
          )}

          {/* Quiz Groups panel */}
          {isGroupsOpen && (
            <div className="mt-2">
              <QuizGroupsPanel
                quiz={quiz}
                featureCollection={featureCollection}
                activeGroup={activeGroup}
                activeSavedGroupId={activeSavedGroupId}
                savedGroups={savedGroups}
                onApplyGroup={applyUnsavedGroup}
                onApplySavedGroup={applySavedGroup}
                onUseFullQuiz={handleUseFullQuiz}
                onToggleSavedGroup={toggleSavedGroup}
                onSaveGroup={saveGroup}
                onUpdateGroup={updateGroup}
                onDeleteGroup={deleteGroup}
                onSetActiveSavedGroup={setActiveSavedGroupId}
                isDisabled={false}
              />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
