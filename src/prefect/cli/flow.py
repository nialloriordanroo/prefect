"""
Command line interface for working with flows.
"""

from typing import List, Optional

import typer
from rich.panel import Panel
from rich.table import Table

from prefect.cli._types import PrefectTyper
from prefect.cli.root import app
from prefect.client import get_client
from prefect.client.schemas.sorting import FlowSort
from prefect.deployments.runner import RunnerDeployment
from prefect.runner import Runner

flow_app = PrefectTyper(name="flow", help="Commands for interacting with flows.")
app.add_typer(flow_app, aliases=["flows"])


@flow_app.command()
async def ls(
    limit: int = 15,
):
    """
    View flows.
    """
    async with get_client() as client:
        flows = await client.read_flows(
            limit=limit,
            sort=FlowSort.CREATED_DESC,
        )

    table = Table(title="Flows")
    table.add_column("ID", justify="right", style="cyan", no_wrap=True)
    table.add_column("Name", style="green", no_wrap=True)
    table.add_column("Created", no_wrap=True)

    for flow in flows:
        table.add_row(
            str(flow.id),
            str(flow.name),
            str(flow.created),
        )

    app.console.print(table)


@flow_app.command()
async def serve(
    entrypoint: str = typer.Argument(
        None,
        help=(
            "The path to a file containing a flow and the name of the flow function in"
            " the format `./path/to/file.py:flow_func_name`."
        ),
    ),
    name: str = typer.Option(
        ...,
        "--name",
        "-n",
        help="The name to give the deployment created for the flow.",
    ),
    description: Optional[str] = typer.Option(
        None,
        "--description",
        "-d",
        help=(
            "The description to give the created deployment. If not provided, the"
            " description will be populated from the flow's description."
        ),
    ),
    version: Optional[str] = typer.Option(
        None, "-v", "--version", help="A version to give the created deployment."
    ),
    tags: Optional[List[str]] = typer.Option(
        ...,
        "-t",
        "--tag",
        default_factory=list,
        help="One or more optional tags to apply to the created deployment.",
    ),
    cron: Optional[str] = typer.Option(
        None,
        "--cron",
        help=(
            "A cron string that will be used to set a schedule for the created"
            " deployment."
        ),
    ),
    interval: Optional[int] = typer.Option(
        None,
        "--interval",
        help=(
            "An integer specifying an interval (in seconds) between scheduled runs of"
            " the flow."
        ),
    ),
    interval_anchor: Optional[str] = typer.Option(
        None, "--anchor-date", help="The start date for an interval schedule."
    ),
    rrule: Optional[str] = typer.Option(
        None,
        "--rrule",
        help="An RRule that will be used to set a schedule for the created deployment.",
    ),
    timezone: Optional[str] = typer.Option(
        None,
        "--timezone",
        help="Timezone to used scheduling flow runs e.g. 'America/New_York'",
    ),
    pause_on_shutdown: bool = typer.Option(
        True,
        help=(
            "If set, provided schedule will be paused when the serve command is"
            " stopped. If not set, the schedules will continue running."
        ),
    ),
):
    """
    Serve a flow via an entrypoint.
    """
    runner = Runner(name=name, pause_on_shutdown=pause_on_shutdown)
    runner_deployment = await RunnerDeployment.from_entrypoint(
        entrypoint=entrypoint,
        name=name,
        interval=interval,
        anchor_date=interval_anchor,
        cron=cron,
        rrule=rrule,
        timezone=timezone,
        description=description,
        tags=tags,
        version=version,
    )
    await runner.add_deployment(runner_deployment)
    app.console.print(
        Panel("Your flow is served and polling for scheduled runs!"),
        style="blue",
    )
    await runner.start()
