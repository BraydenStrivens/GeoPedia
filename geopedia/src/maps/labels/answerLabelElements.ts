/**
 * Creates and styles the HTML elements displayed by Show Answers markers.
 *
 * Answer labels use HTML rather than a MapLibre symbol layer so individual
 * labels can have custom rounded-rectangle styling and react directly to the
 * hover state of their associated geographic feature.
 */

import type { AnswerLabelMarkers } from "./answerLabelTypes";

/**
 * Creates the HTML element displayed inside a Show Answers marker.
 *
 * @param label - User-facing answer text displayed by the marker.
 * @returns Styled HTML element containing the answer.
 */
export function createAnswerLabelElement(
  label: string,
): HTMLDivElement {
  const element = document.createElement("div");

  element.textContent = label;

  element.className = [
    "pointer-events-none",
    "whitespace-nowrap",
    "rounded-md",
    "border",
    "border-gray-300",
    "bg-white",
    "px-2",
    "py-1",
    "text-xs",
    "font-semibold",
    "text-gray-900",
    "shadow-sm",
    "transition-all",
    "duration-150",
  ].join(" ");

  return element;
}

/**
 * Applies hover styling to the answer label belonging to the currently
 * hovered geographic feature.
 *
 * All other labels are returned to their normal appearance.
 *
 * @param labelMarkers - Currently rendered Show Answers markers.
 * @param hoveredFeatureId - ID of the currently hovered geographic feature.
 */
export function setAnswerLabelHovered(
  labelMarkers: AnswerLabelMarkers,
  hoveredFeatureId: string | null,
): void {
  for (const [featureId, labelMarker] of labelMarkers) {
    const isHovered = featureId === hoveredFeatureId;

    labelMarker.element.classList.toggle("bg-gray-800", isHovered);

    labelMarker.element.classList.toggle("text-white", isHovered);

    labelMarker.element.classList.toggle(
      "border-gray-800",
      isHovered,
    );

    /*
     * Remove the normal appearance while hovered so conflicting Tailwind
     * background, text, and border classes are never active simultaneously.
     */
    labelMarker.element.classList.toggle("bg-white", !isHovered);

    labelMarker.element.classList.toggle("text-gray-900", !isHovered);

    labelMarker.element.classList.toggle(
      "border-gray-300",
      !isHovered,
    );
  }
}
