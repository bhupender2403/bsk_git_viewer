from dulwich.repo import Repo

from bsk_git_viewer.git.tree_diff import extract_tree_diff
from bsk_git_viewer.models import CommitWithPreDiff, CommitWithTree


def compute_diffs_with_parent(repo:Repo, commits_with_tree:dict[str,CommitWithTree]) -> dict[str,CommitWithPreDiff]:
    """ Compute each single parent commits tree diff with its parent.

    Root commits and merge commits are excluded. Commits whose parents are not present in the
    ``commits_with_tree`` are skipped.
    """
    pre_diff_map:dict[str,CommitWithPreDiff] = {}

    for commit_id, commit_data in commits_with_tree.items():
        commit = commit_data.commit
        tree = commit_data.gittree


        if len(commit.parents)==1:
            
            parent_data:CommitWithTree = commits_with_tree.get(commit.parents[0])

            if parent_data:

                diff = extract_tree_diff(repo, tree, parent_data.gittree)
                pre_diff_map[commit_id] = CommitWithPreDiff(
                    commit = commit
                    ,pre_diff =diff)
        
    return pre_diff_map
