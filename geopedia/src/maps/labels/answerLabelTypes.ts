/**
 * Defines shared types used by GeoPedia's Show Answers label system.
 */

import type { Marker } from "maplibre-gl";

/**
 * Associates a MapLibre marker with the HTML element displayed inside it.
 *
 * The element is retained separately so its appearance can be updated when
 * the corresponding geographic feature is hovered.
 */
export type AnswerLabelMarker = {
  /** MapLibre marker responsible for positioning the answer label. */
  marker: Marker;

  /** HTML element containing the visible answer label. */
  element: HTMLDivElement;
};

/**
 * Collection of currently rendered Show Answers markers keyed by feature ID.
 */
export type AnswerLabelMarkers = globalThis.Map<
  string,
  AnswerLabelMarker
>;
