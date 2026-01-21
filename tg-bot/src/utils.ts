const DANGEROUS_PATH_PATTERNS = ["__proto__", "constructor", "prototype"];

export function setByPath(obj: any, path: string, value: any) {
  const parts = path.split(".").filter(Boolean);
  if (!parts.length) throw new Error("Empty path");
  
  // Validate path to prevent prototype pollution
  for (const part of parts) {
    if (DANGEROUS_PATH_PATTERNS.includes(part)) {
      throw new Error(`Invalid path component: ${part}`);
    }
  }
  
  let cur = obj;
  for (let i = 0; i < parts.length - 1; i++) {
    const k = parts[i];
    if (typeof cur[k] !== "object" || cur[k] === null) cur[k] = {};
    cur = cur[k];
  }
  cur[parts[parts.length - 1]] = value;
}

export function getByPath(obj: any, path: string): any {
  const parts = path.split(".").filter(Boolean);
  let cur = obj;
  for (const p of parts) {
    if (cur == null) return undefined;
    cur = cur[p];
  }
  return cur;
}

export function parseScalar(raw: string): any {
  const t = raw.trim();
  if (t === "true") return true;
  if (t === "false") return false;
  if (t === "null") return null;
  if (/^-?\d+(\.\d+)?$/.test(t)) return Number(t);
  if ((t.startsWith('"') && t.endsWith('"')) || (t.startsWith("'") && t.endsWith("'"))) return t.slice(1, -1);
  return t;
}

export function nowIso() {
  return new Date().toISOString();
}
