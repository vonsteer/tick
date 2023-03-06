from dataclasses import dataclass
from dataclasses import field
from datetime import datetime
from functools import cached_property
from typing import List

from atlassian import Jira
from tick import utils


@dataclass
class BaseTask:
    key: str
    summary: str = None
    status: str = None
    type: str = None
    time_spent: int = 0
    start_time: int = 0

    def dict(self):
        _dict = self.__dict__.copy()
        _dict.pop("jira", None)
        return _dict

    def format(self):
        output = self.dict()
        output.pop("time_spent")
        output.pop("start_time")
        output["minutes_elapsed"] = str(self.minutes)
        return output

    def save(self):
        utils.save_config("current_task", self.dict())

    @cached_property
    def repo(self):
        return utils.resolve("repo", self.key)

    @cached_property
    def project(self):
        return utils.resolve("project", self.key)

    @cached_property
    def branch(self):
        return utils.resolve("branch", self.key) + self.key

    @property
    def seconds(self):
        if getattr(self, "start_time", None):
            return (datetime.now() - datetime.fromtimestamp(self.start_time)).total_seconds() + int(self.time_spent)
        return self.time_spent

    @property
    def minutes(self):
        return round(self.seconds / 60)


@dataclass
class JiraTask(BaseTask):
    jira: Jira = field(repr=False, hash=False, default=None)
    start_time: int = int(datetime.now().timestamp())

    def stop(self):
        self.jira.issue_worklog(
            self.key,
            datetime.fromtimestamp(self.start_time).strftime("%Y-%m-%dT%H:%M:%S.000+0000%z"),
            self.seconds,
        )
        utils.save_config("current_task")


@dataclass
class TaskList:
    tasks: List[dict or BaseTask]

    def __post_init__(self):
        self.tasks = [BaseTask(**task) for task in self.tasks]
        self.keys = [task.key for task in self.tasks]

    def get_task(self, key):
        return [task for task in self.tasks if task.key == key][0]

    def add_task(self, task: BaseTask):
        if task.key not in self.keys:
            self.tasks.append(task)
        else:
            self.replace_task(self.get_task(task.key), task)

    def replace_task(self, old_task, new_task):
        self.tasks[self.tasks.index(old_task)] = new_task
