import { redirect } from "next/navigation";

/**
 * Creative Editor - Redirects to Production
 * Legacy route: /dimension/creative-editor
 * New route: /production?step=veo
 */
export default function CreativeEditorPage() {
  redirect("/production?step=veo");
}
