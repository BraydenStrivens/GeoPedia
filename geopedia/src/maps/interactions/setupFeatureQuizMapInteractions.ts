/**
 * Registers GeoPedia's feature-map geographic interaction handlers.
 *
 * Feature click and hover behavior are implemented in separate modules. This
 * file coordinates those systems and owns the small mutable hover state they
 * share.
 *
 * The interaction system supports both active feature-quiz behavior and
 * inactive map inspection. During an active quiz, feature clicks can submit
 * answers and display temporary incorrect-selection feedback. While the quiz
 * is inactive, feature clicks can temporarily reveal the selected feature's
 * answer for inspection.
 *
 * World-country navigation uses an independent interaction system and is not
 * represented here.
 */

import { registerQuizClickInteractions } from "./featureQuizClickInteractions";
import { registerQuizHoverInteractions } from "./featureQuizHoverInteractions";
import type {
  FeatureHoverState,
  QuizMapInteractionContext,
} from "./featureQuizInteractionTypes";

/**
 * Registers hover and click interactions for a GeoPedia feature quiz map.
 *
 * The supplied interaction context provides the current map, quiz state,
 * runtime settings, and callbacks used by both active-quiz interactions and
 * inactive feature inspection.
 *
 * @param context - MapLibre instance, runtime refs, and callbacks required by
 * the feature-map interaction system.
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
