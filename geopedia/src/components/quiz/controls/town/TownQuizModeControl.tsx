/**
 * Renders the compact Normal / Hard mode selector used by GeoPedia town quizzes.
 *
 * Town quiz mode is intentionally exposed directly above the map rather than
 * being hidden inside a settings panel because mode is the only display setting
 * currently supported by town quizzes.
 *
 * The selector uses a shared animated background indicator that slides between
 * Normal and Hard, matching the segmented mode selector used by feature quiz
 * settings.
 *
 * Normal mode displays GeoPedia's custom labels and coordinate markers for the
 * towns included in the active quiz. Hard mode hides those labels and markers
 * so the player must recall each town's approximate location without town
 * placement assistance.
 *
 * Mode is transient React state and is intentionally not persisted to
 * localStorage.
 */

"use client";

/**
 * Display modes supported by town quizzes.
 */
export type TownQuizMode = "normal" | "hard";

/**
 * Props required by the town quiz mode selector.
 */
type TownQuizModeControlProps = {
  /** Currently selected town quiz mode. */
  mode: TownQuizMode;

  /** Updates the selected town quiz mode. */
  onModeChange: (mode: TownQuizMode) => void;
};

/**
 * Shared styling for each selectable mode.
 *
 * Both buttons occupy exactly half of the segmented control so the animated
 * selection indicator can move between two equal-width positions.
 */
const MODE_BUTTON_CLASSES = [
  "relative",
  "z-10",
  "w-20",
  "px-3",
  "py-1.5",
  "text-center",
  "text-sm",
  "font-semibold",
  "transition-colors",
  "duration-200",
].join(" ");

/**
 * Displays the animated Normal / Hard town quiz mode selector.
 */
export default function TownQuizModeControl({
  mode,
  onModeChange,
}: TownQuizModeControlProps) {
  return (
    <div className="pointer-events-auto">
      <div className="relative flex rounded-lg bg-white/50 p-1 shadow-sm backdrop-blur-md">
        {/* Sliding selected-mode background. */}
        <div
          aria-hidden="true"
          className={[
            "absolute",
            "bottom-1",
            "left-1",
            "top-1",
            "w-20",
            "rounded-md",
            "bg-white",
            "shadow-sm",
            "transition-transform",
            "duration-200",
            "ease-out",

            mode === "hard" ? "translate-x-20" : "translate-x-0",
          ].join(" ")}
        />

        {/* Normal mode. */}
        <button
          type="button"
          aria-pressed={mode === "normal"}
          onClick={() => {
            onModeChange("normal");
          }}
          className={[
            MODE_BUTTON_CLASSES,

            mode === "normal"
              ? "text-gray-900"
              : "text-gray-600 hover:text-gray-900",
          ].join(" ")}
        >
          Normal
        </button>

        {/* Hard mode. */}
        <button
          type="button"
          aria-pressed={mode === "hard"}
          onClick={() => {
            onModeChange("hard");
          }}
          className={[
            MODE_BUTTON_CLASSES,

            mode === "hard"
              ? "text-gray-900"
              : "text-gray-600 hover:text-gray-900",
          ].join(" ")}
        >
          Hard
        </button>
      </div>
    </div>
  );
}
