import { redirect } from "next/navigation";

/**
 * Abyss Mirror - Redirects to DNA Lab
 * Legacy route: /dimension/abyss
 * New route: /dna-lab?step=mirror
 */
export default function AbyssPage() {
  redirect("/dna-lab?step=mirror");
}
