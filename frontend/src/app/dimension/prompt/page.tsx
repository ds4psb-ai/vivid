import { redirect } from "next/navigation";

/**
 * Prompt Alchemy - Redirects to Story Engine
 * Legacy route: /dimension/prompt
 * New route: /story-engine?step=prompt
 */
export default function PromptPage() {
  redirect("/story-engine?step=prompt");
}
