from pathlib import Path
from dulwich.repo import Repo

from bsk_git_viewer.models import  Repository
from dulwich.reflog import read_reflog

from bsk_git_viewer.utils.parse_utils import to_commit_info

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



def read_repository(repo_path:str|Path):
    
    repo_path = Path(repo_path)

    repo = Repo(repo_path)

    refs = repo.get_refs()

    heads = [
        sha
        for name, sha in refs.items()
        if name.startswith(b"refs/heads/")
    ]

    print(refs)
    print(repo.head())

    commits = [to_commit_info(x) for x in repo.get_walker(include=heads)]

    with open(Path(repo.controldir()) / "logs/HEAD", "rb") as f:
        entries = list(read_reflog(f))

    for entry in entries:
        print(entry.old_sha, entry.new_sha, entry.message)

    return Repository(name = repo_path.name,commits = commits, branches = dict())


