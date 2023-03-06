from datetime import datetime
import os
from typing import List

from atlassian import Bitbucket
from atlassian import Jira
import click
import git
import requests
import rich
from rich.style import Style
from rich.table import Table
import typer

from . import constants
from . import task
from . import utils


class Interface:
    """Base Class for Interface, this class will integrate with the servers."""

    def __init__(self, configuration):
        self.jira = Jira(**configuration)
        configuration["url"] = configuration.get("url").replace("jira", "bitbucket")
        self.bitbucket = Bitbucket(**configuration)
        retrieved_task = utils.get_config("current_task")
        self.current_task = task.JiraTask(jira=self.jira, **retrieved_task) if retrieved_task else None

    def stop(self):
        if self.current_task:
            typer.echo(f"Stopping Current {self.current_task}")
            if self.current_task.status == "In Progress":
                self.move(self.current_task.key, "To Do")
            self.current_task.stop()
        else:
            typer.echo("No task currently being worked on.")

    @property
    @utils.timed_lru_cache(300)
    def task_list(self):
        tasks = task.TaskList(
            utils.map_deep_get(
                self.jira.jql(constants.JQL_CURRENT_TASKS).get("issues"), constants.KEYS, constants.HEADERS
            )
        )
        if self.current_task:
            tasks.add_task(self.current_task)
        return tasks

    @property
    def current_task(self):
        return self._current_task

    @current_task.setter
    def current_task(self, value):
        self._current_task = value

    def get_task(self, key):
        try:
            return task.JiraTask(
                jira=self.jira, **utils.map_deep_get(self.jira.issue(key), constants.KEYS, constants.HEADERS)
            )
        except requests.exceptions.HTTPError as error:
            raise click.ClickException(error.response.json().get("errorMessages")[0])

    def log_time(self, key, time):
        """Logs time for provided key"""
        typer.echo(f"Logging {time} minutes on {key}")
        self.jira.issue_worklog(
            key,
            datetime.now().strftime("%Y-%m-%dT%H:%M:%S.000+0000%z"),
            int(time) * 60,
        )

    def move(self, key, status) -> None:
        """Moves Task to status provided"""
        typer.echo(f"Moving {key} to {status.capitalize()}")
        self.jira.issue_transition(key, status)

    @staticmethod
    def generate_table(task_list: task.TaskList) -> Table:
        """Formats values into a standardised table format."""
        cap_headers = [header.capitalize() for header in constants.HEADERS]
        table = Table(*cap_headers)
        for task in task_list.tasks:
            table.add_row(*task.format().values(), style=constants.CURRENT_STYLE if task.start_time else "")
        return table

    def status(self):
        """Provides the Task Status, included the user's unresolved tasks."""
        task_table = self.generate_table(self.task_list)
        rich.print(task_table)

    def workon(self, key: str):
        if self.current_task and self.current_task.key != key:
            self.stop()
        self.current_task = self.get_task(key)
        self.current_task.save()
        if self.current_task.status == "To Do":
            self.move(key, "In Progress")

    def init(self, key: str, directory: str):
        """Initialises a repo in the repository, and checkouts out the branch key."""
        selected_task = self.get_task(key)
        directory = os.path.join(directory, selected_task.repo)
        try:
            if os.path.exists(directory):
                typer.echo(f"{selected_task.repo} already exists locally.")
                repo = git.Repo(directory)
            else:
                url = utils.deep_get(
                    self.bitbucket.get_repo(selected_task.project, selected_task.repo), constants.CLONE_PATH
                )
                typer.echo(f"Creating new repo at {directory} from {url}")
                repo = git.Repo.clone_from(url=url, to_path=directory)
            typer.echo(repo.git.checkout(selected_task.branch))
            typer.echo(repo.git.pull())
        except git.GitCommandError:
            raise click.UsageError(
                f"Resolution likely failed, custom rules can be added using 'tick config edit' to fix the following:\n"
                f"repo -> {selected_task.repo}\n"
                f"branch -> {selected_task.branch}\n"
                f"project -> {selected_task.branch}"
            )

    def push(self, key: str, directory: str):
        """Pushes current changes."""
        selected_task = self.get_task(key)
        if utils.is_correct_repo(selected_task.branch):
            repo = git.Repo(directory)
            repo.git.add("./")
            repo.git.commit(selected_task.summary)
            repo.git.push()

    def open_pr(self, key: str):
        """Creates a pull request on bitbucket for the associated task."""
        selected_task = self.get_task(key)
        typer.echo(f"Opening PR for {selected_task.key}")
        self.bitbucket.open_pull_request(
            selected_task.project,
            selected_task.repo,
            selected_task.project,
            selected_task.repo,
            selected_task.branch,
            "develop",
            f"{key} {selected_task.summary}",
            "",
        )
        typer.echo(f"Pull request created for branch {selected_task.branch}")
