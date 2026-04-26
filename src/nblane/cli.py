"""nblane -- CLI entry point.

Commands:
    nblane init <name>              Create a new profile
    nblane context <name> [--mode | --chat | --review | ...]
                                    Print agent system prompt
    nblane status [name]            Show skill tree summary
    nblane log <name> <event>       Append growth log entry
    nblane sync <name> [--check|--write]
                                    Sync generated sections
    nblane validate [name]          Validate skill-tree
    nblane gap <name> [task]        Task -> skills / gaps
    nblane team <team_id>           Show team summary
    nblane evidence <name> <skill_id> add --type <t> --title <t>
                                    Append inline evidence on a node
    nblane evidence <name> pool add --type <t> --title <t>
                                    Create a pool record (shared id)
    nblane evidence <name> pool remove <evidence_id> [--prune-refs]
                                    Remove a pool row (see docs/evidence.md)
    nblane evidence <name> pool deprecate <evidence_id> [--replaced-by ID]
                                    Mark pool row deprecated (soft retire)
    nblane evidence <name> link <skill_id> <evidence_id>
                                    Attach pool id to a node
    nblane evidence <name> unlink <skill_id> <evidence_id>
                                    Remove pool id from that node's refs
    nblane ingest-resume <name> --file path | --stdin
                                    Resume text → pool + tree (LLM)
    nblane ingest-kanban <name>     Done column → pool + tree (LLM)
    nblane health [name]            Profile health / growth review
    nblane public init <name>       Initialize public site layer
    nblane public build <name>      Build static public site
    nblane auth hash-password       Generate a password hash for Web auth

Examples:
    nblane init alice
    nblane context alice
    nblane context alice --mode review
    nblane context alice --review
    nblane status
    nblane log alice "finished first manipulation demo"
    nblane sync alice --check
    nblane validate
    nblane gap alice "VLM robot control"
    nblane team example-team
    nblane evidence alice ros2_basics add \\
        --type project --title "Bringup demo"
    nblane evidence alice pool add --type project --title "Demo"
    nblane evidence alice pool remove 20260322_demo --prune-refs
    nblane evidence alice unlink ros2_basics 20260322_demo
    nblane evidence alice link ros2_basics 20260322_demo
"""

from __future__ import annotations

import argparse
import getpass
import sys
from pathlib import Path

from nblane.core.auth import DEFAULT_ITERATIONS, hash_password
from nblane.commands.evidence import cmd_evidence_dispatch
from nblane.commands.gap import cmd_gap
from nblane.commands.health import cmd_health
from nblane.commands.ingest import (
    cmd_ingest_kanban,
    cmd_ingest_resume,
)
from nblane.commands.integration import (
    cmd_crystallize,
    cmd_sync_cursor,
)
from nblane.commands.profile import (
    cmd_context,
    cmd_init,
    cmd_log,
    cmd_status,
    cmd_sync,
    cmd_validate,
)
from nblane.commands.public import (
    cmd_public_build,
    cmd_public_blog_list,
    cmd_public_blog_media,
    cmd_public_blog_new,
    cmd_public_blog_publish,
    cmd_public_draft_blog,
    cmd_public_draft_project_update,
    cmd_public_draft_resume,
    cmd_public_group,
    cmd_public_hydrate,
    cmd_public_init,
    cmd_public_resume,
    cmd_public_suggest_groups,
    cmd_public_validate,
)
from nblane.commands.team import cmd_team


# -- main -------------------------------------------------------------------


def main() -> None:
    """Parse arguments and dispatch to command handlers."""
    parser = argparse.ArgumentParser(
        prog="nblane",
        description=(
            "nblane — track the path to becoming "
            "a domain expert."
        ),
    )
    sub = parser.add_subparsers(
        dest="command", required=True
    )

    p_init = sub.add_parser(
        "init", help="Create a new profile"
    )
    p_init.add_argument(
        "name",
        help="Profile name (e.g. your GitHub handle)",
    )

    p_ctx = sub.add_parser(
        "context",
        help="Generate agent system prompt from a profile",
        epilog=(
            "Mode shortcuts: --chat, --review, --write, --plan "
            "(equivalent to --mode <name>). Default is chat."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p_ctx.add_argument("name", help="Profile name")
    ctx_mode = p_ctx.add_mutually_exclusive_group()
    ctx_mode.add_argument(
        "--mode",
        choices=["chat", "review", "write", "plan"],
        dest="context_mode",
        help="Prompt mode (default: chat)",
    )
    for _mode in ("chat", "review", "write", "plan"):
        ctx_mode.add_argument(
            f"--{_mode}",
            action="store_const",
            const=_mode,
            dest="context_mode",
            help=argparse.SUPPRESS,
        )
    p_ctx.add_argument(
        "--no-kanban",
        action="store_true",
        help="Exclude kanban.md from the prompt",
    )

    p_status = sub.add_parser(
        "status", help="Show skill tree summary"
    )
    p_status.add_argument(
        "name", nargs="?", default=None
    )

    p_log = sub.add_parser(
        "log", help="Append entry to growth log"
    )
    p_log.add_argument("name", help="Profile name")
    p_log.add_argument(
        "event", help="What happened (quoted string)"
    )

    p_sync = sub.add_parser(
        "sync",
        help="Sync generated SKILL.md sections",
    )
    p_sync.add_argument("name", help="Profile name")
    mode_group = p_sync.add_mutually_exclusive_group(
        required=True
    )
    mode_group.add_argument(
        "--check",
        action="store_true",
        help="Check generated section drift only",
    )
    mode_group.add_argument(
        "--write",
        action="store_true",
        help="Rewrite generated sections in SKILL.md",
    )

    p_val = sub.add_parser(
        "validate",
        help="Validate skill-tree.yaml against schemas/",
    )
    p_val.add_argument(
        "name",
        nargs="?",
        default=None,
        help="Profile name (omit to validate all)",
    )

    p_gap = sub.add_parser(
        "gap",
        help="Match a task to skills and list gaps",
    )
    p_gap.add_argument("name", help="Profile name")
    p_gap.add_argument(
        "task",
        nargs="?",
        default="",
        help="Natural language task (optional if --node)",
    )
    p_gap.add_argument(
        "--node",
        dest="node",
        default=None,
        help="Target schema node id",
    )
    p_gap.add_argument(
        "--llm-router",
        action="store_true",
        help="Use LLM to suggest schema nodes (requires API key)",
    )
    p_gap.add_argument(
        "--no-rule",
        action="store_true",
        help="Disable rule-based keyword overlap",
    )

    p_team = sub.add_parser(
        "team",
        help="Show team.yaml and product-pool summary",
    )
    p_team.add_argument(
        "team_id",
        help="Directory name under teams/",
    )

    p_evidence = sub.add_parser(
        "evidence",
        help=(
            "Inline evidence, evidence pool, or link pool id "
            "to a skill"
        ),
    )
    p_evidence.add_argument("name", help="Profile name")
    p_evidence.add_argument(
        "tokens",
        nargs=argparse.REMAINDER,
        help=(
            "pool add|remove|deprecate | link | unlink | "
            "<skill_id> add …"
        ),
    )

    p_ing_res = sub.add_parser(
        "ingest-resume",
        help=(
            "Ingest resume or long text via LLM into "
            "evidence pool + skill tree"
        ),
    )
    p_ing_res.add_argument("name", help="Profile name")
    src = p_ing_res.add_mutually_exclusive_group(
        required=True
    )
    src.add_argument(
        "--file",
        dest="resume_file",
        metavar="PATH",
        help="Path to resume text file",
    )
    src.add_argument(
        "--stdin",
        action="store_true",
        help="Read resume text from stdin",
    )
    p_ing_res.add_argument(
        "--dry-run",
        action="store_true",
        help="Print merged YAML only; do not write",
    )
    p_ing_res.add_argument(
        "--allow-status-change",
        action="store_true",
        help="Apply status fields from the LLM patch",
    )
    p_ing_res.add_argument(
        "--no-bump-locked",
        action="store_true",
        help=(
            "Do not set learning on nodes that remain locked "
            "but have evidence"
        ),
    )

    p_ing_kan = sub.add_parser(
        "ingest-kanban",
        help=(
            "Ingest kanban Done tasks via LLM into "
            "evidence pool + skill tree"
        ),
    )
    p_ing_kan.add_argument("name", help="Profile name")
    p_ing_kan.add_argument(
        "--dry-run",
        action="store_true",
        help="Print merged YAML only; do not write",
    )
    p_ing_kan.add_argument(
        "--allow-status-change",
        action="store_true",
        help="Apply status fields from the LLM patch",
    )
    p_ing_kan.add_argument(
        "--no-bump-locked",
        action="store_true",
        help=(
            "Do not set learning on nodes that remain locked "
            "but have evidence"
        ),
    )

    p_health = sub.add_parser(
        "health",
        help="Show profile health / growth review",
    )
    p_health.add_argument(
        "name",
        nargs="?",
        default=None,
        help="Profile name (omit to scan all profiles)",
    )

    p_sync_cur = sub.add_parser(
        "sync-cursor",
        help=(
            "Write .cursor/rules/nblane-context.mdc from profile "
            "summary"
        ),
    )
    p_sync_cur.add_argument("name", help="Profile name")

    p_cryst = sub.add_parser(
        "crystallize",
        help="Write a method draft under profiles/<name>/methods/",
    )
    p_cryst.add_argument("name", help="Profile name")
    p_cryst.add_argument(
        "project",
        help="Project or session label (used in filename)",
    )
    p_cryst.add_argument(
        "--file",
        dest="crystallize_file",
        metavar="PATH",
        default=None,
        help="Read draft body from file (utf-8)",
    )
    p_cryst.add_argument(
        "--stdin",
        action="store_true",
        help="Read draft body from stdin",
    )

    p_public = sub.add_parser(
        "public",
        help="Public personal site, blog, and resume tools",
    )
    public_sub = p_public.add_subparsers(
        dest="public_command",
        required=True,
    )

    p_pub_init = public_sub.add_parser(
        "init",
        help="Create missing public-layer files for a profile",
    )
    p_pub_init.add_argument("name", help="Profile name")

    p_pub_validate = public_sub.add_parser(
        "validate",
        help="Validate public-profile, resume, projects, outputs, and blog",
    )
    p_pub_validate.add_argument("name", help="Profile name")
    p_pub_validate.add_argument(
        "--include-drafts",
        action="store_true",
        help="Also validate draft objects as publish candidates",
    )

    p_pub_build = public_sub.add_parser(
        "build",
        help="Build a static public site",
    )
    p_pub_build.add_argument("name", help="Profile name")
    p_pub_build.add_argument(
        "--out",
        dest="public_out",
        default=None,
        help="Output directory (default: dist/public/<profile>)",
    )
    p_pub_build.add_argument(
        "--include-drafts",
        action="store_true",
        help="Preview private/draft content in the generated site",
    )
    p_pub_build.add_argument(
        "--base-url",
        default="",
        help="Absolute site URL for sitemap entries",
    )

    p_pub_resume = public_sub.add_parser(
        "resume",
        help="Generate resume HTML and Markdown",
    )
    p_pub_resume.add_argument("name", help="Profile name")
    p_pub_resume.add_argument(
        "--out",
        dest="resume_out",
        default=None,
        help=(
            "HTML output path "
            "(default: profiles/<name>/resumes/generated/default.html)"
        ),
    )
    p_pub_resume.add_argument(
        "--target",
        default="",
        help="Optional target role or direction label",
    )

    p_pub_draft_blog = public_sub.add_parser(
        "draft-blog",
        help="Create a draft blog post from evidence or kanban Done",
    )
    p_pub_draft_blog.add_argument("name", help="Profile name")
    blog_src = p_pub_draft_blog.add_mutually_exclusive_group(
        required=True,
    )
    blog_src.add_argument(
        "--from-evidence",
        dest="draft_evidence_id",
        default=None,
        metavar="ID",
        help="Evidence id to turn into a draft post",
    )
    blog_src.add_argument(
        "--from-kanban-done",
        action="store_true",
        help="Turn current kanban Done tasks into a draft post",
    )

    p_pub_blog = public_sub.add_parser(
        "blog",
        help="Create, list, publish, and add media to blog posts",
    )
    pub_blog_sub = p_pub_blog.add_subparsers(
        dest="public_blog_command",
        required=True,
    )

    p_pub_blog_list = pub_blog_sub.add_parser(
        "list",
        help="List blog posts",
    )
    p_pub_blog_list.add_argument("name", help="Profile name")
    p_pub_blog_list.add_argument(
        "--include-drafts",
        action="store_true",
        help="Include draft posts",
    )

    p_pub_blog_new = pub_blog_sub.add_parser(
        "new",
        help="Create a new blog draft",
    )
    p_pub_blog_new.add_argument("name", help="Profile name")
    p_pub_blog_new.add_argument(
        "--title",
        required=True,
        help="Blog post title",
    )
    p_pub_blog_new.add_argument(
        "--slug",
        default=None,
        help="Optional blog slug",
    )
    p_pub_blog_new.add_argument(
        "--summary",
        default="",
        help="Optional summary",
    )
    p_pub_blog_new.add_argument(
        "--tag",
        action="append",
        default=[],
        dest="tags",
        help="Optional tag; repeat for multiple tags",
    )
    blog_body = p_pub_blog_new.add_mutually_exclusive_group()
    blog_body.add_argument(
        "--body-file",
        default=None,
        help="Read Markdown body from a UTF-8 file",
    )
    blog_body.add_argument(
        "--stdin",
        action="store_true",
        help="Read Markdown body from stdin",
    )

    p_pub_blog_media = pub_blog_sub.add_parser(
        "media",
        help="Copy media into media/blog/<slug>/",
    )
    p_pub_blog_media.add_argument("name", help="Profile name")
    p_pub_blog_media.add_argument("slug", help="Blog slug")
    p_pub_blog_media.add_argument(
        "--file",
        required=True,
        dest="blog_media_file",
        help="Image or short video file to copy",
    )
    p_pub_blog_media.add_argument(
        "--kind",
        required=True,
        choices=["image", "video"],
        help="Media kind",
    )
    p_pub_blog_media.add_argument(
        "--alt",
        default="",
        help="Image alt text",
    )
    p_pub_blog_media.add_argument(
        "--caption",
        default="",
        help="Video caption or image caption",
    )
    p_pub_blog_media.add_argument(
        "--cover",
        action="store_true",
        help="Use an image as the post cover",
    )
    p_pub_blog_media.add_argument(
        "--append",
        action="store_true",
        help="Append or marker-insert the snippet into the post body",
    )

    p_pub_blog_publish = pub_blog_sub.add_parser(
        "publish",
        help="Publish a blog post after validation",
    )
    p_pub_blog_publish.add_argument("name", help="Profile name")
    p_pub_blog_publish.add_argument("slug", help="Blog slug")

    p_pub_draft_resume = public_sub.add_parser(
        "draft-resume",
        help="Create a target-specific resume draft",
    )
    p_pub_draft_resume.add_argument("name", help="Profile name")
    p_pub_draft_resume.add_argument(
        "--target",
        required=True,
        help="Target role or direction",
    )

    p_pub_draft_update = public_sub.add_parser(
        "draft-project-update",
        help="Append a draft public update to a project",
    )
    p_pub_draft_update.add_argument("name", help="Profile name")
    p_pub_draft_update.add_argument(
        "--project",
        required=True,
        dest="project_id",
        help="Project id in projects.yaml",
    )

    p_pub_suggest = public_sub.add_parser(
        "suggest-groups",
        help="Preview deterministic evidence grouping suggestions",
    )
    p_pub_suggest.add_argument("name", help="Profile name")
    p_pub_suggest.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview only; suggestions never write files",
    )

    p_pub_group = public_sub.add_parser(
        "group",
        help="Create a draft public project from selected evidence",
    )
    p_pub_group.add_argument("name", help="Profile name")
    p_pub_group.add_argument(
        "--id",
        required=True,
        dest="project_id",
        help="New project id in projects.yaml",
    )
    p_pub_group.add_argument(
        "--title",
        required=True,
        help="Public draft project title",
    )
    p_pub_group.add_argument(
        "--evidence",
        action="append",
        required=True,
        dest="evidence_ids",
        metavar="ID",
        help="Evidence id to include; repeat for multiple refs",
    )
    p_pub_group.add_argument(
        "--summary",
        default="",
        help="Optional draft summary",
    )
    p_pub_group.add_argument(
        "--tag",
        action="append",
        default=[],
        dest="tags",
        help="Optional project tag; repeat for multiple tags",
    )

    p_pub_hydrate = public_sub.add_parser(
        "hydrate",
        help="Preview or write obvious paper/patent output drafts",
    )
    p_pub_hydrate.add_argument("name", help="Profile name")
    hydrate_mode = p_pub_hydrate.add_mutually_exclusive_group()
    hydrate_mode.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview output drafts without writing",
    )
    hydrate_mode.add_argument(
        "--write-drafts",
        action="store_true",
        help="Write draft outputs to outputs.yaml",
    )

    p_auth = sub.add_parser(
        "auth",
        help="Authentication helpers for the Streamlit Web UI",
    )
    auth_sub = p_auth.add_subparsers(
        dest="auth_command",
        required=True,
    )
    p_hash = auth_sub.add_parser(
        "hash-password",
        help="Generate a PBKDF2 password hash for auth/users.yaml",
    )
    p_hash.add_argument(
        "password",
        nargs="?",
        default=None,
        help="Password to hash; omit to enter it securely",
    )
    p_hash.add_argument(
        "--iterations",
        type=int,
        default=DEFAULT_ITERATIONS,
        help=f"PBKDF2 iterations (default: {DEFAULT_ITERATIONS})",
    )

    args = parser.parse_args()

    if args.command == "init":
        cmd_init(args.name)
    elif args.command == "context":
        ctx_mode = (
            args.context_mode
            if args.context_mode is not None
            else "chat"
        )
        cmd_context(args.name, ctx_mode, args.no_kanban)
    elif args.command == "status":
        cmd_status(args.name)
    elif args.command == "log":
        cmd_log(args.name, args.event)
    elif args.command == "sync":
        cmd_sync(args.name, args.check, args.write)
    elif args.command == "validate":
        cmd_validate(args.name)
    elif args.command == "gap":
        cmd_gap(
            args.name,
            args.task,
            args.node,
            use_llm_router=args.llm_router,
            use_rule_match=not args.no_rule,
        )
    elif args.command == "team":
        cmd_team(args.team_id)
    elif args.command == "evidence":
        cmd_evidence_dispatch(args.name, args.tokens)
    elif args.command == "ingest-resume":
        cmd_ingest_resume(
            args.name,
            file_path=args.resume_file,
            use_stdin=args.stdin,
            dry_run=args.dry_run,
            allow_status_change=args.allow_status_change,
            bump_locked_with_evidence=not args.no_bump_locked,
        )
    elif args.command == "ingest-kanban":
        cmd_ingest_kanban(
            args.name,
            dry_run=args.dry_run,
            allow_status_change=args.allow_status_change,
            bump_locked_with_evidence=not args.no_bump_locked,
        )
    elif args.command == "health":
        cmd_health(args.name)
    elif args.command == "sync-cursor":
        cmd_sync_cursor(args.name)
    elif args.command == "crystallize":
        if args.stdin:
            body = sys.stdin.read()
        elif args.crystallize_file:
            body = Path(
                args.crystallize_file
            ).read_text(encoding="utf-8")
        else:
            body = (
                "_Add playbook notes here. "
                "Re-run with --file or --stdin for content._\n"
            )
        cmd_crystallize(args.name, args.project, body)
    elif args.command == "public":
        if args.public_command == "init":
            cmd_public_init(args.name)
        elif args.public_command == "validate":
            cmd_public_validate(
                args.name,
                include_drafts=args.include_drafts,
            )
        elif args.public_command == "build":
            cmd_public_build(
                args.name,
                out_dir=args.public_out,
                include_drafts=args.include_drafts,
                base_url=args.base_url,
            )
        elif args.public_command == "resume":
            cmd_public_resume(
                args.name,
                out_path=args.resume_out,
                target=args.target,
            )
        elif args.public_command == "draft-blog":
            cmd_public_draft_blog(
                args.name,
                evidence_id=args.draft_evidence_id,
                from_kanban_done=args.from_kanban_done,
            )
        elif args.public_command == "blog":
            if args.public_blog_command == "list":
                cmd_public_blog_list(
                    args.name,
                    include_drafts=args.include_drafts,
                )
            elif args.public_blog_command == "new":
                cmd_public_blog_new(
                    args.name,
                    title=args.title,
                    slug=args.slug,
                    summary=args.summary,
                    tags=args.tags,
                    body_file=args.body_file,
                    use_stdin=args.stdin,
                )
            elif args.public_blog_command == "media":
                cmd_public_blog_media(
                    args.name,
                    slug=args.slug,
                    file_path=args.blog_media_file,
                    kind=args.kind,
                    alt=args.alt,
                    caption=args.caption,
                    cover=args.cover,
                    append=args.append,
                )
            elif args.public_blog_command == "publish":
                cmd_public_blog_publish(
                    args.name,
                    slug=args.slug,
                )
        elif args.public_command == "draft-resume":
            cmd_public_draft_resume(
                args.name,
                target=args.target,
            )
        elif args.public_command == "draft-project-update":
            cmd_public_draft_project_update(
                args.name,
                project_id=args.project_id,
            )
        elif args.public_command == "suggest-groups":
            cmd_public_suggest_groups(args.name)
        elif args.public_command == "group":
            cmd_public_group(
                args.name,
                project_id=args.project_id,
                title=args.title,
                evidence_ids=args.evidence_ids,
                summary=args.summary,
                tags=args.tags,
            )
        elif args.public_command == "hydrate":
            cmd_public_hydrate(
                args.name,
                write_drafts=args.write_drafts,
            )
    elif args.command == "auth":
        if args.auth_command == "hash-password":
            password = args.password
            if password is None:
                password = getpass.getpass("Password: ")
                again = getpass.getpass("Confirm password: ")
                if password != again:
                    raise SystemExit("passwords do not match")
            print(
                hash_password(
                    password,
                    iterations=args.iterations,
                )
            )


if __name__ == "__main__":
    main()
