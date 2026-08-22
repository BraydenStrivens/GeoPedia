/**
 * Displays temporary feedback beside the cursor after an incorrect
 * geographic feature is selected.
 */

import type { IncorrectSelection } from "@/maps/types";

type IncorrectSelectionPopupProps = {
  selection: IncorrectSelection | null;
};

export default function IncorrectSelectionPopup({
  selection,
}: IncorrectSelectionPopupProps) {
  if (!selection) {
    return null;
  }

  return (
    <div
      className="pointer-events-none absolute z-20 rounded-md bg-red-600/90 px-3 py-1.5 text-sm font-semibold text-white shadow-md backdrop-blur-sm"
      style={{
        left: selection.x + 12,
        top: selection.y + 12,
      }}
    >
      {selection.label}
    </div>
  );
}
