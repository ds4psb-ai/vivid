import { redirect } from "next/navigation";

/**
 * Video Maker (VEO) - Redirects to Production
 * Legacy route: /dimension/video-maker
 * New route: /production?step=veo
 */
export default function VideoMakerPage() {
  redirect("/production?step=veo");
}
