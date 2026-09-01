/**
 * Contains the small SVG icons used by GeoPedia's active quiz controls.
 *
 * These icons are presentation-only and intentionally contain no quiz logic.
 */

/**
 * Icon displayed by the Skip control.
 *
 * @returns Skip icon SVG.
 */
export function SkipIcon() {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      className="h-4 w-4"
      aria-hidden="true"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M5 4l10 8-10 8V4z"
      />

      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M19 4v16"
      />
    </svg>
  );
}

/**
 * Icon displayed by the Restart control.
 *
 * @returns Restart icon SVG.
 */
export function RestartIcon() {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      className="h-4 w-4"
      aria-hidden="true"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M20 11a8.1 8.1 0 00-15.5-2M4 5v4h4"
      />

      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M4 13a8.1 8.1 0 0015.5 2M20 19v-4h-4"
      />
    </svg>
  );
}

/**
 * Icon displayed by the Stop control.
 *
 * @returns Stop icon SVG.
 */
export function StopIcon() {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="currentColor"
      className="h-4 w-4"
      aria-hidden="true"
    >
      <rect x="6" y="6" width="12" height="12" rx="1" />
    </svg>
  );
}
