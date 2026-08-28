/**
 * Registers PMTiles URL support with MapLibre.
 *
 * PMTiles stores an entire vector-tile archive in one file while allowing
 * MapLibre to request only the byte ranges needed for visible tiles.
 */

import * as maplibregl from "maplibre-gl";
import { Protocol } from "pmtiles";

/**
 * The protocol instance must remain alive after registration because MapLibre
 * calls its tile resolver whenever PMTiles data is requested.
 */
const pmtilesProtocol = new Protocol();

/**
 * Prevent duplicate protocol registration when multiple maps are created
 * during development or React remounts.
 */
let isRegistered = false;

/**
 * Registers the `pmtiles://` protocol used by GeoPedia vector-tile sources.
 */
export function registerPmtilesProtocol(): void {
  if (isRegistered) {
    return;
  }

  maplibregl.addProtocol("pmtiles", pmtilesProtocol.tile);

  isRegistered = true;
}
