/**
 * Registers GeoPedia's MapLibre geographic interaction handlers.
 *
 * Click and hover behavior are implemented in separate modules. This file
 * coordinates those systems and owns the small mutable hover state they share.
 *
 * The shared hover state remains outside React because it represents temporary
 * MapLibre interaction state rather than UI state that needs to trigger renders.
 */

import { registerClickInteractions } from "./clickInteractions";
import { registerHoverInteractions } from "./hoverInteractions";
import type {
  FeatureHoverState,
  MapInteractionContext,
} from "./interactionTypes";

/**
 * Registers hover and click interactions for GeoPedia's geographic feature
 * layer.
 *
 * @param context - MapLibre instance, runtime refs, and callbacks required by
 * the interaction system.
 */
export function setupMapInteractions(
  context: MapInteractionContext,
): void {
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

  registerHoverInteractions(context, hoverState);

  registerClickInteractions(context, hoverState);
}
