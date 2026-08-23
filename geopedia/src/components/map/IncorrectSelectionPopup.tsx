/**
 * Displays temporary feedback beside the cursor after the user selects an
 * incorrect geographic feature during a quiz.
 *
 * The popup shows the label of the feature that was actually selected and
 * follows the cursor position captured when the incorrect selection occurred.
 * It does not capture pointer events, allowing map interaction to continue
 * normally while the feedback is visible.
 */

import type { IncorrectSelection } from "@/maps/types";

/**
 * Distance in pixels between the recorded cursor position and the incorrect
 * selection popup.
 *
 * The offset prevents the popup from appearing directly underneath the
 * pointer or obscuring the geographic feature that was selected.
 */
const INCORRECT_SELECTION_POPUP_OFFSET = 12;

/**
 * Props required by the incorrect selection popup.
 */
type IncorrectSelectionPopupProps = {
  /** Incorrect selection to display, or null when no feedback is visible. */
  selection: IncorrectSelection | null;
};

/**
 * Displays the label of an incorrectly selected geographic feature beside
 * the cursor.
 *
 * Nothing is rendered when there is no active incorrect selection.
 *
 * @param props - Incorrect selection popup properties.
 * @param props.selection - Incorrect selection and its recorded cursor position.
 * @returns The incorrect-selection popup, or null when no feedback is active.
 */
export default function IncorrectSelectionPopup({
  selection,
}: IncorrectSelectionPopupProps) {
  if (!selection) {
    return null;
  }

  return (
    /* Incorrect selection feedback */
    <div
      className="pointer-events-none absolute z-20 rounded-md bg-red-600/90 px-3 py-1.5 text-sm font-semibold text-white shadow-md backdrop-blur-sm"
      style={{
        left: selection.x + INCORRECT_SELECTION_POPUP_OFFSET,

        top: selection.y + INCORRECT_SELECTION_POPUP_OFFSET,
      }}
    >
      {selection.label}
    </div>
  );
}
