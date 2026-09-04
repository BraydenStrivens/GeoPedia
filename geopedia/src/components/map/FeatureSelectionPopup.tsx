/**
 * Displays temporary answer feedback above a selected geographic feature.
 *
 * The popup is shared by multiple feature-map interactions:
 *
 * - During an active feature quiz, it can identify an incorrectly selected
 *   feature and use error-specific colors supplied by the parent.
 * - While a feature quiz is inactive, it can temporarily reveal the answer of
 *   a feature selected for inspection using the default neutral appearance.
 *
 * The popup supports the same text and image content used by Show Answers
 * labels so image-based quizzes such as Country Flags retain the same compact
 * visual presentation.
 *
 * Background and text colors can be overridden by the parent while neutral
 * semantic colors remain the default. This keeps the component independent
 * from the meaning of the interaction that caused the popup to appear.
 *
 * The component owns no map or quiz state. It receives the current temporary
 * selection and presentation overrides from its parent and renders nothing
 * when no feedback is active.
 */

import Image from "next/image";

import type { FeatureSelection } from "@/maps/types";

/**
 * Props required by the temporary feature-selection popup.
 */
type FeatureSelectionPopupProps = {
  /** Temporary selected-feature feedback, or null when hidden. */
  selection: FeatureSelection | null;

  /**
   * Optional background-color class overriding the popup's neutral background.
   *
   * This should contain a Tailwind background utility such as `bg-red-600`.
   */
  backgroundClassName?: string;

  /**
   * Optional text-color class overriding the popup's neutral text color.
   *
   * This should contain a Tailwind text utility such as `text-white`.
   */
  textClassName?: string;
};

/**
 * Renders temporary answer feedback at the selected map position.
 *
 * Text-only answers use a compact single-line presentation, while selections
 * containing images use a vertically stacked layout with smaller text.
 * Presentation colors default to GeoPedia's neutral semantic colors but can be
 * overridden by the parent when the popup represents a particular state such
 * as an incorrect answer.
 *
 * @param props - Feature-selection popup properties and color overrides.
 * @returns Temporary answer feedback, or null when no selection is active.
 */
export default function FeatureSelectionPopup({
  selection,
  backgroundClassName = "bg-background-1",
  textClassName = "text-text",
}: FeatureSelectionPopupProps) {
  if (!selection) {
    return null;
  }

  const { content, x, y } = selection;

  const hasImages = content.images.length > 0;

  return (
    <div
      className={[
        "pointer-events-none",
        "absolute",
        "z-40",
        "-translate-x-1/2",
        "-translate-y-full",
        "rounded-md",
        "border",
        "border-border",
        "font-semibold",
        "shadow-sm",
        backgroundClassName,
        textClassName,
        hasImages
          ? "flex flex-col items-center gap-0.5 px-1.5 py-1 text-[10px] leading-tight"
          : "whitespace-nowrap px-2 py-1 text-xs",
      ].join(" ")}
      style={{
        left: x,
        top: y - 8,
      }}
    >
      {content.images.map((image) => (
        <Image
          key={image.imageUrl}
          src={image.imageUrl}
          alt={image.alt}
          width={56}
          height={32}
          className="block h-auto max-h-8 w-auto max-w-14 border border-text object-contain"
        />
      ))}

      {content.label && <span>{content.label}</span>}
    </div>
  );
}
