/**
 * Coordinates GeoPedia's hydrated town-based quiz experience.
 *
 * This component connects a town quiz to its persisted settings, population
 * filtering, location-guessing engine, MapLibre town presentation, floating
 * Settings and Filter panels, and quiz overlay.
 *
 * Town-specific orchestration lives here so the shared `QuizMapClient`
 * hydration boundary does not need to understand the internal state or
 * workflows of location-based town quizzes.
 */

"use client";

import { useMemo, useState } from "react";

import TownQuizMap from "@/components/map/TownQuizMap";
import TownQuizPanelControls from "@/components/quiz/controls/town/TownQuizPanelControls";
import TownQuizOverlay from "@/components/quiz/overlay/TownQuizOverlay";
import TownQuizFilterPanel from "@/components/quiz/panel/town/TownQuizFilterPanel";
import TownQuizSettingsPanel from "@/components/quiz/panel/town/TownQuizSettingsPanel";
import { getTownPopulationGroup } from "@/quiz/groupings/town/townPopulationGroups";
import { useTownQuiz } from "@/quiz/hooks/useTownQuiz";
import { useTownQuizSettings } from "@/quiz/hooks/useTownQuizSettings";
import { getTownQuestionName } from "@/quiz/town/getTownQuestionName";
import type { TownCountryConfig } from "@/quiz/town/townCountryConfigs";
import type { TownQuiz } from "@/types/quiz";

/**
 * Props required by the hydrated town quiz client.
 */
type HydratedTownQuizMapClientProps = {
  /** Country containing the quiz and its persisted user state. */
  countryId: string;

  /** Town quiz displayed and controlled by the map. */
  quiz: TownQuiz;

  /** Country-specific map and geographic scoring configuration. */
  townConfig: TownCountryConfig;
};

/**
 * Coordinates a hydrated location-based town quiz and its surrounding UI.
 *
 * @param props - Town quiz client properties.
 * @param props.countryId - Country used to identify persisted town settings.
 * @param props.quiz - Town quiz definition and generated settlement data.
 * @param props.townConfig - Country-specific map and scoring configuration.
 * @returns The hydrated town quiz map, controls, and overlay.
 */
export default function HydratedTownQuizMapClient({
  countryId,
  quiz,
  townConfig,
}: HydratedTownQuizMapClientProps) {
  /**
   * Number of population-ranked towns currently participating in the quiz.
   *
   * The complete generated dataset is active initially.
   */
  const [activeTownCount, setActiveTownCount] = useState(
    quiz.towns.length,
  );

  /** Whether the floating town Filter panel is currently visible. */
  const [isFilterOpen, setIsFilterOpen] = useState(false);

  /**
   * Whether the user is currently being told why the town Filter panel cannot
   * be opened.
   */
  const [isFilterBlockedMessageOpen, setIsFilterBlockedMessageOpen] =
    useState(false);

  /** Whether the floating town Settings panel is currently visible. */
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);

  /** Loads settings persisted specifically for this town quiz. */
  const { settings, setSettings } = useTownQuizSettings(
    countryId,
    quiz.id,
  );

  /**
   * Town records consumed by both the quiz engine and Normal-mode label layer.
   *
   * Full Quiz preserves the generated dataset exactly. Numeric filters use the
   * shared population-group helper so the national capital is included even
   * when it falls outside the requested population cutoff.
   */
  const activeTowns = useMemo(() => {
    if (activeTownCount === quiz.towns.length) {
      return quiz.towns;
    }

    return getTownPopulationGroup(quiz.towns, activeTownCount);
  }, [quiz.towns, activeTownCount]);

  /**
   * Whether the active town subset contains at least one settlement whose
   * native name differs from its English/international name.
   *
   * The Language setting is hidden when changing languages would have no
   * visible effect on any question in the active subset.
   */
  const hasNativeNames = useMemo(
    () => activeTowns.some((town) => town.nativeName !== undefined),
    [activeTowns],
  );

  const {
    currentQuestion,
    lastResult,

    answeredCount,
    questionCount,

    averageScore,
    totalDistanceKm,

    isActive,
    isFinished,

    startQuiz,
    skipQuestion,
    stopQuiz,
    restartQuiz,

    submitGuess,
  } = useTownQuiz({
    towns: activeTowns,
    maxErrorKm: townConfig.maxErrorKm,
  });

  /**
   * User-facing name for the current town question.
   */
  const currentQuestionName = currentQuestion
    ? getTownQuestionName(currentQuestion, settings.questionLanguage)
    : undefined;

  /**
   * Restores the complete generated town dataset.
   */
  function useFullTownQuiz(): void {
    setActiveTownCount(quiz.towns.length);
  }

  /**
   * Applies a population-ranked town count.
   *
   * @param count - Number of towns that should participate in the quiz.
   */
  function applyTownCount(count: number): void {
    setActiveTownCount(count);
  }

  /**
   * Opens or closes the town Settings panel.
   */
  function toggleSettingsPanel(): void {
    setIsSettingsOpen((wasOpen) => !wasOpen);
  }

  /**
   * Attempts to open or close the town Filter panel.
   *
   * Filtering cannot change while a quiz attempt is active because doing so
   * would change both the active question collection and the Normal-mode town
   * labels during gameplay.
   *
   * When filtering is blocked, an explanatory warning is displayed instead.
   */
  function toggleFilterPanel(): void {
    if (isActive) {
      setIsFilterBlockedMessageOpen(true);

      return;
    }

    setIsFilterBlockedMessageOpen(false);

    setIsFilterOpen((wasOpen) => !wasOpen);
  }

  /**
   * Starts a town quiz after closing all Filter-related floating UI.
   */
  function handleStartQuiz(): void {
    setIsFilterOpen(false);
    setIsFilterBlockedMessageOpen(false);

    startQuiz();
  }

  return (
    <div className="relative h-full w-full">
      {/* Interactive town quiz map */}
      <TownQuizMap
        townConfig={townConfig}
        towns={activeTowns}
        settings={settings}
        lastResult={lastResult}
        isGuessingEnabled={isActive && currentQuestion !== undefined}
        onGuess={submitGuess}
      />

      {/* Floating town quiz Settings and Filter controls */}
      <TownQuizPanelControls
        isSettingsOpen={isSettingsOpen}
        isFilterOpen={isFilterOpen}
        isFilterBlockedMessageOpen={isFilterBlockedMessageOpen}
        onToggleSettings={toggleSettingsPanel}
        onToggleFilter={toggleFilterPanel}
        onCloseFilterBlockedMessage={() =>
          setIsFilterBlockedMessageOpen(false)
        }
        settingsPanel={
          <TownQuizSettingsPanel
            settings={settings}
            hasNativeNames={hasNativeNames}
            onChange={setSettings}
          />
        }
        filterPanel={
          <TownQuizFilterPanel
            availableTownCount={quiz.towns.length}
            activeTownCount={activeTownCount}
            onUseFullQuiz={useFullTownQuiz}
            onApplyTownCount={applyTownCount}
          />
        }
      />

      {/* Town quiz question, score, and lifecycle overlay */}
      <TownQuizOverlay
        quizName={quiz.name}
        currentTownName={currentQuestionName}
        answeredCount={answeredCount}
        questionCount={questionCount}
        lastScore={lastResult?.score}
        lastDistanceKm={lastResult?.distanceKm}
        averageScore={averageScore}
        totalDistanceKm={totalDistanceKm}
        isActive={isActive}
        isFinished={isFinished}
        onStart={handleStartQuiz}
        onSkip={skipQuestion}
        onStop={stopQuiz}
        onRestart={restartQuiz}
      />
    </div>
  );
}
