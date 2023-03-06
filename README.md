
Task Integration CLI


Initial concept will only cover Atlassian Apps, specifically Jira and Bitbucket. Things to do:
 - tick configure 
 - tick task -w --workon <TASK> (work on a task if key provided, if not presents list of unresolved tasks, moves task
to In Progress if chosen, starts timer )
 - tick status (Provides the status of Tasks, what's in progress and what was recently worked on.)
 - tick task -m --move <STATUS> <TASK> (Moves task to status specified, if no task is specified current task is used.)
 - tick task -r --request <TASK> (Creates a Pull request for associated task and provides link.)
 - tick task -s --stop <TASK> (Stops timer for task and moves to To Do if in progress)
 - tick task -i --init <TASK> (Initialises the repo, creates the branch and pulls latest changes)

We should integrate this with git, maybe with pre-commit/new-branch hooks, plus when you start a new task it should 
automatically create the branch if it's not already associated.

