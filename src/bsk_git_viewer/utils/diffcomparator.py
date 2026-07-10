from collections import defaultdict
from typing import DefaultDict

from bsk_git_viewer.utils.treediff import TreeDiff
from itertools import combinations
from collections import Counter


def build_path_commit_index(
    commit_diffs: dict[str, TreeDiff],
) -> dict[str, list[str]]:
    """
    Converts

        {
            commit_id -> TreeDiff
        }

    into

        {
            file_path -> [commit_id1, commit_id2, ...]
        }
    """

    path_index: DefaultDict[str, list[str]] = defaultdict(list)

    for commit_id, tree_diff in commit_diffs.items():
        for file_change in tree_diff.files:
            path_index[file_change.path].append(commit_id)

    return dict(path_index)


def build_commit_pairs(
    path_commits: dict[str, list[str]],
) -> list[tuple[str, str]]:
    """
    Returns all unique unordered commit pairs that modified
    the same file.

    Example:
        {
            "a.py": ["c1", "c2", "c3"],
            "b.py": ["c2", "c4"]
        }

    returns

        [
            ("c1", "c2"),
            ("c1", "c3"),
            ("c2", "c3"),
            ("c2", "c4"),
        ]
    """

    pairs: set[tuple[str, str]] = set()

    for commits in path_commits.values():
        # Remove duplicates while preserving order
        commits = list(dict.fromkeys(commits))

        for c1, c2 in combinations(commits, 2):
            # Store in canonical order so (A,B)==(B,A)
            if c1 > c2:
                c1, c2 = c2, c1
            pairs.add((c1, c2))

    return sorted(pairs)



def tree_diff_similarity(
    diff1: TreeDiff,
    diff2: TreeDiff,
) -> float:
    """
    Returns similarity score between two TreeDiffs.

    Score range: 0-100
    """

    file_weight = 35
    status_weight = 15
    added_weight = 25
    deleted_weight = 25

    files1 = {f.path: f for f in diff1.files}
    files2 = {f.path: f for f in diff2.files}

    common_paths = set(files1) & set(files2)
    all_paths = set(files1) | set(files2)

    # ---------- Files ----------
    if all_paths:
        file_score = len(common_paths) / len(all_paths)
    else:
        file_score = 1.0

    # ---------- Status ----------
    if common_paths:
        matches = sum(
            files1[p].status == files2[p].status
            for p in common_paths
        )
        status_score = matches / len(common_paths)
    else:
        status_score = 1.0

    # ---------- Added Lines ----------
    add_matches = 0
    add_total = 0

    # ---------- Deleted Lines ----------
    del_matches = 0
    del_total = 0

    for path in common_paths:
        f1 = files1[path]
        f2 = files2[path]

        adds1 = Counter(a.content for a in f1.additions)
        adds2 = Counter(a.content for a in f2.additions)

        dels1 = Counter(d.content for d in f1.deletions)
        dels2 = Counter(d.content for d in f2.deletions)

        add_matches += sum((adds1 & adds2).values())
        add_total += max(sum(adds1.values()), sum(adds2.values()))

        del_matches += sum((dels1 & dels2).values())
        del_total += max(sum(dels1.values()), sum(dels2.values()))

    add_score = 1.0 if add_total == 0 else add_matches / add_total
    del_score = 1.0 if del_total == 0 else del_matches / del_total

    score = (
        file_score * file_weight
        + status_score * status_weight
        + add_score * added_weight
        + del_score * deleted_weight
    )

    return round(score, 2)