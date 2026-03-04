export function getAdminKey(): string | null {
  if (typeof window === "undefined") return null;
  let key = localStorage.getItem("openpango_admin_key");
  if (!key) {
    key = prompt("Admin Action Required\n\nPlease enter the pool operator secret key to perform this action:");
    if (key) {
      localStorage.setItem("openpango_admin_key", key);
    }
  }
  return key;
}

export function clearAdminKey() {
  if (typeof window !== "undefined") {
    localStorage.removeItem("openpango_admin_key");
  }
}
