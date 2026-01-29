import { redirect } from "next/navigation";

/**
 * Aesthetic Director - Redirects to DNA Lab
 * Legacy route: /dimension/aesthetic
 * New route: /dna-lab?step=ad
 */
export default function AestheticPage() {
  redirect("/dna-lab?step=ad");
}
