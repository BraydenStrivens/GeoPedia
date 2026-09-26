/**
 * Calculates safe geographic positions for Show Answers labels.
 *
 * Turf's pointOnFeature is preferred because it usually places a label on
 * the visible geography itself. MapLibre-rendered geometry can occasionally
 * be clipped or invalid, so these helpers fall back to a valid coordinate
 * contained within the feature rather than allowing one bad geometry to
 * crash Show Answers.
 */

import area from "@turf/area";
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
 * Returns the polygon with the greatest geographic area from a MultiPolygon.
 *
 * Show Answers labels should represent the feature's primary landmass rather
 * than being influenced by smaller detached polygons such as islands.
 *
 * @param feature - MultiPolygon feature whose largest polygon should be found.
 * @returns GeoJSON feature containing only the largest polygon.
 */
function getLargestPolygonFeature(
  feature: MapGeoJSONFeature,
): Feature<Geometry> {
  if (feature.geometry.type !== "MultiPolygon") {
    return toGeoJsonFeature(feature);
  }

  let largestPolygon = feature.geometry.coordinates[0];
  let largestArea = -1;

  for (const polygonCoordinates of feature.geometry.coordinates) {
    const polygonFeature: Feature<Geometry> = {
      type: "Feature",
      properties: feature.properties ?? {},
      geometry: {
        type: "Polygon",
        coordinates: polygonCoordinates,
      },
    };

    const polygonArea = area(polygonFeature);

    if (polygonArea > largestArea) {
      largestArea = polygonArea;
      largestPolygon = polygonCoordinates;
    }
  }

  return {
    type: "Feature",
    properties: feature.properties ?? {},
    geometry: {
      type: "Polygon",
      coordinates: largestPolygon,
    },
  };
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
    const anchor = pointOnFeature(getLargestPolygonFeature(feature));

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
