/**
 * Defines the shared MapLibre source and layer IDs used by GeoPedia's
 * geographic map system.
 *
 * Keeping these IDs centralized prevents hooks, interaction handlers, and
 * layer-creation utilities from drifting apart as the map architecture grows.
 */

/**
 * GeoJSON source containing GeoPedia's geographic quiz features.
 */
export const FEATURE_SOURCE_ID = "features";

/**
 * GeoJSON source containing GeoPedia's contextual town-label points.
 */
export const TOWN_SOURCE_ID = "towns";

/**
 * Symbol layer displaying GeoPedia-controlled town names.
 */
export const TOWN_LABEL_LAYER_ID = "town-labels";

/**
 * Main geographic fill layer used for normal map shading and quiz-result
 * coloring.
 */
export const FEATURE_FILL_LAYER_ID = "features-fill";

/**
 * Temporary overlay used to highlight features selected during manual quiz
 * group creation or editing.
 */
export const FEATURE_SELECTION_LAYER_ID = "features-selection";

/**
 * Overlay used for geographic hover highlighting.
 */
export const FEATURE_HOVER_LAYER_ID = "features-hover";

/**
 * Explicit geographic border layer rendered above GeoPedia's feature fills.
 */
export const FEATURE_BORDER_LAYER_ID = "features-borders";
