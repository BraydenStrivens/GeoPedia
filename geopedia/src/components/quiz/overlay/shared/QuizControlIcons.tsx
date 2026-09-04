/**
 * Contains the small SVG icons used by GeoPedia's quiz lifecycle controls.
 *
 * Skip, Restart, and Stop icons are presentation-only and intentionally contain
 * no quiz state or interaction logic. Their color is inherited from the parent
 * control through `currentColor`, allowing shared quiz control styling to
 * determine both the normal and hover icon colors.
 */

/**
 * Renders the icon displayed by the Skip quiz control.
 *
 * @returns Skip icon SVG inheriting its stroke color from the parent control.
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
 * Renders the icon displayed by the Restart quiz control.
 *
 * @returns Restart icon SVG inheriting its stroke color from the parent control.
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
 * Renders the icon displayed by the Stop quiz control.
 *
 * @returns Stop icon SVG inheriting its fill color from the parent control.
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
