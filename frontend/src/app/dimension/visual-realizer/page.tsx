import { redirect } from "next/navigation";

/**
 * Visual Realizer - Redirects to Production
 * Legacy route: /dimension/visual-realizer
 * New route: /production?step=veo
 */
export default function VisualRealizerPage() {
  redirect("/production?step=veo");
}
