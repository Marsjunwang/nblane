// Separate entries keep two open editors from overwriting each other's backup.
export interface CareerLocalDraft<T> {
  value: T;
  etag: string;
  savedAt: number;
}

export interface StoredCareerDraft<T> extends CareerLocalDraft<T> {
  key: string;
  raw: string;
}

function prefix(document: string): string {
  return `nblane.career.localDraft:${encodeURIComponent(document)}:`;
}

export function careerDraftKey(document: string): string {
  const id = crypto.randomUUID?.() ?? Array.from(crypto.getRandomValues(new Uint32Array(4)), (part) => part.toString(16)).join('-');
  return `${prefix(document)}${id}`;
}

/** Only restore the shape written by this editor, not malformed local data. */
function compatible(value: unknown, initial: unknown): boolean {
  if (initial === null) return true;
  if (Array.isArray(initial)) return Array.isArray(value);
  if (typeof initial === 'object') {
    return value !== null && typeof value === 'object' && !Array.isArray(value)
      && Object.entries(initial).every(([key, field]) => key in value && compatible((value as Record<string, unknown>)[key], field));
  }
  return typeof value === typeof initial;
}

export function readCareerDraft<T>(document: string, initial: T): StoredCareerDraft<T> | null {
  try {
    const storage = window.localStorage;
    let newest: StoredCareerDraft<T> | null = null;
    const keys = Array.from({ length: storage.length }, (_, index) => storage.key(index));
    for (const key of keys) {
      if (!key?.startsWith(prefix(document))) continue;
      const raw = storage.getItem(key);
      if (!raw) continue;
      let item: CareerLocalDraft<T>;
      try { item = JSON.parse(raw) as CareerLocalDraft<T>; } catch { continue; }
      if (!item || typeof item.etag !== 'string' || !Number.isFinite(item.savedAt) || !compatible(item.value, initial)) continue;
      // An exit save may already have reached the server without its response
      // reaching the old page. No recovery or conflict is needed in that case.
      if (JSON.stringify(item.value) === JSON.stringify(initial)) {
        clearCareerDraft(key, raw);
        continue;
      }
      if (!newest || item.savedAt > newest.savedAt) newest = { ...item, key, raw };
    }
    return newest;
  } catch {
    return null;
  }
}

export function writeCareerDraft<T>(key: string, value: T, etag: string): string | null {
  try {
    const raw = JSON.stringify({ value, etag, savedAt: Date.now() } satisfies CareerLocalDraft<T>);
    window.localStorage.setItem(key, raw);
    return raw;
  } catch {
    return null;
  }
}

/** A delayed acknowledgement must not delete a newer backup from another tab. */
export function clearCareerDraft(key: string, raw: string | null): void {
  try {
    if (raw && window.localStorage.getItem(key) === raw) window.localStorage.removeItem(key);
  } catch {
    // Storage can be disabled; normal saving still works.
  }
}
