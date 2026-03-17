import click

import client


@click.group()
def cli():
    """CLI client for the steer listen server."""


@cli.command()
@click.argument("url")
@click.argument("prompt")
def start(url: str, prompt: str):
    """Start a new agent job."""
    result = client.start_job(url, prompt)
    click.echo(result["job_id"])


@cli.command()
@click.argument("url")
@click.argument("job_id")
def get(url: str, job_id: str):
    """Get the current state of a job."""
    yaml_content = client.get_job(url, job_id)
    click.echo(yaml_content)


@cli.command("list")
@click.argument("url")
@click.option("--archived", is_flag=True, help="Show archived jobs only.")
def list_cmd(url: str, archived: bool):
    """List all jobs."""
    yaml_content = client.list_jobs(url, archived=archived)
    click.echo(yaml_content)


@cli.command()
@click.argument("url")
def clear(url: str):
    """Archive all jobs."""
    result = client.clear_jobs(url)
    click.echo(f"Archived {result['archived']} job(s)")


@cli.command()
@click.argument("url")
@click.argument("n", default=1, type=int)
def latest(url: str, n: int):
    """Show full details of the latest N jobs."""
    output = client.latest_jobs(url, n)
    click.echo(output)


@cli.command()
@click.argument("url")
@click.argument("job_id")
def stop(url: str, job_id: str):
    """Stop a running job."""
    result = client.stop_job(url, job_id)
    click.echo(f"Job {result['job_id']} {result['status']}")


@cli.command()
@click.argument("prompt")
@click.option("--requires", "-r", multiple=True, help="Required capabilities (e.g. gui-x11, terminal)")
@click.option("--agent", default="claude", help="Agent backend: claude, opencode, pi")
def route(prompt: str, requires: tuple[str, ...], agent: str):
    """Route a job to the best available device via brain."""
    caps = list(requires) if requires else ["terminal"]
    try:
        result = client.route_job(prompt, caps, agent)
        click.echo(f"Routed → {result['job_id']}")
    except RuntimeError as e:
        click.echo(f"Routing failed: {e}", err=True)
        raise SystemExit(1)


if __name__ == "__main__":
    cli()
