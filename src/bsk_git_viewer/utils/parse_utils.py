
from bsk_git_viewer.models import CommitInfo


def to_commit_info(entry):
    commit = entry.commit
    return CommitInfo(commit_id=commit.id.decode(),author = commit.author.decode(),message = commit.message.decode(), commit_time = int(commit.commit_time),parents = [x.decode() for x in commit.parents])
