
import typer
import uvicorn

from bsk_git_viewer.server import app

cmd_app = typer.Typer()

@cmd_app.command()
def main(
    repo_path:str=".",
    port:int=8000):
    """Start BKS Git Command Viewer"""
    typer.echo(f"Starting BKS viewer with repp {repo_path}")
    typer.echo(f"Starting... http://127.0.0.1:{port}")

    app.state.repo_path = repo_path

    uvicorn.run("bsk_git_viewer.server:app",
                host = "127.0.0.1",
                port = port,
                reload = False
    )

if __name__=="__main__":
    cmd_app()



