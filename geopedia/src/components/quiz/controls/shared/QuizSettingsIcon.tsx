/**
 * Contains the shared Settings icon used by GeoPedia's floating quiz panel
 * controls.
 *
 * Feature and town quizzes both provide a Settings panel toggle using the same
 * gear-shaped SVG. Centralizing the icon avoids duplicating the SVG markup
 * while keeping the icon independent from panel state and interaction logic.
 *
 * The icon inherits its color from the parent control through `currentColor`,
 * allowing `QuizTogglePanelButton` to determine its appearance.
 */

/**
 * Renders the gear icon used by quiz Settings panel controls.
 *
 * @returns Settings gear SVG inheriting its stroke color from the parent.
 */
export default function QuizSettingsIcon() {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      className="h-5 w-5"
      aria-hidden="true"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M9.594 3.94c.09-.542.56-.94 1.11-.94h2.592c.55 0 1.02.398 1.11.94l.213 1.279c.063.379.313.696.645.889.09.052.18.107.268.164.325.21.72.275 1.082.139l1.223-.46a1.125 1.125 0 0 1 1.37.49l1.296 2.244a1.125 1.125 0 0 1-.26 1.431l-1.003.827a1.125 1.125 0 0 0-.38.95v.31c0 .374.137.735.38.95l1.003.827c.424.35.534.956.26 1.431l-1.296 2.244a1.125 1.125 0 0 1-1.37.49l-1.223-.46a1.125 1.125 0 0 0-1.082.139c-.088.057-.178.112-.268.164a1.125 1.125 0 0 0-.645.889l-.213 1.279c-.09.542-.56.94-1.11.94h-2.592c-.55 0-1.02-.398-1.11-.94l-.213-1.279a1.125 1.125 0 0 0-.645-.889 8.09 8.09 0 0 1-.268-.164 1.125 1.125 0 0 0-1.082-.139l-1.223.46a1.125 1.125 0 0 1-1.37-.49L3.447 15.3a1.125 1.125 0 0 1 .26-1.431l1.003-.827c.243-.2.38-.576.38-.95v-.31c0-.374-.137-.735-.38-.95l-1.003-.827a1.125 1.125 0 0 1-.26-1.431L4.743 6.33a1.125 1.125 0 0 1 1.37-.49l1.223.46c.362.136.757.071 1.082-.139.088-.057.178-.112.268-.164a1.125 1.125 0 0 0 .645-.889l.213-1.279Z"
      />

      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M15 12a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z"
      />
    </svg>
  );
}
