/**
 * Map configuration for Bhutan's 20 dzongkhags.
 */

import { createMapConfig } from "@/maps/configs/createMapConfig";

import { BHUTAN_INITIAL_VIEW } from "./constants";

export const bhutanDzongkhagsMap = createMapConfig({
  id: "bhutan-dzongkhags",
  geojsonUrl: "/data/countries/bhutan/geojson/bhutan_adm1.geojson",

  featureProperty: "name",
  promoteId: "admin_id",

  initialView: BHUTAN_INITIAL_VIEW,

  hover: {
    labelProperty: "name",
  },
});
