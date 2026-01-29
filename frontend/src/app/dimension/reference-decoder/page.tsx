import { redirect } from "next/navigation";

/**
 * Reference Decoder (VPE) - Redirects to DNA Lab
 * Legacy route: /dimension/reference-decoder
 * New route: /dna-lab?step=vpe
 */
export default function ReferenceDecoderPage() {
  redirect("/dna-lab?step=vpe");
}
