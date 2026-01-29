import { redirect } from "next/navigation";

/**
 * Character Consistency - Redirects to DNA Lab
 * Legacy route: /dimension/character-consistency
 * New route: /dna-lab?step=mirror
 */
export default function CharacterConsistencyPage() {
  redirect("/dna-lab?step=mirror");
}
