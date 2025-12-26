const ADMIN_MODE = process.env.NEXT_PUBLIC_ADMIN_MODE || "";

const ADMIN_ALLOWLIST = new Set(["1", "true", "yes", "admin"]);

export const isAdminModeEnabled = () => ADMIN_ALLOWLIST.has(ADMIN_MODE.trim().toLowerCase());
