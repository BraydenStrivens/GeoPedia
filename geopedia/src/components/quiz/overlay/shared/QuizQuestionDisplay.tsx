"use client";

import Image from "next/image";

import type { QuizQuestionPrompt } from "@/types/quiz";

/**
 * Displays a quiz question prompt using the presentation required by its
 * prompt type.
 *
 * Text prompts are rendered directly, while image prompts use Next.js Image
 * with the supplied alternative text.
 *
 * @param props - Question-display properties.
 * @param props.question - Prompt displayed to the user.
 * @returns Rendered quiz question content.
 */
export default function QuizQuestionDisplay({
  question,
}: {
  question: QuizQuestionPrompt;
}) {
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
