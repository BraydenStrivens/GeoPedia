/**
 * Registers GeoPedia's quiz-map geographic interaction handlers.
 *
 * Quiz click and hover behavior are implemented in separate modules. This file
 * coordinates those systems and owns the small mutable hover state they share.
 *
 * World-country navigation uses an independent interaction system and is not
 * represented here.
 */

import { registerQuizClickInteractions } from "./quizClickInteractions";
import { registerQuizHoverInteractions } from "./quizHoverInteractions";
import type {
  FeatureHoverState,
  QuizMapInteractionContext,
} from "./quizInteractionTypes";

/**
 * Registers hover and click interactions for a GeoPedia quiz map.
 *
 * @param context - MapLibre instance, runtime refs, and callbacks required by
 * the quiz interaction system.
 * @returns Cleanup function removing all registered interaction listeners.
 */
export function setupQuizMapInteractions(
  context: QuizMapInteractionContext,
): () => void {
  /**
   * Mutable hover identity shared by hover and click handlers.
   *
   * The click handler uses this state to immediately clear hover when a quiz
   * answer completes a feature, without routing purely MapLibre state through
   * React.
   */
  const hoverState: FeatureHoverState = {
    featureId: null,
  };

  const cleanupHover = registerQuizHoverInteractions(
    context,
    hoverState,
  );

  const cleanupClick = registerQuizClickInteractions(
    context,
    hoverState,
  );

  return () => {
    cleanupClick();
    cleanupHover();
  };
}
