/**
 * Registers all MapLibre feature interactions used by GeoPedia maps.
 *
 * Hover and click behavior are implemented in separate modules. This file
 * coordinates those systems and provides the small shared mutable hover state
 * they both require.
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
 * @param context - MapLibre instance, React refs, and callbacks required by
 * the interaction system.
 */
export function setupMapInteractions(
  context: MapInteractionContext,
): void {
  /**
   * Shared local hover state lets the click handler immediately clear the
   * feature that was being hovered without putting this purely MapLibre state
   * into React.
   */
  const hoverState: FeatureHoverState = {
    featureId: null,
  };

  registerHoverInteractions(context, hoverState);

  registerClickInteractions(context, hoverState);
}
