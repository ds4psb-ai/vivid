import { redirect } from "next/navigation";

/**
 * Kling - Redirects to Production
 * Legacy route: /dimension/kling
 * New route: /production?step=kling
 */
export default function KlingPage() {
  redirect("/production?step=kling");
}
