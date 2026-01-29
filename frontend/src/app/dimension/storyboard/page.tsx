import { redirect } from "next/navigation";

/**
 * Storyboard Sketch - Redirects to Story Engine
 * Legacy route: /dimension/storyboard
 * New route: /story-engine?step=story
 */
export default function StoryboardPage() {
  redirect("/story-engine?step=story");
}
