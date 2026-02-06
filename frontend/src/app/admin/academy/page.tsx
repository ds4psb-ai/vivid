import { redirect } from "next/navigation";

/**
 * Admin Academy Page - Redirects to main page with admin tab
 *
 * 모든 관리 기능이 루트 페이지의 관리자 탭으로 통합되었습니다.
 */
export default function AdminAcademyPage() {
  redirect("/?tab=admin");
}
