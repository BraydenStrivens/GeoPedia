/**
 * Displays the label for a currently hovered map feature.
 */

import { HoveredFeature } from "@/maps/types";

type MapHoverLabelProps = {
  feature: HoveredFeature | null;
};

export default function MapHoverLabel({ feature }: MapHoverLabelProps) {
  if (!feature) {
    return null;
  }

  return (
    <div
      className="pointer-events-none absolute z-20 rounded-md bg-black/75 px-3 py-1.5 text-sm font-medium text-white shadow-lg"
      style={{
        left: feature.x + 12,
        top: feature.y + 12,
      }}
    >
      {feature.name}
    </div>
  );
}
