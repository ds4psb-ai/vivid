/**
 * Main Page - Prompty Homepage
 *
 * prompty.co.kr 접속 시 Prompty 페이지 표시
 * 기존 Crebit 홈페이지는 page.crebit-backup.tsx에 백업
 */

import { PromptyNavbar } from "@/components/prompty/PromptyNavbar";
import PromptyHomePage from "@/components/prompty/PromptyHomePage";

export default function Home() {
  return (
    <>
      <PromptyNavbar />
      <PromptyHomePage />
    </>
  );
}
