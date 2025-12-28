const ADMIN_MODE = process.env.NEXT_PUBLIC_ADMIN_MODE || "";

const ADMIN_ALLOWLIST = new Set(["1", "true", "yes", "admin"]);
const ROLE_ALLOWLIST = new Set(["admin", "master"]);
const IS_PRODUCTION = process.env.NODE_ENV === "production";

export const isAdminModeEnabled = (role?: string | null) => {
  if (role && ROLE_ALLOWLIST.has(role.trim().toLowerCase())) {
    return true;
  }
  if (IS_PRODUCTION) {
    return false;
  }
  return ADMIN_ALLOWLIST.has(ADMIN_MODE.trim().toLowerCase());
};
