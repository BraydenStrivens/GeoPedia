/**
 * Creates and styles the HTML elements displayed by Show Answers markers.
 *
 * Answer labels use HTML rather than a MapLibre symbol layer so individual
 * labels can have custom rounded-rectangle styling, optional quiz imagery, and
 * react directly to the hover state of their associated geographic feature.
 */

import type {
  AnswerLabelContent,
  AnswerLabelMarkers,
} from "./answerLabelTypes";

/**
 * Creates the HTML element displayed inside a Show Answers marker.
 *
 * Text-only quizzes retain GeoPedia's existing compact rounded answer label.
 *
 * Image-based quizzes additionally display their question image beneath the
 * textual answer. Their layout is intentionally kept small because global
 * quizzes may display many geographic labels simultaneously.
 *
 * @param content - User-facing text and optional images displayed by the marker.
 * @returns Styled HTML element containing the complete answer presentation.
 */
export function createAnswerLabelElement(
  content: AnswerLabelContent,
): HTMLDivElement {
  const element = document.createElement("div");

  const hasImages = content.images.length > 0;

  element.className = [
    "pointer-events-none",
    "rounded-md",
    "border",
    "border-gray-300",
    "bg-gray-300",
    "font-semibold",
    "text-gray-900",
    "shadow-sm",
    "transition-all",
    "duration-150",

    /*
     * Image-based labels use tighter spacing and slightly smaller text so a
     * world-scale map can display many labels without excessive overlap.
     */
    hasImages
      ? "flex flex-col items-center gap-0.5 px-1.5 py-1 text-[10px] leading-tight"
      : "whitespace-nowrap px-2 py-1 text-xs",
  ].join(" ");

  /**
   * Render answer text as its own child instead of assigning element.textContent
   * directly so optional imagery can be placed underneath it.
   */
  const textElement = document.createElement("div");

  textElement.textContent = content.label;
  textElement.className = "whitespace-nowrap";

  element.appendChild(textElement);

  /**
   * Image questions normally contribute one image per geographic feature.
   *
   * A horizontal container is nevertheless used so multi-answer image features
   * can display several images without requiring another marker format.
   */
  if (hasImages) {
    const imageContainer = document.createElement("div");

    imageContainer.className = [
      "flex",
      "items-center",
      "justify-center",
      "gap-1",
    ].join(" ");

    for (const imageData of content.images) {
      const image = document.createElement("img");

      image.src = imageData.imageUrl;
      image.alt = imageData.alt;

      /*
       * Preserve the source image's aspect ratio while constraining its visual
       * footprint. Flags and future country-shape images can therefore use the
       * same Show Answers rendering system.
       */
      image.className = [
        "block",
        "h-auto",
        "max-h-8",
        "w-auto",
        "max-w-14",
        "object-contain",
      ].join(" ");

      imageContainer.appendChild(image);
    }

    element.appendChild(imageContainer);
  }

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
    labelMarker.element.classList.toggle("bg-gray-300", !isHovered);

    labelMarker.element.classList.toggle("text-gray-900", !isHovered);

    labelMarker.element.classList.toggle(
      "border-gray-300",
      !isHovered,
    );
  }
}
