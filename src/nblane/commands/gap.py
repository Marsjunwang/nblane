"""Gap-analysis CLI command."""

from __future__ import annotations

import sys

from nblane.commands.common import _require_profile


def cmd_gap(
    name: str,
    task: str,
    node: str | None,
    *,
    use_llm_router: bool = False,
    use_rule_match: bool = True,
) -> None:
    """Run gap analysis."""
    _require_profile(name)
    from nblane.core.gap import analyze, format_text

    result = analyze(
        name,
        task,
        explicit_node=node,
        use_llm_router=use_llm_router,
        use_rule_match=use_rule_match,
    )
    print(format_text(result))
    if result.error:
        sys.exit(1)
