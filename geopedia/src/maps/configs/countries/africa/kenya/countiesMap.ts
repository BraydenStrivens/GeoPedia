/**
 * Map configuration for Kenya's counties.
 *
 * Features use the canonical county_id property for map identity and answers.
 */

import { createMapConfig } from "@/maps/configs/createMapConfig";

import { KENYA_INITIAL_VIEW } from "./constants";

export const kenyaCountiesMap = createMapConfig({
  id: "kenya-counties",
  geojsonUrl: "/data/countries/kenya/geojson/counties.geojson",

  featureProperty: "county_id",
  promoteId: "county_id",

  initialView: KENYA_INITIAL_VIEW,

  hover: {
    labelProperty: "county",
  },
});
