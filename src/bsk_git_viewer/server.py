
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from bsk_git_viewer.git_reader import analyze_repository


app = FastAPI(title = "BSK Git Command Viewer")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods = ["*"],
    allow_headers = ["*"]
)

@app.get("/api/health")
def health_check():
    return {"status":"ok"}


@app.get("/api/repository")
def get_repository(path:str = "."):
    return analyze_repository(app.state.repo_path)

