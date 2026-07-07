
import typer
import uvicorn


cmd_app = typer.Typer()

@cmd_app.command()
def main(
    repo_path:str=",",
    port:int=8000):
    """Start BKS Git Command Viewer"""
    typer.echo(f"Starting BKS viewer with repp {repo_path}")
    typer.echo(f"Starting... http://127.0.0.1:{port}")

    uvicorn.run("bsk_git_viewer.server:app",
                host = "127.0.0.1",
                port = port,
                reload = False
    )

if __name__=="__maini__":
    cmd_app()



