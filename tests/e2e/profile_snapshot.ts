import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";

import { e2eDataRoot } from "./helpers";

/**
 * Snapshot the sandbox profiles the suite writes into (default `dev`,
 * `王军`) before the run and restore them afterwards, so e2e residue
 * (e2e-chain-* evidence, 验收 posts, throwaway projects) never piles up in
 * the shared isolated data. Only touches `.dev-data` / `.dev-assets`:
 * other data roots are left alone unless NBLANE_E2E_RESTORE_ANY_ROOT=1.
 * NBLANE_E2E_KEEP_DATA=1 skips the restore (inspect residue after a run).
 */

const repoRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..", "..");
const stateFile = path.join(os.tmpdir(), "nblane-e2e-profile-snapshot.json");
// Same filesystem as the live dirs so restore is a pair of renames. Nothing
// is ever deleted: the run's residue is moved next to the snapshot.
const snapshotRoot = path.join(repoRoot, ".dev-data", ".e2e-snapshot");

interface SnapshotTarget {
  live: string;
  backup: string;
  residue: string;
  existed: boolean;
}

interface SnapshotState {
  dir: string;
  targets: SnapshotTarget[];
}

function profileNames(): string[] {
  const raw = process.env.NBLANE_E2E_RESTORE_PROFILES ?? "dev,王军";
  return raw.split(",").map((s) => s.trim()).filter((s) => s && !s.includes("/") && s !== "..");
}

function liveDirs(): string[] {
  const dataRoot = path.resolve(e2eDataRoot());
  const isolated = dataRoot === path.join(repoRoot, ".dev-data");
  if (!isolated && process.env.NBLANE_E2E_RESTORE_ANY_ROOT !== "1") return [];
  const assetRoot = path.join(isolated ? path.join(repoRoot, ".dev-assets") : dataRoot, "research", "profiles");
  return profileNames().flatMap((name) => [
    path.join(dataRoot, "profiles", name),
    path.join(assetRoot, name),
  ]);
}

// Keep the newest few runs for post-mortems (~60 MB each); older ones go.
const KEEP_SNAPSHOTS = 5;

function pruneOldSnapshots(): void {
  if (!fs.existsSync(snapshotRoot)) return;
  const runs = fs
    .readdirSync(snapshotRoot)
    .filter((n) => /^\d{4}-\d{2}-\d{2}T[\d-]+Z$/.test(n))
    .sort();
  for (const name of runs.slice(0, Math.max(0, runs.length - (KEEP_SNAPSHOTS - 1)))) {
    fs.rmSync(path.join(snapshotRoot, name), { recursive: true, force: true });
  }
}

/** Copy each live profile dir aside before the suite runs. */
export function snapshotProfiles(): void {
  const lives = liveDirs();
  if (!lives.length) return;
  pruneOldSnapshots();
  const stamp = new Date().toISOString().replace(/[:.]/g, "-");
  const dir = path.join(snapshotRoot, stamp);
  fs.mkdirSync(dir, { recursive: true });
  const targets = lives.map((live, i) => {
    const existed = fs.existsSync(live);
    const backup = path.join(dir, `backup-${i}`);
    if (existed) fs.cpSync(live, backup, { recursive: true, preserveTimestamps: true });
    return { live, backup, residue: path.join(dir, `residue-${i}`), existed };
  });
  fs.writeFileSync(stateFile, JSON.stringify({ dir, targets } satisfies SnapshotState, null, 2));
  console.log(`e2e: snapshot of ${targets.filter((t) => t.existed).length} dirs in ${dir}`);
}

/** Put the snapshot back; the run's residue moves into the snapshot dir. */
export function restoreProfiles(): void {
  if (!fs.existsSync(stateFile)) return;
  const state = JSON.parse(fs.readFileSync(stateFile, "utf-8")) as SnapshotState;
  fs.renameSync(stateFile, `${stateFile}.done`);
  if (process.env.NBLANE_E2E_KEEP_DATA === "1") {
    console.log(`e2e: NBLANE_E2E_KEEP_DATA=1, residue kept; snapshot stays in ${state.dir}`);
    return;
  }
  for (const t of state.targets) {
    if (fs.existsSync(t.live)) fs.renameSync(t.live, t.residue);
    if (t.existed) fs.renameSync(t.backup, t.live);
  }
  console.log(`e2e: restored sandbox profiles; run residue kept in ${state.dir}`);
}
