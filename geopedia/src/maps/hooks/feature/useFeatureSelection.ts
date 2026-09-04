/**
 * Manages temporary feature-selection feedback for feature quiz maps.
 *
 * Feature selections are used in two contexts:
 *
 * - During an active quiz, the selection can identify an incorrectly clicked
 *   geographic feature.
 * - While the quiz is inactive, the selection can temporarily reveal the
 *   answer associated with a feature selected for inspection.
 *
 * Regardless of how the selection was created, it remains visible briefly
 * before being cleared automatically.
 */

import type { Dispatch, SetStateAction } from "react";
import { useEffect, useState } from "react";

import type { FeatureSelection } from "@/maps/types";

/**
 * Length of time temporary feature-selection feedback remains visible.
 */
const FEATURE_SELECTION_DURATION_MS = 1200;

/**
 * Result returned by `useFeatureSelection`.
 */
type UseFeatureSelectionResult = {
  /** Feature selection currently being displayed. */
  featureSelection: FeatureSelection | null;

  /** Updates or clears the current temporary feature selection. */
  setFeatureSelection: Dispatch<
    SetStateAction<FeatureSelection | null>
  >;
};

/**
 * Stores temporary feature-selection feedback and automatically clears it after
 * a short delay.
 *
 * The hook is intentionally unaware of why the feature was selected. The
 * caller determines whether the selection represents incorrect quiz feedback,
 * inactive-map inspection, or another temporary feature-selection interaction.
 *
 * @returns Current feature selection and its React state setter.
 */
export function useFeatureSelection(): UseFeatureSelectionResult {
  const [featureSelection, setFeatureSelection] =
    useState<FeatureSelection | null>(null);

  /**
   * Starts a new dismissal timer whenever temporary feature-selection feedback
   * changes.
   */
  useEffect(() => {
    if (!featureSelection) {
      return;
    }

    const timeoutId = window.setTimeout(() => {
      setFeatureSelection(null);
    }, FEATURE_SELECTION_DURATION_MS);

    return () => {
      window.clearTimeout(timeoutId);
    };
  }, [featureSelection]);

  return {
    featureSelection,
    setFeatureSelection,
  };
}
