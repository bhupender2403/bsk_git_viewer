import os
from pathlib import Path

import typer

from bsk_git_viewer.git_reader import analyze_repository, read_repository
from bsk_git_viewer.gitcreate.git_sceneria_creator import GitScenarioRunner, parse_scenario

app = typer.Typer()

@app.command()
def gitrun(
    repo_path:str,
    command_file:str
):
    repo_path = Path(repo_path)

    if os.path.exists(repo_path):
        typer.echo("Path already exist so it cannot be run again")
    
    os.mkdir(repo_path)

    with open(command_file,"rt") as fd:
        command_text = fd.read()
    
    commands = parse_scenario(
        command_text
    )
    gitrunner = GitScenarioRunner(repo_path)

    gitrunner.run(commands)
    
if __name__=="__main__":
    app()
