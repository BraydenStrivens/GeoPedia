// /**
//  * Defines shared types used by GeoPedia's Show Answers label system.
//  */

// import type { Marker } from "maplibre-gl";

// /**
//  * Associates a MapLibre marker with the HTML element displayed inside it.
//  *
//  * The element is retained separately so its appearance can be updated when
//  * the corresponding geographic feature is hovered.
//  */
// export type AnswerLabelMarker = {
//   /** MapLibre marker responsible for positioning the answer label. */
//   marker: Marker;

//   /** HTML element containing the visible answer label. */
//   element: HTMLDivElement;
// };

// /**
//  * Collection of currently rendered Show Answers markers keyed by feature ID.
//  */
// export type AnswerLabelMarkers = globalThis.Map<
//   string,
//   AnswerLabelMarker
// >;

/**
 * Defines shared types used by GeoPedia's Show Answers label system.
 */

import type { Marker } from "maplibre-gl";

/**
 * Optional image displayed inside one Show Answers marker.
 *
 * Image data originates from an image-based quiz question's prompt rather than
 * from the geographic map configuration itself.
 */
export type AnswerLabelImage = {
  /** Public URL of the image displayed inside the answer marker. */
  imageUrl: string;

  /** Accessible description assigned to the rendered image element. */
  alt: string;
};

/**
 * Complete user-facing content displayed by one Show Answers marker.
 *
 * Text-only quizzes provide only `label`.
 *
 * Image-based quizzes may additionally provide one or more images. Multiple
 * images are supported because one geographic feature can represent multiple
 * quiz answers.
 */
export type AnswerLabelContent = {
  /** User-facing textual answer displayed by the marker. */
  label: string;

  /** Optional quiz images displayed beneath the textual answer. */
  images: AnswerLabelImage[];
};

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
