from typing import Optional

import click
import rich
import typer

from . import constants
from . import interface
from . import utils


app = typer.Typer()
config_app = typer.Typer()
app.add_typer(config_app, name="config", help="Entry point for configuration changes.")


@app.callback()
def main(ctx: typer.Context):
    configuration = utils.get_config("config")
    if not configuration and "config" != ctx.invoked_subcommand:
        raise click.UsageError("Please configure the CLI prior to use.")
    ctx.obj = interface.Interface(configuration) if ctx.invoked_subcommand != "config" else configuration


@app.command()
def status(ctx: typer.Context):
    """Displays current status of tasks assigned to the user."""
    ctx.obj.status()


@app.command()
def stop(ctx: typer.Context):
    """Stops current task and moves it to 'To Do' if in 'In Progress'."""
    ctx.obj.stop()


@config_app.command()
def init(ctx: typer.Context):
    """Initialise the configuration."""
    data = {}
    if ctx.obj:
        for question in constants.CONFIG_INIT:
            data.update(question.ask(default=ctx.obj.get(question.name)))
    typer.echo("Credentials will be saved locally! If you wish to configure other values use 'tick config edit'")
    utils.save_config("config", data)


@config_app.command()
def edit():
    """Allows user to manually edit file."""
    click.edit(filename=f"{utils.base_path}/config.yaml")


@app.command()
def task(
    ctx: typer.Context,
    workon: Optional[bool] = typer.Option(False, "--workon", "-w", help=constants.WORKON_HELP),
    request: Optional[bool] = typer.Option(False, "--request", "-r", help=constants.REQUEST_HELP),
    task_status: constants.ValidStatus = typer.Option(
        None, "--move", "-m", case_sensitive=False, show_default=False, help=constants.MOVE_HELP
    ),
    time: Optional[int] = typer.Option(None, "--log_time", "-l", min=1, show_default=False, help=constants.TIME_HELP),
    initialise: Optional[bool] = typer.Option(False, "--init", "-i", help=constants.INIT_HELP),
    push: Optional[bool] = typer.Option(False, "--push", "-p", help=constants.PUSH_HELP),
    key: Optional[str] = typer.Argument(utils.get_config(keys=["current_task", "key"]), help=constants.KEY_HELP),
    directory: Optional[str] = typer.Argument("./", help=constants.DIR_HELP),
):
    """Entry-point for all task related functionality."""
    if not key:
        raise click.UsageError("No key provided and no current task.")
    if push:
        ctx.obj.push(key, directory)
    if initialise:
        ctx.obj.init(key, directory)
    if workon:
        ctx.obj.workon(key)
    if task_status:
        ctx.obj.move(key, task_status.value)
    if request:
        ctx.obj.open_pr(key)
    if time:
        ctx.obj.log_time(key, time)


if __name__ == "__main__":
    app()
