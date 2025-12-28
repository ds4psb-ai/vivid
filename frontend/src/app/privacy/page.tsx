import { redirect } from "next/navigation";

export default function PrivacyPage() {
  redirect("/crebit/terms?tab=privacy");
}
