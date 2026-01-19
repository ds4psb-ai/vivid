import type { Metadata } from "next";
import IPDetailClient from "./_components/IPDetailClient";

export const metadata: Metadata = {
  title: "IP Detail | Crebit",
  description: "View IP details and create AI fan-fiction videos",
};

export default function IPDetailPage({ params }: { params: { slug: string } }) {
  return <IPDetailClient slug={params.slug} />;
}
