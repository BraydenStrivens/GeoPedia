/**
 * Calculates safe geographic positions for Show Answers labels.
 *
 * Turf's pointOnFeature is preferred because it usually places a label on
 * the visible geography itself. MapLibre-rendered geometry can occasionally
 * be clipped or invalid, so these helpers fall back to a valid coordinate
 * contained within the feature rather than allowing one bad geometry to
 * crash Show Answers.
 */

import pointOnFeature from "@turf/point-on-feature";
import type { Feature, Geometry } from "geojson";
import type { MapGeoJSONFeature } from "maplibre-gl";

/**
 * Converts a MapLibre-rendered feature into the standard GeoJSON Feature
 * representation expected by Turf.
 *
 * @param feature - MapLibre feature to convert.
 * @returns Standard GeoJSON feature containing its geometry and properties.
 */
function toGeoJsonFeature(
  feature: MapGeoJSONFeature,
): Feature<Geometry> {
  return {
    type: "Feature",
    properties: feature.properties ?? {},
    geometry: feature.geometry,
  };
}

/**
 * Recursively searches nested GeoJSON coordinates for the first valid
 * longitude/latitude pair.
 *
 * @param coordinates - GeoJSON coordinate structure to search.
 * @returns First valid coordinate pair, or `null` when none can be found.
 */
function findFirstValidCoordinateInArray(
  coordinates: unknown,
): [number, number] | null {
  if (!Array.isArray(coordinates)) {
    return null;
  }

  if (
    coordinates.length >= 2 &&
    typeof coordinates[0] === "number" &&
    typeof coordinates[1] === "number" &&
    Number.isFinite(coordinates[0]) &&
    Number.isFinite(coordinates[1])
  ) {
    return [coordinates[0], coordinates[1]];
  }

  for (const childCoordinates of coordinates) {
    const validCoordinate =
      findFirstValidCoordinateInArray(childCoordinates);

    if (validCoordinate) {
      return validCoordinate;
    }
  }

  return null;
}

/**
 * Searches a GeoJSON geometry for the first valid longitude/latitude pair.
 *
 * Geometry collections are searched recursively because they do not expose
 * a direct `coordinates` property.
 *
 * @param geometry - GeoJSON geometry to search.
 * @returns First valid coordinate pair, or `null` when none exists.
 */
function findFirstValidCoordinate(
  geometry: Geometry,
): [number, number] | null {
  if (geometry.type === "GeometryCollection") {
    for (const childGeometry of geometry.geometries) {
      const validCoordinate = findFirstValidCoordinate(childGeometry);

      if (validCoordinate) {
        return validCoordinate;
      }
    }

    return null;
  }

  return findFirstValidCoordinateInArray(geometry.coordinates);
}

/**
 * Returns a safe geographic anchor for a Show Answers marker.
 *
 * Turf's pointOnFeature is attempted first. If Turf cannot process the
 * rendered geometry, any valid coordinate contained within the feature is
 * used as a fallback.
 *
 * @param feature - MapLibre feature requiring an answer-label position.
 * @returns Longitude/latitude anchor, or `null` when no valid position exists.
 */
export function getAnswerLabelAnchor(
  feature: MapGeoJSONFeature,
): [number, number] | null {
  try {
    const anchor = pointOnFeature(toGeoJsonFeature(feature));

    const [longitude, latitude] = anchor.geometry.coordinates;

    if (Number.isFinite(longitude) && Number.isFinite(latitude)) {
      return [longitude, latitude];
    }
  } catch (error) {
    console.warn(
      "Could not calculate answer label position:",
      feature.id,
      error,
    );
  }

  /*
   * Turf failed, so fall back to a valid coordinate from the feature instead
   * of allowing one malformed geometry to break Show Answers.
   */
  return findFirstValidCoordinate(feature.geometry);
}
