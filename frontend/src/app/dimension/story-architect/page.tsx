import { redirect } from "next/navigation";

/**
 * Story Architect - Redirects to Story Engine
 * Legacy route: /dimension/story-architect
 * New route: /story-engine?step=story
 */
export default function StoryArchitectPage() {
  redirect("/story-engine?step=story");
}
