"""Build MCP client config snippets for external agent runtimes.

External runtimes (OpenClaw, Cursor, Claude Desktop, …) connect to the
``nblane-mcp`` stdio server (see ``nblane.mcp_server``). This module renders
ready-to-merge config entries so users do not hand-write paths.
"""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

from nblane.core import paths


def resolve_mcp_server_command(
    executable: str | None = None,
) -> tuple[str, list[str]]:
    """Return ``(command, args)`` that launches the nblane MCP server."""
    if executable:
        return executable, []
    found = shutil.which("nblane-mcp")
    if found:
        return found, []
    return sys.executable, ["-m", "nblane.mcp_server"]


def _default_profile(root: Path) -> str | None:
    """Prefill the profile when exactly one exists under *root*."""
    try:
        from nblane.core.profile_io import list_profiles

        names = list_profiles()
    except Exception:
        return None
    if len(names) == 1:
        return names[0]
    return None


def build_mcp_server_entry(
    profile: str | None = None,
    *,
    root: Path | None = None,
    executable: str | None = None,
) -> dict:
    """Return one MCP stdio server entry (command/args/env) as a dict."""
    command, args = resolve_mcp_server_command(executable)
    repo_root = Path(root) if root is not None else paths.REPO_ROOT
    env = {"NBLANE_ROOT": str(repo_root)}
    chosen = profile or _default_profile(repo_root)
    if chosen:
        env["NBLANE_PROFILE"] = chosen
    entry: dict = {"command": command, "env": env}
    if args:
        # JSON convention: args after command; keep order command, args, env.
        entry = {"command": command, "args": args, "env": env}
    return entry


def _first_doc_line(description: object) -> str:
    """Return the first line of a description/docstring, or ``""``."""
    text = str(description or "").strip()
    if not text:
        return ""
    return text.splitlines()[0].strip()


def _mcp_inventory() -> tuple[list[tuple[str, str]], list[tuple[str, str]]] | None:
    """Introspect ``(resources, tools)`` from the live FastMCP registry.

    Each entry is ``(uri_or_name, first_doc_line)``. Returns ``None`` when the
    FastMCP SDK layout changes so the snippet degrades to a pointer at
    ``nblane.mcp_server`` instead of crashing.
    """
    try:
        from nblane.mcp_server import mcp

        tool_manager = getattr(mcp, "_tool_manager", None)
        resource_manager = getattr(mcp, "_resource_manager", None)
        if tool_manager is None or resource_manager is None:
            return None
        tools = [
            (str(tool.name), _first_doc_line(tool.description))
            for tool in tool_manager.list_tools()
        ]
        resources = [
            (str(res.uri), _first_doc_line(res.description))
            for res in resource_manager.list_resources()
        ]
        for template in resource_manager.list_templates():
            uri = getattr(template, "uri_template", None) or getattr(
                template, "uriTemplate", None
            )
            if uri is None:
                return None
            resources.append((str(uri), _first_doc_line(template.description)))
    except Exception:
        return None
    if not resources and not tools:
        return None
    return resources, tools


def _inventory_lines() -> list[str]:
    """Render the nblane-mcp resource/tool inventory for the snippet."""
    inventory = _mcp_inventory()
    if inventory is None:
        return [
            "- 资源与工具:无法自动内省,以 `src/nblane/mcp_server.py` 里的",
            "  `@mcp.resource` / `@mcp.tool` 注册项为准。",
        ]
    resources, tools = inventory
    lines = ["- 资源(自省自 `nblane.mcp_server`):"]
    lines.extend(
        f"  - `{uri}` — {desc}" if desc else f"  - `{uri}`"
        for uri, desc in resources
    )
    lines.append("- 工具:")
    lines.extend(
        f"  - `{name}` — {desc}" if desc else f"  - `{name}`"
        for name, desc in tools
    )
    return lines


def build_openclaw_mcp_snippet(
    profile: str | None = None,
    *,
    root: Path | None = None,
    executable: str | None = None,
) -> str:
    """Render a markdown snippet wiring ``nblane-mcp`` into OpenClaw."""
    entry = build_mcp_server_entry(profile, root=root, executable=executable)
    config = {"mcp": {"servers": {"nblane": entry}}}
    json_block = json.dumps(config, indent=2, ensure_ascii=False)
    has_profile = "NBLANE_PROFILE" in entry["env"]
    profile_note = (
        f"NBLANE_PROFILE 已预填为 `{entry['env']['NBLANE_PROFILE']}`。"
        if has_profile
        else "检测到多个 profile 或无法列出,请把 NBLANE_PROFILE 加进 env 并填上你的 profile 名。"
    )
    lines = [
        "# nblane → OpenClaw MCP 接入配置",
        "",
        "把下面这段合并进 `~/.openclaw/openclaw.json`(OpenClaw 官方托管",
        "`mcp.servers` 条目;也可以用 `openclaw mcp add` 交互式添加,参数以",
        "`openclaw mcp add --help` 为准):",
        "",
        "```json",
        json_block,
        "```",
        "",
        f"- {profile_note}",
        "- 可选环境变量:`NBLANE_CONTEXT_MODE`(chat|review|write|plan,默认 chat)、",
        "  `NBLANE_GAP_USE_LLM=1`(gap 分析启用 LLM 路由)。",
        "",
        "## 验证",
        "",
        "```bash",
        "openclaw mcp list            # 应能看到 nblane",
        "openclaw mcp probe nblane    # 应能列出 submit_agent_task_candidate 等工具",
        "```",
        "",
        "## 可用资源与工具(nblane-mcp)",
        "",
        *_inventory_lines(),
        "",
        "闭环约定:OpenClaw 是执行层,产出必须经 `submit_agent_task_candidate`",
        "进入 Agent Activity 审批队列,由人在 Web UI 处置——不要绕过审批直写。",
        "详见 docs/zh/guides/openclaw-integration.md。",
    ]
    return "\n".join(lines).rstrip() + "\n"


__all__ = [
    "build_mcp_server_entry",
    "build_openclaw_mcp_snippet",
    "resolve_mcp_server_command",
]
