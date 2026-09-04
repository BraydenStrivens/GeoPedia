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

/**
 * Props required by the shared quiz question display.
 */
type QuizQuestionDisplayProps = {
  /** Question prompt displayed to the user. */
  question: QuizQuestionPrompt;
};

/**
 * Displays a quiz question using the presentation required by its prompt type.
 *
 * @param props - Quiz question display properties.
 * @returns Rendered text or image question content.
 */
export default function QuizQuestionDisplay({
  question,
}: QuizQuestionDisplayProps) {
  if (question.type === "image") {
    return (
      <div className="flex items-center justify-center">
        <Image
          src={question.imageUrl}
          alt={question.alt}
          width={224}
          height={128}
          className="max-h-32 max-w-56 object-contain"
        />
      </div>
    );
  }

  return <div className="text-center">{question.text}</div>;
}
