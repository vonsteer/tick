from enum import Enum
import re

from rich import prompt
from rich.style import Style


JQL_CURRENT_TASKS = "assignee = currentUser() and resolution = Unresolved order by updated"
JQL_ = "assignee = currentUser() and resolution = Unresolved order by updated"


class ValidStatus(str, Enum):
    TO_DO = "to do"
    IN_PROGRESS = "in progress"
    AWAITING_PR_APPROVAL = "awaiting pr approval"
    PR_IN_REVIEW = "pr in review"
    PENDING_QA = "pending qa"
    QA_IN_REVIEW = "qa in review"
    RESOLVED = "resolved"
    DONE = "done"


class PreparedPrompt:
    """Wrapper for prompt, so the output is a key pair and can be pre-prepared."""

    def __init__(self, name, question, password=False):
        self.name = name
        self.question = question
        self.password = password
        self.prompt = prompt.Prompt(password=password)

    def ask(self, **kwargs):
        return {self.name: self.prompt.ask(prompt=self.question, password=self.password, **kwargs)}


CONFIG_INIT = [
    PreparedPrompt(name="url", question="Server Url:"),
    PreparedPrompt(name="username", question="Username:"),
    PreparedPrompt(name="password", question="Password:", password=True),
]
WORKON_HELP = "Work on a task if key provided."
REQUEST_HELP = "Creates a Pull request for associated task and provides link."
MOVE_HELP = "Moves task to status specified."
TIME_HELP = "Logs minutes specified on task, minimum 1 minute."
KEY_HELP = "Optional key argument used in conjunction with options. If not provided, current task key will be used."
INIT_HELP = "Initialises new git repo using the key, the project will be filtered from the key."
PUSH_HELP = "Collects git changes into a new commit and pushes them with the task summary."
DIR_HELP = "Optional dir argument used in conjunction with init option."


CURRENT_STYLE = Style(color="magenta", blink=True, bold=True)

KEYS = [
    ["key"],
    ["fields", "summary"],
    ["fields", "status", "name"],
    ["fields", "issuetype", "name"],
    ["fields", "aggregatetimespent"],
]
HEADERS = ["key", "summary", "status", "type", "time_spent"]
CLONE_PATH = ["links", "clone", -1, "href"]
RE_KEY = re.compile(r"(\w+)-\d+$")
