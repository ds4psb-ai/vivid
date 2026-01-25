"use client";

/**
 * Crebit Home Page - Stitch V2 Cinematic AI OTT Experience
 *
 * Ultra-dark theme with neon accents
 * Split hero layout with character model card
 * Bento box variations grid
 */

import React, { Suspense } from "react";
import { CrebitNavbar } from "@/components/home/CrebitNavbar";
import { CinematicHero, FeaturedIP } from "@/components/home/CinematicHero";
import { VariationsGrid, VariationCard } from "@/components/home/VariationsGrid";
import { CrebitFooter } from "@/components/home/CrebitFooter";

// Featured IP data - Stitch V2 design
const FEATURED_IP: FeaturedIP = {
  slug: "neon-horizon",
  title: "NEON",
  titleAccent: "HORIZON",
  description:
    "In a city that never sleeps, a rogue AI begins to dream. Uncover the synthetic truth before your memory is erased.",
  bannerUrl:
    "https://lh3.googleusercontent.com/aida-public/AB6AXuDh2e3UoFCS76v_Zznn9MxmBvQaJyklYFDZbBaI6UWaLtBrvkSxVQOSfTDbNVaX0cJij8j99B6IkOH0_MLfMlraZlyPRnRaY35g62p2Fe3R-yGq81_vnAl8ApHAzCfA3X79StAD67u-A4-DR_a7qo79v8QqKabI5tSUDJOkrj3ar1DGf6NekiqYpIm1BRm9w-yJGN3id3hoUa69Gg5AfkthMK_sMISLHxIrIsXNKIn0RZbHYaG5XLjO7cA22Oe0bJx8HDku_VFzYNg",
  tags: ["Season 1", "2042"],
  rating: 4.9,
  remixCount: "12K",
  matchPercent: 98,
  character: {
    name: "Kael-09",
    description: "Cybernetic protagonist. Fully rigged for animation and style transfer.",
    status: "Character Model Ready",
  },
};

// Variation cards data - Bento box layout with Crebit dimension mapping
const VARIATION_CARDS: VariationCard[] = [
  {
    id: "anime-adaptation",
    name: "Anime Adaptation",
    description:
      "Reimagine the gritty streets as a high-octane anime series with vibrant color palettes.",
    thumbnailUrl:
      "https://lh3.googleusercontent.com/aida-public/AB6AXuA0r2qo4L4VmyuCId41jiXkjFCO1haV7IDSbJhzCT6sPC8I6bFdZoQ5VQLPEsgaDpW2JOJCpwKmN0UJA_6nPVGcahgFpfO173A6v14e7C8XM8-kEdxrM6gZ-TZS4TQt2a7UMte3lDWQcJqLmkD6ngyZQavT8o6TPkBBqKrIbGYOHcD-TeIJ9TEVzGHA_xBxbmGL_EG2quNe5YDycI_3U9pBrWvnSqZuWgsBM8fwrFmuTEI8Fx6RlNSom13VC6oaPwi8ZZK8ku4Ccpg",
    category: "visual",
    badge: "VISUAL STYLE",
    badgeColor: "bg-violet-600",
    href: "/dimension/visual-realizer",
    layout: "tall",
  },
  {
    id: "shortform-drama",
    name: "Short-form Drama",
    description:
      "Punchy 60-second vertical episodes optimized for viral social platforms.",
    thumbnailUrl:
      "https://lh3.googleusercontent.com/aida-public/AB6AXuB2tBApxBE_y5JRz_79of0LwA_koCjfEHgjOyoZf-2CVrADOm8_JKbNcctgPyf3UtxEJKmBaw3uTQvbxKjduBeL0Z6Mz43TAIAVzOd_qDFhow4m2v6SmhINvJX-47fh4Wvc0_ZBjZnIz-A5jf3Yz3eLMG3bnGw7hbkSBM-RFY59uxEaghM_I1l9Oio_CN263M4wqBXOMEWca2FWIo6VKIj-c_qJbdRoougP0LQ7Imc2xIedTOaaDUzBOsI4rYWLAlrzNUFGovWrQrM",
    category: "video",
    badge: "FORMAT",
    badgeColor: "bg-blue-600",
    href: "/dimension/video-maker",
    layout: "wide",
  },
  {
    id: "interactive-game",
    name: "Interactive Game",
    description:
      "Create a branching narrative game where users can choose different paths.",
    thumbnailUrl:
      "https://lh3.googleusercontent.com/aida-public/AB6AXuCcUjKInzOtfp5cZifxh65zNNJgO0SHc3gwqrIYN83WKGibsUZxOuzS646dMw8NQYrVJeCY1iUbp-olKPlBnzlfuii2pTXStRq2-9HMGivbpfRQ92rETfQeRL5vi3w0FkA2S5g2YfjHun1F0FkcMduJY9ISG_0m7AlaTpvfn0gc_ZMn499FAUEJ1XDT_kO4H2vherED8sacBwgnPUgDFlSzUu9prPIj7Gb9-kg6tw7Jmurqtbu4lWihBv93ivATNMC135caqdvH25M",
    category: "interactive",
    href: "/dimension/scenario-generator",
    layout: "normal",
  },
  {
    id: "graphic-novel",
    name: "Graphic Novel",
    description:
      "Generate a full-color graphic novel layout with consistent character art panels.",
    thumbnailUrl:
      "https://lh3.googleusercontent.com/aida-public/AB6AXuAEjDABfWSOWoCE8z39Uf9HewzfInWI575WbW6482O4KXOTY4J6Ybhkw-yssBuKTYCIYzZP8WeUtfvQCCnfp6z7jPJblSnyIDsDGoKMtm5csZjfOkyHQr2dG_Aywxj49Dpp_f_mgb98_I5E7DTFWKX7nLFa6FH_9VYSadkBwZ0IuCNBxjWETlsCn_GrcELcuXzy3OTzT1XvbBgvCiYe9l_gSJ8GMJ2foRZh3pI6Fb5CQ5jzeWBLShpIKNYekf2x4rWV60GtVQS9yIA",
    category: "story",
    href: "/dimension/storyboard-sketcher",
    layout: "normal",
  },
  {
    id: "3d-audio",
    name: "3D Audio",
    description:
      "Convert the script into a 3D binaural audio drama with AI voice actors.",
    thumbnailUrl:
      "https://lh3.googleusercontent.com/aida-public/AB6AXuCYZPJFPKgMSdKVU_W3iR-uzF7kSGHOsv3rhcmwdb-TRfrnJZIib_FptEDLGD6MwCRe1cIbPOoWkZhcr54lZc3bateyYL9vgzf-IudGmZv4aTceiquaSXjj8FzpR3pqqtDtPw303Kvoz__-yP3u2u3rNK2Do3dNfBPCNwlZR16hSrXOSx9VcIJJE56EUiMs1T4mJ9TDj8fQBdgLeB9MPSIbRsxzHRfZnYpzlwjn-c6q-9R2Qr8O5ncDux8qhYXzRKSiUmdtDz6RWUk",
    category: "audio",
    href: "/dimension/sound-crafter",
    layout: "normal",
  },
];

function HomePageContent() {
  return (
    <div className="min-h-screen bg-[#030014] text-gray-100 font-sans">
      {/* Navigation */}
      <CrebitNavbar />

      {/* Main Content */}
      <main className="relative">
        {/* Cinematic Hero */}
        <CinematicHero featured={FEATURED_IP} />

        {/* Variations Grid */}
        <VariationsGrid variations={VARIATION_CARDS} />
      </main>

      {/* Footer */}
      <CrebitFooter />
    </div>
  );
}

export default function HomePage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen flex items-center justify-center bg-[#030014]">
          <div className="flex flex-col items-center gap-4">
            <div className="w-10 h-10 bg-white text-[#030014] font-display font-bold text-xl flex items-center justify-center rounded-sm animate-pulse">
              C
            </div>
            <div className="h-1 w-24 bg-gray-800 rounded-full overflow-hidden">
              <div className="h-full w-1/2 bg-violet-500 rounded-full animate-pulse" />
            </div>
          </div>
        </div>
      }
    >
      <HomePageContent />
    </Suspense>
  );
}
