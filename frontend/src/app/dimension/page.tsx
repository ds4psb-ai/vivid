import { redirect } from "next/navigation";

/**
 * Dimension Hub - Redirects to DNA Lab
 *
 * Legacy route: /dimension
 * New route: /dna-lab (start of workflow)
 *
 * Migration (2026.01): All dimension apps are now consolidated
 * into 3 MegaApps. The workflow starts at DNA Lab.
 */
export default function DimensionHubPage() {
  redirect("/dna-lab");
}
