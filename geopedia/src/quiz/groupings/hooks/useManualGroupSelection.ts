/**
 * Manages the temporary geographic feature selection used to construct or edit
 * a manual quiz group.
 *
 * Manual-selection state is intentionally separate from the active quiz group.
 * While selection mode is active, the user builds a draft set of stable map
 * feature IDs. That draft is only persisted when a saved manual group is
 * created or updated.
 *
 * The hook owns:
 *
 * - Whether manual-selection mode is active.
 * - The current draft feature-ID set.
 * - Feature toggling.
 * - Select All.
 * - Deselect All.
 * - Loading an existing manual group into selection mode.
 * - Cancelling and clearing the draft.
 */

"use client";

import { useState } from "react";

/**
 * State and controls returned by the manual-group selection workflow.
 */
type UseManualGroupSelectionResult = {
  /** Whether map clicks currently toggle manual feature selection. */
  isSelecting: boolean;

  /** Stable IDs of the features currently included in the draft selection. */
  selectedFeatureIds: ReadonlySet<string>;

  /**
   * Begins manual-selection mode with an optional initial feature selection.
   *
   * Existing feature IDs are supplied when editing a previously saved manual
   * group.
   */
  beginSelection: (initialFeatureIds?: Iterable<string>) => void;

  /** Adds or removes one feature from the draft selection. */
  toggleFeature: (featureId: string) => void;

  /** Replaces the current draft with every supplied feature ID. */
  selectAllFeatures: (featureIds: Iterable<string>) => void;

  /** Removes one specific feature from the draft selection. */
  removeFeature: (featureId: string) => void;

  /** Removes every feature while keeping manual-selection mode active. */
  clearSelection: () => void;

  /** Exits manual-selection mode and discards the complete draft. */
  cancelSelection: () => void;
};

/**
 * Owns the temporary feature-ID draft used by manual quiz-group workflows.
 *
 * @returns Manual-selection state and controls.
 */
export function useManualGroupSelection(): UseManualGroupSelectionResult {
  /** Whether map feature clicks currently modify the manual selection. */
  const [isSelecting, setIsSelecting] = useState(false);

  /** Stable map feature IDs belonging to the current manual-selection draft. */
  const [selectedFeatureIds, setSelectedFeatureIds] = useState<
    Set<string>
  >(new Set());

  /**
   * Starts manual-selection mode with an optional initial selection.
   *
   * Starting with existing IDs allows saved manual groups to reuse the same
   * workflow for editing.
   *
   * @param initialFeatureIds - Feature IDs that should begin selected.
   */
  function beginSelection(
    initialFeatureIds: Iterable<string> = [],
  ): void {
    setSelectedFeatureIds(new Set(initialFeatureIds));

    setIsSelecting(true);
  }

  /**
   * Adds or removes one feature from the current manual-selection draft.
   *
   * @param featureId - Stable ID of the geographic feature to toggle.
   */
  function toggleFeature(featureId: string): void {
    setSelectedFeatureIds((previousFeatureIds) => {
      const updatedFeatureIds = new Set(previousFeatureIds);

      if (updatedFeatureIds.has(featureId)) {
        updatedFeatureIds.delete(featureId);
      } else {
        updatedFeatureIds.add(featureId);
      }

      return updatedFeatureIds;
    });
  }

  /**
   * Replaces the current manual-selection draft with every supplied feature ID.
   *
   * @param featureIds - Stable IDs of all features that should become selected.
   */
  function selectAllFeatures(featureIds: Iterable<string>): void {
    setSelectedFeatureIds(new Set(featureIds));
  }

  /**
   * Removes one feature from the current manual-selection draft.
   *
   * This is used by the selected-feature list in the Groups panel.
   *
   * @param featureId - Stable ID of the feature to remove.
   */
  function removeFeature(featureId: string): void {
    setSelectedFeatureIds((previousFeatureIds) => {
      if (!previousFeatureIds.has(featureId)) {
        return previousFeatureIds;
      }

      const updatedFeatureIds = new Set(previousFeatureIds);

      updatedFeatureIds.delete(featureId);

      return updatedFeatureIds;
    });
  }

  /**
   * Clears every selected feature while preserving manual-selection mode.
   */
  function clearSelection(): void {
    setSelectedFeatureIds(new Set());
  }

  /**
   * Exits manual-selection mode and discards the current draft.
   */
  function cancelSelection(): void {
    setSelectedFeatureIds(new Set());

    setIsSelecting(false);
  }

  return {
    isSelecting,
    selectedFeatureIds,

    beginSelection,
    toggleFeature,
    selectAllFeatures,
    removeFeature,
    clearSelection,
    cancelSelection,
  };
}
