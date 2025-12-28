import { redirect } from "next/navigation";

export default function TermsPage() {
  redirect("/crebit/terms?tab=terms");
}
