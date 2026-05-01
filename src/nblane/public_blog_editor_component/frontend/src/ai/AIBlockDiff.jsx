import React, { useMemo } from "react";
import DiffMatchPatch from "diff-match-patch";

function cleanText(value) {
  return value === null || value === undefined ? "" : String(value);
}

const dmp = new DiffMatchPatch();

export function AIBlockDiff({ before = "", after = "" }) {
  const rows = useMemo(() => {
    const left = cleanText(before);
    const right = cleanText(after);
    if (!left && !right) {
      return [];
    }
    const diffs = dmp.diff_main(left, right);
    dmp.diff_cleanupSemantic(diffs);
    return diffs.map(([op, text], index) => ({
      key: `${op}-${index}-${text.slice(0, 12)}`,
      op,
      text,
    }));
  }, [after, before]);

  if (!rows.length) {
    return null;
  }

  return (
    <div className="nb-ai-diff" aria-label="AI diff">
      {rows.map((row) => {
        const className =
          row.op > 0 ? "is-added" : row.op < 0 ? "is-removed" : "is-equal";
        return (
          <span className={className} key={row.key}>
            {row.text}
          </span>
        );
      })}
    </div>
  );
}

