import { redirect } from "next/navigation";

/**
 * System Prompt - Redirects to Story Engine
 * Legacy route: /dimension/prompt-translator
 * New route: /story-engine?step=system-prompt
 */
export default function PromptTranslatorPage() {
  redirect("/story-engine?step=system-prompt");
}
