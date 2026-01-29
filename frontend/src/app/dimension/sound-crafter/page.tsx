import { redirect } from "next/navigation";

/**
 * Sound Crafter - Redirects to Production
 * Legacy route: /dimension/sound-crafter
 * New route: /production?step=suno
 */
export default function SoundCrafterPage() {
  redirect("/production?step=suno");
}
