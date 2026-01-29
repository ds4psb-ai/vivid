import { redirect } from "next/navigation";

/**
 * Suno - Redirects to Production
 * Legacy route: /dimension/suno
 * New route: /production?step=suno
 */
export default function SunoPage() {
  redirect("/production?step=suno");
}
