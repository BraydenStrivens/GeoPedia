/**
 * Renders the content of a GeoPedia quiz question prompt.
 *
 * Question prompts currently support:
 *
 * - Text prompts, displayed directly as centered text.
 * - Image prompts, rendered through Next.js Image using the prompt's supplied
 *   image URL and alternative text.
 *
 * This component is presentation-only. It does not own quiz state or question
 * lifecycle behavior.
 */

"use client";

import Image from "next/image";

import type { QuizQuestionPrompt } from "@/types/quiz";

const DEFAULT_IMAGE_WIDTH = 224;
const DEFAULT_IMAGE_HEIGHT = 128;

/**
 * Props required by the shared quiz question display.
 */
type QuizQuestionDisplayProps = {
  /** Question prompt displayed to the user. */
  question: QuizQuestionPrompt;

  /** Multiplier applied to image-based question prompts. */
  imageSizeMultiplier?: number;
};

/**
 * Displays a quiz question using the presentation required by its prompt type.
 *
 * @param props - Quiz question display properties.
 * @returns Rendered text or image question content.
 */
export default function QuizQuestionDisplay({
  question,
  imageSizeMultiplier = 1,
}: QuizQuestionDisplayProps) {
  if (question.type === "image") {
    const width = DEFAULT_IMAGE_WIDTH * imageSizeMultiplier;
    const height = DEFAULT_IMAGE_HEIGHT * imageSizeMultiplier;

    return (
      <div className="flex items-center justify-center">
        <Image
          src={question.imageUrl}
          alt={question.alt}
          width={width}
          height={height}
          style={{
            maxWidth: width,
            maxHeight: height,
          }}
          className="object-contain"
        />
      </div>
    );
  }

  return <div className="text-center">{question.text}</div>;
}
