/**
 * Displays a floating label for the geographic feature currently being
 * hovered on GeoPedia's world navigation map.
 *
 * The label follows the cursor using coordinates supplied by the map's hover
 * interaction system. It does not capture pointer events, allowing map
 * interaction to continue normally while the label is visible.
 *
 * This component is used by the Home world-navigation map to identify
 * countries that provide GeoPedia quizzes.
 */

/**
 * Distance in pixels between the cursor and the floating hover label.
 *
 * The offset prevents the label from appearing directly underneath the
 * pointer and obscuring the geographic feature being inspected.
 */
const HOVER_LABEL_OFFSET = 12;

import type { HoveredFeature } from "@/maps/types";

/**
 * Props required by the world-navigation map hover label.
 */
type MapHoverLabelProps = {
  /** Feature currently being hovered, or null when nothing is hovered. */
  feature: HoveredFeature | null;
};

/**
 * Displays the name of the currently hovered geographic feature beside the
 * cursor.
 *
 * Nothing is rendered when no feature is currently hovered.
 *
 * @param props - Map hover label properties.
 * @returns Floating geographic feature label, or null when no feature is
 * hovered.
 */
export default function MapHoverLabel({
  feature,
}: MapHoverLabelProps) {
  if (!feature) {
    return null;
  }

  return (
    /* Floating geographic feature label */
    <div
      className="pointer-events-none absolute z-20 rounded-md bg-text/75 px-3 py-1.5 text-sm font-medium text-background-1 shadow-lg"
      style={{
        left: feature.x + HOVER_LABEL_OFFSET,
        top: feature.y + HOVER_LABEL_OFFSET,
      }}
    >
      {feature.name}
    </div>
  );
}
