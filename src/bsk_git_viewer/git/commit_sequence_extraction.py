from dulwich.objects import Commit

from bsk_git_viewer.models import CommitInfo
from bsk_git_viewer.utils.parse_utils import to_commit_info


def extract_other_commits(repo, main_commits:list[CommitInfo]) -> list[CommitInfo]:
    all_commits = extract_all_commits(repo)

    main_commit_set = {x.commit_id for x in main_commits}

    return [
        x for x in all_commits
        if x.commit_id not in main_commit_set
    ]

def extract_all_commits(repo):

    all_commits = {}
    for sha in repo.object_store:
        obj = repo.object_store[sha]

        if isinstance(obj, Commit):
            all_commits.append(to_commit_info(obj)) 

    return all_commits

# ===============================================================================================
# Main commits: ref/heads/main
# ===============================================================================================

def extract_main_commits(repo):
    main_ref_name = b"refs/heads/main"

    if main_ref_name not in repo.refs:
        raise ValueError("Repository does not contain a main branch")
    
    main_commit_id = repo.refs[main_ref_name]

    return [
        to_commit_info(x) 
        for x in repo.get_walker(
            include=[main_commit_id]
        )
    ]



