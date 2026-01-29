import { redirect } from "next/navigation";

/**
 * Quality Director - Redirects to DNA Lab
 * Legacy route: /dimension/quality-check
 * New route: /dna-lab?step=qc
 */
export default function QualityCheckPage() {
  redirect("/dna-lab?step=qc");
}
