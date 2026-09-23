// Backward-compatible re-export: the visual tokens for the unified /projects
// page live in src/theme.ts (single source of truth since the 2026-09-23 dark
// unification). Keep importing from here or switch to ../../theme — both are
// the same object.
export { boardPalette } from '../../theme';
