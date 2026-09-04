/**
 * Resolves the user-facing question name for a town quiz.
 *
 * English mode always uses the town's preferred English/international name.
 * Native mode uses `nativeName` when one exists and otherwise falls back to the
 * English name. This allows countries containing a mixture of identical and
 * differing English/native names to use one consistent question-language
 * setting without requiring duplicate data.
 */

import type { TownQuizTown } from "@/types/quiz";
import type { TownQuizQuestionLanguage } from "@/types/townQuizSettings";

/**
 * Returns the settlement name that should be displayed as the current question.
 *
 * @param town - Current town quiz question.
 * @param language - Persisted question-language setting.
 * @returns English or native question name.
 */
export function getTownQuestionName(
  town: TownQuizTown,
  language: TownQuizQuestionLanguage,
): string {
  if (language === "native" && town.nativeName) {
    return town.nativeName;
  }

  return town.name;
}
