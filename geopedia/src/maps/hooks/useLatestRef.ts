/**
 * Provides a reusable React hook for keeping a ref synchronized
 * with the latest value received during rendering.
 *
 * This is useful when long-lived external event handlers, such as
 * MapLibre listeners, need access to current React values without
 * recreating those handlers every time the value changes.
 */

import { RefObject, useEffect, useRef } from "react";

/**
 * Returns a ref whose `.current` value always reflects the latest value
 * provided to the hook.
 *
 * The ref object itself remains stable across renders, which makes it safe to
 * pass into long-lived callbacks that should not be recreated whenever the
 * underlying value changes.
 *
 * @param value - Value that should remain available through the ref.
 * @returns Stable React ref containing the latest value.
 */
export function useLatestRef<T>(value: T): RefObject<T> {
  const latestValueRef = useRef(value);

  /**
   * Synchronizes the mutable ref after React commits a render containing a
   * new value.
   */
  useEffect(() => {
    latestValueRef.current = value;
  }, [value]);

  return latestValueRef;
}
