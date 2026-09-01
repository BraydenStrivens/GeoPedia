/**
 * Defines and resolves population-based grouping behavior for GeoPedia town
 * quizzes.
 *
 * Town quizzes provide predefined population groups such as Top 10, Top 25,
 * Top 50, and Top 100, with availability determined by the number of towns in
 * a country's generated dataset. These groups prioritize the most populous
 * locations while guaranteeing that the national capital is included without
 * increasing the requested group size.
 *
 * This module owns the constants, types, and selection helpers specific to
 * population-based town groups. Custom town-group selection and broader town
 * quiz state are handled separately.
 */

import type { TownQuizTown } from "@/types/quiz";

/**
 * Population-based preset sizes offered by town quizzes.
 *
 * Presets larger than the number of towns available to a particular country
 * should be hidden by the UI rather than producing a smaller preset.
 */
export const TOWN_QUIZ_PRESET_COUNTS = [10, 25, 50, 100] as const;

/**
 * Number of towns included in the largest generated country town dataset.
 */
export const MAX_TOWN_QUIZ_COUNT = 200;

/**
 * Minimum number of towns allowed in a custom town group.
 */
export const MIN_TOWN_QUIZ_COUNT = 1;

/**
 * Number of towns represented by one predefined population preset.
 */
export type TownQuizPresetCount =
  (typeof TOWN_QUIZ_PRESET_COUNTS)[number];

/**
 * Returns the highest-population towns for a population-based quiz group while
 * guaranteeing that the national capital occupies one of the requested slots.
 *
 * Generated town datasets are already ordered by `populationRank`, so the
 * initial population group can be selected directly from the beginning of the
 * array.
 *
 * If the capital already belongs to the requested population range, the normal
 * top-N result is returned unchanged. If the capital falls outside that range,
 * the lowest-ranked town in the range is replaced by the capital. The returned
 * group therefore always contains exactly `count` towns when at least `count`
 * towns are available.
 *
 * For example, if the capital is population rank 139:
 *
 * - Top 10 contains ranks 1-9 plus the capital.
 * - Top 25 contains ranks 1-24 plus the capital.
 * - Top 50 contains ranks 1-49 plus the capital.
 * - Top 100 contains ranks 1-99 plus the capital.
 *
 * @param towns - Population-ranked towns available to the quiz.
 * @param count - Number of towns requested for the population group.
 * @returns Population-based town group with the capital included when present.
 */
export function getTownPopulationGroup(
  towns: TownQuizTown[],
  count: number,
): TownQuizTown[] {
  const requestedCount = Math.min(Math.max(0, count), towns.length);

  if (requestedCount === 0) {
    return [];
  }

  const topTowns = towns.slice(0, requestedCount);
  const capital = towns.find((town) => town.isCapital);

  if (!capital || topTowns.some((town) => town.id === capital.id)) {
    return topTowns;
  }

  return [...topTowns.slice(0, requestedCount - 1), capital];
}

/**
 * Returns the population preset sizes supported by the supplied town dataset.
 *
 * A preset is available only when the country contains at least that many
 * generated towns. This prevents, for example, a country with 43 towns from
 * displaying Top 50 or Top 100 options.
 *
 * @param townCount - Number of towns available to the country quiz.
 * @returns Population preset sizes that can be offered by the UI.
 */
export function getAvailableTownPresetCounts(
  townCount: number,
): TownQuizPresetCount[] {
  return TOWN_QUIZ_PRESET_COUNTS.filter(
    (count) => count <= townCount,
  );
}
