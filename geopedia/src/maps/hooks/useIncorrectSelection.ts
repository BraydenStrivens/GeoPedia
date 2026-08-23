/**
 * Manages temporary incorrect-selection feedback for quiz maps.
 *
 * Incorrect selections remain visible briefly before being cleared
 * automatically.
 */

import type { Dispatch, SetStateAction } from "react";
import { useEffect, useState } from "react";

import type { IncorrectSelection } from "@/maps/types";

/**
 * Length of time incorrect-selection feedback remains visible.
 */
const INCORRECT_SELECTION_DURATION_MS = 1200;

/**
 * Result returned by `useIncorrectSelection`.
 */
type UseIncorrectSelectionResult = {
  /** Incorrect selection currently being displayed. */
  incorrectSelection: IncorrectSelection | null;

  /** Updates or clears the current incorrect selection. */
  setIncorrectSelection: Dispatch<
    SetStateAction<IncorrectSelection | null>
  >;
};

/**
 * Stores incorrect-selection feedback and automatically clears it after a
 * short delay.
 *
 * @returns Current incorrect selection and its React state setter.
 */
export function useIncorrectSelection(): UseIncorrectSelectionResult {
  const [incorrectSelection, setIncorrectSelection] =
    useState<IncorrectSelection | null>(null);

  /**
   * Starts a new dismissal timer whenever incorrect-selection feedback
   * changes.
   */
  useEffect(() => {
    if (!incorrectSelection) {
      return;
    }

    const timeoutId = window.setTimeout(() => {
      setIncorrectSelection(null);
    }, INCORRECT_SELECTION_DURATION_MS);

    return () => {
      window.clearTimeout(timeoutId);
    };
  }, [incorrectSelection]);

  return {
    incorrectSelection,
    setIncorrectSelection,
  };
}
