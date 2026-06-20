import { test } from "node:test";
import assert from "node:assert/strict";
import {
  parseISO,
  toISO,
  dateExtent,
  buildDomain,
  pickUnit,
  buildTicks,
  msToX,
  xToMs,
  zoomDomain,
  _DAY_MS,
} from "./scale.js";

test("parseISO parses and rejects", () => {
  assert.equal(parseISO("2026-06-30"), Date.UTC(2026, 5, 30));
  assert.equal(parseISO("not-a-date"), null);
  assert.equal(parseISO(""), null);
});

test("toISO round-trips parseISO", () => {
  assert.equal(toISO(parseISO("2026-01-15")), "2026-01-15");
});

test("dateExtent ignores unparseable", () => {
  const { lo, hi } = dateExtent(["2026-03-01", "bad", "2026-01-01", "2026-05-01"]);
  assert.equal(toISO(lo), "2026-01-01");
  assert.equal(toISO(hi), "2026-05-01");
});

test("buildDomain falls back to window around today when no points", () => {
  const today = Date.UTC(2026, 5, 20);
  const { start, end } = buildDomain([], today);
  assert.ok(start < today && end > today);
});

test("buildDomain includes today and pads", () => {
  const today = Date.UTC(2026, 5, 20);
  const { start, end } = buildDomain(["2026-01-01", "2026-03-01"], today);
  assert.ok(start < Date.UTC(2026, 0, 1));
  assert.ok(end > today); // today is later than all points -> extends
});

test("pickUnit adapts to span", () => {
  assert.equal(pickUnit(900 * _DAY_MS), "year");
  assert.equal(pickUnit(120 * _DAY_MS), "month");
  assert.equal(pickUnit(20 * _DAY_MS), "week");
  assert.equal(pickUnit(5 * _DAY_MS), "day");
});

test("buildTicks yields a reasonable count and thins out", () => {
  const start = Date.UTC(2024, 0, 1);
  const end = Date.UTC(2026, 0, 1);
  const ticks = buildTicks(start, end, "year");
  assert.ok(ticks.length >= 2 && ticks.length <= 8);
  // monthly over 2 years would be 24 -> must be thinned
  const monthly = buildTicks(start, end, "month");
  assert.ok(monthly.length <= 8);
});

test("msToX / xToMs are inverse within domain", () => {
  const start = Date.UTC(2026, 0, 1);
  const end = Date.UTC(2026, 11, 31);
  const mid = (start + end) / 2;
  const x = msToX(mid, start, end, 800, 40, 40);
  const back = xToMs(x, start, end, 800, 40, 40);
  assert.ok(Math.abs(back - mid) < _DAY_MS); // within a day
});

test("zoomDomain shrinks around anchor and respects min span", () => {
  const start = Date.UTC(2026, 0, 1);
  const end = Date.UTC(2026, 11, 31);
  const anchor = (start + end) / 2;
  const zoomed = zoomDomain(start, end, anchor, 0.5);
  assert.ok(zoomed.end - zoomed.start < end - start);
  // extreme zoom clamps to min span
  const tiny = zoomDomain(start, end, anchor, 0.00001);
  assert.ok(tiny.end - tiny.start >= 3 * _DAY_MS - 1);
});
