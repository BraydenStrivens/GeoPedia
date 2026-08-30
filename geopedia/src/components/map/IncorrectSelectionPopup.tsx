/**
 * Displays temporary answer feedback above a selected geographic feature.
 *
 * The popup supports the same text and image content used by Show Answers
 * labels so image-based quizzes such as Country Flags retain the same compact
 * visual presentation.
 */

import Image from "next/image";

import type { IncorrectSelection } from "@/maps/types";

type IncorrectSelectionPopupProps = {
  /** Temporary selected-feature feedback, or null when hidden. */
  selection: IncorrectSelection | null;
};

/**
 * Renders temporary answer feedback at the map click position.
 *
 * @param props - Popup state.
 * @param props.selection - Selected feature's answer content and screen position.
 * @returns Temporary answer label, or null when no feedback is active.
 */
export default function IncorrectSelectionPopup({
  selection,
}: IncorrectSelectionPopupProps) {
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
        "border-gray-300",
        "bg-gray-300",
        "font-semibold",
        "text-gray-900",
        "shadow-sm",

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
          className="block h-auto max-h-8 w-auto max-w-14 object-contain"
        />
      ))}

      {content.label && <span>{content.label}</span>}
    </div>
  );
}
