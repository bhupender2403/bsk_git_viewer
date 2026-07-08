import typer

from bsk_git_viewer.git_reader import analyze_repository, read_repository

app = typer.Typer()

@app.command()
def repo(repo_path:str="."):
    analyze_repository(repo_path)
    
if __name__=="__main__":
    app()
