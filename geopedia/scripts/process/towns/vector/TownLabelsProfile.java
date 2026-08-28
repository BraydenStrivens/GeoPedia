/**
 * Generates GeoPedia's runtime town-label PMTiles archive from the processed
 * town GeoJSON dataset.
 *
 * The input GeoJSON remains GeoPedia's canonical processed settlement dataset.
 * This profile creates a much smaller runtime representation containing only
 * properties needed by the MapLibre town-label layer.
 *
 * Each settlement is omitted from vector tiles below the integer portion of its
 * fractional `labelMinZoom`. The original fractional value is retained as a
 * vector-tile attribute so MapLibre can continue revealing labels gradually at
 * quarter-zoom intervals.
 */

import com.onthegomap.planetiler.FeatureCollector;
import com.onthegomap.planetiler.Planetiler;
import com.onthegomap.planetiler.Profile;
import com.onthegomap.planetiler.config.Arguments;
import com.onthegomap.planetiler.reader.SourceFeature;

import java.nio.file.Path;
import java.util.Map;

public class TownLabelsProfile implements Profile {

  /**
   * Name used by Planetiler for the GeoJSON source.
   */
  private static final String SOURCE_NAME =
    "towns";

  /**
   * Vector-tile layer consumed by MapLibre.
   */
  private static final String TILE_LAYER_NAME =
    "town_labels";

  /**
   * Highest zoom at which settlement features are explicitly generated.
   */
  private static final int MAX_ZOOM =
    14;

  /**
   * Returns a descriptive profile name stored in archive metadata.
   */
  @Override
  public String name() {
    return "GeoPedia Town Labels";
  }

  /**
   * Returns a short description stored in archive metadata.
   */
  @Override
  public String description() {
    return "GeoPedia contextual settlement labels";
  }

  /**
   * Converts one processed GeoJSON settlement into a lightweight vector-tile
   * point feature.
   *
   * @param sourceFeature GeoJSON feature supplied by Planetiler.
   * @param features Collector receiving output vector-tile features.
   */
  @Override
  public void processFeature(
    SourceFeature sourceFeature,
    FeatureCollector features
  ) {
    if (
      !SOURCE_NAME.equals(
        sourceFeature.getSource()
      )
    ) {
      return;
    }

    Map<String, Object> tags =
      sourceFeature.tags();

    String name =
      getString(
        tags,
        "name"
      );

    if (
      name == null ||
      name.isBlank()
    ) {
      return;
    }

    double labelMinZoom =
      getDouble(
        tags,
        "labelMinZoom",
        MAX_ZOOM
      );

    /*
     * Planetiler uses integer tile zooms.
     *
     * A town with labelMinZoom=6.72 must physically exist in zoom-6 tiles so
     * MapLibre can reveal it once the actual map reaches 6.72.
     */
    int tileMinZoom =
      Math.max(
        0,
        Math.min(
          MAX_ZOOM,
          (int) Math.floor(
            labelMinZoom
          )
        )
      );

    FeatureCollector.Feature output =
      features
        .point(
          TILE_LAYER_NAME
        )
        .setMinZoom(
          tileMinZoom
        )
        .setMaxZoom(
          MAX_ZOOM
        )
        .setAttr(
          "name",
          name
        )
        .setAttr(
          "labelMinZoom",
          labelMinZoom
        );

    /*
     * Only attributes used by the runtime town layer are retained.
     */
    copyAttribute(
      tags,
      output,
      "place"
    );

    copyAttribute(
      tags,
      output,
      "importance"
    );

    copyAttribute(
      tags,
      output,
      "significanceTier"
    );

    copyAttribute(
      tags,
      output,
      "markerType"
    );
  }

  /**
   * Copies one optional property from the source feature to the vector tile.
   */
  private static void copyAttribute(
    Map<String, Object> tags,
    FeatureCollector.Feature output,
    String key
  ) {
    Object value =
      tags.get(
        key
      );

    if (
      value != null
    ) {
      output.setAttr(
        key,
        value
      );
    }
  }

  /**
   * Reads a string property.
   */
  private static String getString(
    Map<String, Object> tags,
    String key
  ) {
    Object value =
      tags.get(
        key
      );

    return value == null
      ? null
      : String.valueOf(
          value
        );
  }

  /**
   * Reads a numeric property while tolerating JSON values represented either
   * as Java Numbers or numeric strings.
   */
  private static double getDouble(
    Map<String, Object> tags,
    String key,
    double fallback
  ) {
    Object value =
      tags.get(
        key
      );

    if (
      value instanceof Number number
    ) {
      return number.doubleValue();
    }

    if (
      value instanceof String string
    ) {
      try {
        return Double.parseDouble(
          string
        );
      } catch (
        NumberFormatException ignored
      ) {
        return fallback;
      }
    }

    return fallback;
  }

  /**
   * Generates the PMTiles archive.
   *
   * Usage:
   *
   * java ... TownLabelsProfile
   *   --input=public/data/geojson/world/towns.geojson
   *   --output=public/data/tiles/world_towns.pmtiles
   */
  public static void main(
    String[] args
  ) {
    Arguments arguments =
      Arguments.fromArgs(
        args
      );

    Path inputPath =
      arguments.inputFile(
        "input",
        "Processed town GeoJSON input",
        Path.of(
          "public/data/geojson/world/towns.geojson"
        )
      );

    Path outputPath =
      arguments.file(
        "output",
        "PMTiles output archive",
        Path.of(
          "public/data/tiles/world_towns.pmtiles"
        )
      );

    Planetiler
      .create(
        arguments
      )
      .setProfile(
        new TownLabelsProfile()
      )
      .addGeoJsonSource(
        SOURCE_NAME,
        inputPath
      )
      .overwriteOutput(
        outputPath
      )
      .run();
  }
}