from __future__ import annotations

import typer

from whoosh.api.merger import execute_local_merge, plan_local_merge

app = typer.Typer(help="Merge source and destination directories.")


@app.command()
def run(
    source_dir: str = typer.Option(..., "--source-dir"),
    dest_dir: str = typer.Option(..., "--dest-dir"),
    recursive: bool = typer.Option(True, "--recursive/--no-recursive", "-r"),
    hash_name: str = typer.Option("md5", "--hash", help="md5 or sha256"),
    dry_run: bool = typer.Option(False, "--dry-run"),
) -> None:
    actions = plan_local_merge(source_dir, dest_dir, recursive=recursive, hash_name=hash_name)
    for action in actions:
        typer.echo(f"{action.action} {action.source} -> {action.destination} ({action.reason})")

    if not dry_run:
        execute_local_merge(actions)

    typer.echo(f"planned={len(actions)} applied={0 if dry_run else len(actions)}")


def main() -> None:
    app()


if __name__ == "__main__":
    main()
