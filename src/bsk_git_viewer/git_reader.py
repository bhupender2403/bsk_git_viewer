from pathlib import Path

def analyze_repository(path:Path):
    repo_path = Path(path).resolve()
    git_path = repo_path / ".git"
    

    if not git_path.exists():
        return {
            "status":"fail",
            "error":"Not a valid git repository root",
            "path": str(repo_path)
        }
    
    return {
        "status":"pass",
        "path":str(repo_path),
        "git_path":str(git_path),
        "message": "Found git folder"
    }

