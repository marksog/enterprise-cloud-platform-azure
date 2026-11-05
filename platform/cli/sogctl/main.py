import typer

from sogctl.auth import login as entra_login
from sogctl.auth import logout as entra_logout

import httpx

from sogctl.client import (
    get_current_identity,
    create_workload,
)



app = typer.Typer(
    help="SOG Internal Developer Platform CLI",
    no_args_is_help=True,
)

workload_app = typer.Typer(
    help="Manage platform workloads."
)

app.add_typer(workload_app, name="workload")

DEMO_IMAGE = "nginx:1.27"
DEMO_PORT = 80

@app.callback()
def cli() -> None:
    """SOG Internal Developer Platform CLI."""
    pass


@app.command()
def version():
    """Display the installed CLI version."""
    typer.echo("sogctl version 0.1.0")


@app.command()
def login():
    """Sign in with Microsoft Entra ID."""

    try:
        result = entra_login()

    except (RuntimeError, ValueError) as exc:
        typer.echo(f"Login failed: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    typer.echo(f"Signed in as {result['username']}")

@app.command()
def logout():
    """Remove locally cached Microsoft Entra credentials."""

    try:
        entra_logout()

    except RuntimeError as exc:
        typer.echo(f"Logout failed: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    typer.echo("Local sogctl credentials removed.")

@app.command()
def whoami():
    """Display the identity verified by the SOG Platform API."""

    try:
        identity = get_current_identity()

    except RuntimeError as exc:
        typer.echo(f"Authentication failed: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    except httpx.HTTPStatusError as exc:
        typer.echo(
            f"Platform API rejected the request "
            f"(HTTP {exc.response.status_code}).",
            err=True,
        )
        raise typer.Exit(code=1) from exc

    except httpx.RequestError as exc:
        typer.echo(
            f"Cannot reach Platform API: {exc}",
            err=True,
        )
        raise typer.Exit(code=1) from exc

    typer.echo(f"Developer ID: {identity['developer_id']}")
    typer.echo(f"Platform groups: {', '.join(identity['groups']) or 'None'}")

@workload_app.command("create")
def workload_create(
    name: str = typer.Option(..., help="Workload name."),
    domain: str = typer.Option(..., help="Owning domain."),
    environment: str = typer.Option(..., help="Target environment."),
    size: str = typer.Option("small", help="Workload size."),
    image: str | None = typer.Option(
        None, help="Application container image."
    ),
    port: int | None = typer.Option(
        None, min=1, max=65535, help="Container port."
    ),
):
    """Create a workload proposal."""

    if image is None:
        image = DEMO_IMAGE
        typer.echo(
            "Demo mode: using nginx, not your application image.",
            err=True,
        )

    if port is None:
        port = DEMO_PORT if image == DEMO_IMAGE else 8080

    payload = {
        "name": name,
        "domain": domain,
        "environment": environment,
        "size": size,
        "image": image,
        "port": port,
    }

    try:
        result = create_workload(payload)

    except RuntimeError as exc:
        typer.echo(f"Authentication failed: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    except httpx.HTTPStatusError as exc:
        typer.echo(
            f"API returned HTTP {exc.response.status_code}: "
            f"{exc.response.text}",
            err=True,
        )
        raise typer.Exit(code=1) from exc

    except httpx.RequestError as exc:
        typer.echo(f"API connection failed: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    policy = result.get("policy", {})
    decision = policy.get("decision", "unknown")

    typer.echo(f"Workload: {result.get('workload', name)}")
    typer.echo(f"Policy decision: {decision}")

    for reason in policy.get("reasons", []):
        typer.echo(f"Reason: {reason}")

    preview = result.get("pull_request")

    if preview:
        typer.echo(f"Repository: {preview.get('repository')}")
        typer.echo(f"Branch: {preview.get('branch')}")
        typer.echo(f"Dry run: {preview.get('dry_run')}")

    if decision.lower() not in ("allow", "allowed"):
        raise typer.Exit(code=2)

if __name__ == "__main__":
    app()