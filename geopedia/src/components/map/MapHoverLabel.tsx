/**
 * Displays a floating label for the geographic feature currently being
 * hovered on a GeoPedia map.
 *
 * The label follows the cursor using coordinates supplied by the map's hover
 * interaction system. It does not capture pointer events, allowing map
 * interaction to continue normally while the label is visible.
 */

import type { HoveredFeature } from "@/maps/types";

/**
 * Distance in pixels between the cursor and the floating hover label.
 *
 * The offset prevents the label from appearing directly underneath the
 * pointer and obscuring the geographic feature being inspected.
 */
const HOVER_LABEL_OFFSET = 12;

/**
 * Props required by the map hover label.
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
 * @param props.feature - Currently hovered feature and its cursor position.
 * @returns The floating hover label, or null when no feature is hovered.
 */
export default function MapHoverLabel({
  feature,
}: MapHoverLabelProps) {
  if (!feature) {
    return null;
  }

  return (
    /* Floating feature label */
    <div
      className="pointer-events-none absolute z-20 rounded-md bg-black/75 px-3 py-1.5 text-sm font-medium text-white shadow-lg"
      style={{
        left: feature.x + HOVER_LABEL_OFFSET,

        top: feature.y + HOVER_LABEL_OFFSET,
      }}
    >
      {feature.name}
    </div>
  );
}
