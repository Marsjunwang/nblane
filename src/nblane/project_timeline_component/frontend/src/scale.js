// Pure timeline scale helpers: date parsing, domain, adaptive ticks.
// No DOM, no React -- unit-tested with `node --test`.

const DAY_MS = 24 * 60 * 60 * 1000;

export function parseISO(value) {
  const text = String(value || "").trim();
  const match = /^(\d{4})-(\d{2})-(\d{2})/.exec(text);
  if (!match) return null;
  const ms = Date.UTC(Number(match[1]), Number(match[2]) - 1, Number(match[3]));
  return Number.isNaN(ms) ? null : ms;
}

export function toISO(ms) {
  const d = new Date(ms);
  const y = d.getUTCFullYear();
  const m = String(d.getUTCMonth() + 1).padStart(2, "0");
  const day = String(d.getUTCDate()).padStart(2, "0");
  return `${y}-${m}-${day}`;
}

// Collect min/max ms from a list of ISO date strings (ignoring unparseable).
export function dateExtent(isoDates) {
  let lo = null;
  let hi = null;
  for (const value of isoDates || []) {
    const ms = parseISO(value);
    if (ms == null) continue;
    if (lo == null || ms < lo) lo = ms;
    if (hi == null || ms > hi) hi = ms;
  }
  return { lo, hi };
}

// Build a padded [start,end] domain from points; falls back around `todayMs`.
export function buildDomain(isoDates, todayMs) {
  const { lo, hi } = dateExtent(isoDates);
  const today = todayMs == null ? Date.now() : todayMs;
  if (lo == null || hi == null) {
    // No points: show a ~3-month window centered on today.
    return { start: today - 45 * DAY_MS, end: today + 45 * DAY_MS };
  }
  let start = Math.min(lo, today);
  let end = Math.max(hi, today);
  if (start === end) {
    start -= 15 * DAY_MS;
    end += 15 * DAY_MS;
  }
  const pad = Math.max((end - start) * 0.06, 2 * DAY_MS);
  return { start: start - pad, end: end + pad };
}

// Pick a tick unit aiming for ~targetTicks intervals across the span.
export function pickUnit(spanMs, targetTicks = 5) {
  const days = spanMs / DAY_MS;
  const year = days / 365;
  const month = days / 30;
  const week = days / 7;
  if (year >= 2) return "year";
  if (month >= 2) return "month";
  if (week >= 2) return "week";
  return "day";
}

function startOfUnit(ms, unit) {
  const d = new Date(ms);
  if (unit === "year") return Date.UTC(d.getUTCFullYear(), 0, 1);
  if (unit === "month") return Date.UTC(d.getUTCFullYear(), d.getUTCMonth(), 1);
  // week: snap to Monday (UTC)
  if (unit === "week") {
    const dow = (d.getUTCDay() + 6) % 7; // Mon=0
    return Date.UTC(d.getUTCFullYear(), d.getUTCMonth(), d.getUTCDate() - dow);
  }
  return Date.UTC(d.getUTCFullYear(), d.getUTCMonth(), d.getUTCDate());
}

function addUnit(ms, unit, n) {
  const d = new Date(ms);
  if (unit === "year") return Date.UTC(d.getUTCFullYear() + n, d.getUTCMonth(), d.getUTCDate());
  if (unit === "month") return Date.UTC(d.getUTCFullYear(), d.getUTCMonth() + n, d.getUTCDate());
  if (unit === "week") return ms + n * 7 * DAY_MS;
  return ms + n * DAY_MS;
}

// Generate tick marks {ms,label} across [start,end] using an adaptive unit.
export function buildTicks(start, end, unit, lang = "en") {
  const ticks = [];
  if (end <= start) return ticks;
  let cursor = startOfUnit(start, unit);
  if (cursor < start) cursor = addUnit(cursor, unit, 1);
  let guard = 0;
  while (cursor <= end && guard < 240) {
    ticks.push({ ms: cursor, label: tickLabel(cursor, unit, lang) });
    cursor = addUnit(cursor, unit, 1);
    guard += 1;
  }
  // Thin out if too many: keep ~targetTicks.
  if (ticks.length > 8) {
    const stride = Math.ceil(ticks.length / 6);
    return ticks.filter((_, i) => i % stride === 0);
  }
  return ticks;
}

export function tickLabel(ms, unit, lang = "en") {
  const d = new Date(ms);
  const y = d.getUTCFullYear();
  const m = d.getUTCMonth() + 1;
  const day = d.getUTCDate();
  if (unit === "year") return String(y);
  if (unit === "month") {
    return lang === "zh" ? `${y}年${m}月` : `${y}-${String(m).padStart(2, "0")}`;
  }
  // week / day
  return lang === "zh"
    ? `${m}月${day}日`
    : `${String(m).padStart(2, "0")}-${String(day).padStart(2, "0")}`;
}

// Map a ms value to an x pixel within [padL, width-padR].
export function msToX(ms, start, end, width, padL, padR) {
  const usable = Math.max(1, width - padL - padR);
  const frac = end > start ? (ms - start) / (end - start) : 0;
  return padL + Math.min(1, Math.max(0, frac)) * usable;
}

// Inverse: x pixel -> ms.
export function xToMs(x, start, end, width, padL, padR) {
  const usable = Math.max(1, width - padL - padR);
  const frac = Math.min(1, Math.max(0, (x - padL) / usable));
  return start + frac * (end - start);
}

// Zoom [start,end] around anchorMs by factor (<1 zoom in, >1 zoom out).
export function zoomDomain(start, end, anchorMs, factor) {
  const left = (anchorMs - start) * factor;
  const right = (end - anchorMs) * factor;
  let ns = anchorMs - left;
  let ne = anchorMs + right;
  const minSpan = 3 * DAY_MS;
  if (ne - ns < minSpan) {
    const mid = (ns + ne) / 2;
    ns = mid - minSpan / 2;
    ne = mid + minSpan / 2;
  }
  return { start: ns, end: ne };
}

export const _DAY_MS = DAY_MS;
