from pathlib import Path
from dulwich.repo import Repo

from bsk_git_viewer.models import CommitInfo, Repository


def analyze_repository(path:Path):
    repo_path = Path(path).resolve()
    git_path = repo_path / ".git"
    

    print("git folder",git_path)

    if not git_path.exists():
        return {
            "status":"fail",
            "error":"Not a valid git repository root",
            "name":"Not a valid git",
            "path": str(repo_path)
        }
    
    #print(repo_path)
    repository = read_repository(repo_path)
    

    return {
        "status":"pass",
        "path":str(repo_path),
        "name":repo_path.name,
        "data":repository,
        "git_path":str(git_path),
        "message": "Found git folder"
    }


def _to_commit_info(entry):
    commit = entry.commit
    return CommitInfo(commit_id=commit.id.decode(),author = commit.author.decode(),message = commit.message.decode(), commit_time = int(commit.commit_time),parents = [x.decode() for x in commit.parents])

def read_repository(repo_path:str|Path):
    
    repo_path = Path(repo_path)

    repo = Repo(repo_path)
    
    commits = [_to_commit_info(x) for x in repo.get_walker()]

    return Repository(name = repo_path.name,commits = commits, branches = dict())


