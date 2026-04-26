"""CLI handlers for public personal site generation."""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

from nblane.commands.common import _require_profile
from nblane.core.public_curation import (
    group_project,
    hydrate_public_drafts,
    suggest_groups,
)
from nblane.core.public_site import (
    PublicSiteError,
    add_blog_media,
    build_public_site,
    create_blog_draft,
    draft_blog_from_evidence,
    draft_blog_from_kanban_done,
    draft_project_update,
    draft_resume_for_target,
    generate_resume_files,
    init_public_layer,
    load_blog_posts,
    publish_blog_post,
    validate_public_layer,
)


def _print_validation(
    errors: list[str],
    warnings: list[str],
) -> int:
    """Print validation diagnostics and return a process code."""
    for warning in warnings:
        print(f"WARN: {warning}")
    for error in errors:
        print(f"ERROR: {error}", file=sys.stderr)
    if errors:
        return 1
    print("Public layer validation passed.")
    return 0


def cmd_public_init(name: str) -> None:
    """Create missing public-layer files for a profile."""
    _require_profile(name)
    created = init_public_layer(name)
    if not created:
        print("Public layer already initialized.")
        return
    print("Created public-layer files:")
    for path in created:
        print(f"  {path}")


def cmd_public_validate(
    name: str,
    *,
    include_drafts: bool,
) -> None:
    """Validate a profile's public layer."""
    _require_profile(name)
    result = validate_public_layer(
        name,
        include_drafts=include_drafts,
    )
    sys.exit(_print_validation(result.errors, result.warnings))


def cmd_public_build(
    name: str,
    *,
    out_dir: str | None,
    include_drafts: bool,
    base_url: str,
) -> None:
    """Build the static public site."""
    _require_profile(name)
    try:
        result = build_public_site(
            name,
            out_dir=out_dir,
            include_drafts=include_drafts,
            base_url=base_url,
        )
    except PublicSiteError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
    print(f"Built public site: {result.output_dir}")
    print(f"Pages: {len(result.pages)}")


def cmd_public_resume(
    name: str,
    *,
    out_path: str | None,
    target: str,
) -> None:
    """Generate public resume HTML and Markdown."""
    _require_profile(name)
    html_path, md_path = generate_resume_files(
        name,
        out_path=out_path,
        target=target,
    )
    print(f"Generated resume HTML: {html_path}")
    print(f"Generated resume Markdown: {md_path}")


def cmd_public_draft_blog(
    name: str,
    *,
    evidence_id: str | None,
    from_kanban_done: bool,
) -> None:
    """Create a draft blog post."""
    _require_profile(name)
    try:
        if evidence_id:
            path = draft_blog_from_evidence(name, evidence_id)
        elif from_kanban_done:
            path = draft_blog_from_kanban_done(name)
        else:
            print(
                "ERROR: choose --from-evidence or --from-kanban-done",
                file=sys.stderr,
            )
            sys.exit(1)
    except PublicSiteError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
    print(f"Created blog draft: {path}")


def cmd_public_blog_list(
    name: str,
    *,
    include_drafts: bool,
) -> None:
    """List blog posts in the public layer."""
    _require_profile(name)
    posts = load_blog_posts(name, include_drafts=include_drafts)
    _print_yaml(
        {
            "posts": [
                {
                    "slug": post.slug,
                    "title": post.title,
                    "date": post.date,
                    "status": post.status,
                    "summary": post.summary,
                    "path": str(post.path),
                }
                for post in posts
            ]
        }
    )


def cmd_public_blog_new(
    name: str,
    *,
    title: str,
    slug: str | None,
    summary: str,
    tags: list[str],
    body_file: str | None,
    use_stdin: bool,
) -> None:
    """Create a new blog draft from CLI-provided body text."""
    _require_profile(name)
    if use_stdin:
        body = sys.stdin.read()
    elif body_file:
        body = Path(body_file).read_text(encoding="utf-8")
    else:
        body = "Write the draft here.\n"
    path = create_blog_draft(
        name,
        title=title,
        body=body,
        tags=tags,
        summary=summary,
        slug=slug,
    )
    print(f"Created blog draft: {path}")


def cmd_public_blog_media(
    name: str,
    *,
    slug: str,
    file_path: str,
    kind: str,
    alt: str,
    caption: str,
    cover: bool,
    append: bool,
) -> None:
    """Copy media into a blog media directory and print the snippet."""
    _require_profile(name)
    try:
        result = add_blog_media(
            name,
            slug,
            source=file_path,
            kind=kind,
            alt=alt,
            caption=caption,
            cover=cover,
            append=append,
        )
    except PublicSiteError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
    _print_yaml(result.to_dict())


def cmd_public_blog_publish(
    name: str,
    *,
    slug: str,
) -> None:
    """Publish a blog post after validation."""
    _require_profile(name)
    try:
        path = publish_blog_post(name, slug)
    except PublicSiteError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
    print(f"Published blog post: {path}")


def cmd_public_draft_resume(
    name: str,
    *,
    target: str,
) -> None:
    """Create a target-specific resume draft."""
    _require_profile(name)
    html_path, md_path = draft_resume_for_target(name, target)
    print(f"Created resume draft HTML: {html_path}")
    print(f"Created resume draft Markdown: {md_path}")


def cmd_public_draft_project_update(
    name: str,
    *,
    project_id: str,
) -> None:
    """Append a draft project update."""
    _require_profile(name)
    try:
        path = draft_project_update(name, project_id)
    except PublicSiteError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
    print(f"Updated project draft: {Path(path)}")


def _print_yaml(data: object) -> None:
    """Print readable YAML for curation previews."""
    print(
        yaml.dump(
            data,
            allow_unicode=True,
            default_flow_style=False,
            sort_keys=False,
        ).rstrip()
    )


def cmd_public_suggest_groups(name: str) -> None:
    """Preview deterministic evidence grouping suggestions."""
    _require_profile(name)
    groups = suggest_groups(name)
    _print_yaml({"suggestions": [group.to_dict() for group in groups]})


def cmd_public_group(
    name: str,
    *,
    project_id: str,
    title: str,
    evidence_ids: list[str],
    summary: str,
    tags: list[str],
) -> None:
    """Create a draft public project from manually selected evidence."""
    _require_profile(name)
    try:
        result = group_project(
            name,
            project_id=project_id,
            title=title,
            evidence_ids=evidence_ids,
            summary=summary,
            tags=tags,
        )
    except PublicSiteError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
    _print_yaml(result.to_dict())


def cmd_public_hydrate(
    name: str,
    *,
    write_drafts: bool,
) -> None:
    """Preview or write obvious one-to-one output drafts."""
    _require_profile(name)
    try:
        result = hydrate_public_drafts(
            name,
            write_drafts=write_drafts,
        )
    except PublicSiteError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
    _print_yaml(result.to_dict())
