/**
 * Provides a reusable React hook for keeping a ref synchronized
 * with the latest value received during rendering.
 *
 * This is useful when long-lived external event handlers, such as
 * MapLibre listeners, need access to current React values without
 * recreating those handlers every time the value changes.
 */

import { useEffect, useRef } from "react";

/**
 * Returns a ref whose `.current` value is automatically updated
 * whenever the provided value changes.
 */
export function useLatestRef<T>(value: T) {
  const ref = useRef(value);

  useEffect(() => {
    ref.current = value;
  }, [value]);

  return ref;
}
