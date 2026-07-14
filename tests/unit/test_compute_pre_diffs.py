from unittest.mock import Mock, patch

from bsk_git_viewer.inference.compute_pre_diffs import compute_diffs_with_parent
from bsk_git_viewer.inference.gitcommandinference import CommitWithTree

# from bsk_git_viewer.get_tree_diff import compute_diffs_with_parent
# from bks_git_viewer.models import CommitWithTree


def test_compute_diffs_with_parent_for_single_parent_commit() -> None:
    repo = Mock()

    parent_id = "parent"
    commit_id = "commit"

    parent_commit = Mock()
    parent_commit.parents = []

    current_commit = Mock()
    current_commit.parents = [parent_id]

    parent_tree = Mock(name="parent_tree")
    current_tree = Mock(name="current_tree")
    expected_diff = Mock(name="expected_diff")

    commits_with_tree = {
        parent_id: CommitWithTree(
            commit=parent_commit,
            gittree=parent_tree,
        ),
        commit_id: CommitWithTree(
            commit=current_commit,
            gittree=current_tree,
        ),
    }

    with patch(
        "bsk_git_viewer.inference.compute_pre_diffs.extract_tree_diff",
        return_value=expected_diff,
    ) as mock_extract_tree_diff:
        result = compute_diffs_with_parent(repo, commits_with_tree)

    assert commit_id in result
    assert result[commit_id].commit is current_commit
    assert result[commit_id].pre_diff is expected_diff

    mock_extract_tree_diff.assert_called_once_with(
        repo,
        current_tree,
        parent_tree,
    )



def test_compute_diffs_with_parent_skips_root_commit() -> None:
    repo = Mock()

    root_id = "root"
    root_commit = Mock()
    root_commit.parents = []

    commits_with_tree = {
        root_id: CommitWithTree(
            commit=root_commit,
            gittree=Mock(),
        ),
    }

    with patch(
        "bsk_git_viewer.inference.compute_pre_diffs.extract_tree_diff",
    ) as mock_extract_tree_diff:
        result = compute_diffs_with_parent(repo, commits_with_tree)

    assert result == {}
    mock_extract_tree_diff.assert_not_called()


def test_compute_diffs_with_parent_skips_merge_commit() -> None:
    repo = Mock()
    merge_id = "merge"
    merge_commit = Mock()
    merge_commit.parents = ["parent1","parent2"]

    commits_with_tree = {
        merge_id: CommitWithTree(
            commit=merge_commit,
            gittree=Mock)
    }

    with patch("bsk_git_viewer.inference.compute_pre_diffs.extract_tree_diff",
    ) as mock_extract_tree_diff:
        result = compute_diffs_with_parent(repo, commits_with_tree)

    assert result == {}
    mock_extract_tree_diff.assert_not_called()
    

def test_compute_diffs_with_parent() ->None:
    repo = Mock()

    commit_id = "commit"
    commit = Mock()
    commit.parents = ["missing_parent"]

    commits_with_tree = {
        commit_id:CommitWithTree(
            commit = commit, 
            gittree=Mock())
    }



    with patch("bsk_git_viewer.inference.compute_pre_diffs.extract_tree_diff",
    ) as mock_extract_tree_diff:
        result = compute_diffs_with_parent(repo, commits_with_tree)
    
    assert result=={}
    mock_extract_tree_diff.assert_not_called()

def test_compute_diffs_with_parent_return_empty_map() -> None:
    assert compute_diffs_with_parent(Mock(),{}) == {}


def test_does_not_modify_input_map() -> None:
    commits = {
        "root": CommitWithTree(
            commit=Mock(parents=[]),
            gittree=Mock(),
        ),
    }

    original = commits.copy()

    compute_diffs_with_parent(Mock(), commits)

    assert commits == original

@patch("bsk_git_viewer.inference.compute_pre_diffs.extract_tree_diff")
def test_processes_all_valid_single_parent_commits(
    mock_extract_compute_diff:Mock,
) -> None:
    mock_extract_compute_diff.side_effect = ["diff1","diff2"]
    
    commits = {
        "root": CommitWithTree(
            commit=Mock(parents=[]),
            gittree="tree-root",
        ),
        "commit-1": CommitWithTree(
            commit=Mock(parents=["root"]),
            gittree="tree-1",
        ),
        "commit-2": CommitWithTree(
            commit=Mock(parents=["commit-1"]),
            gittree="tree-2",
        ),
        "merge": CommitWithTree(
            commit=Mock(parents=["commit-1", "other"]),
            gittree="tree-merge",
        ),
    }

    result = compute_diffs_with_parent(Mock(), commits)

    assert set(result) == {"commit-1","commit-2"}
    assert result["commit-1"].pre_diff == "diff1"
    assert result["commit-2"].pre_diff == "diff2"
    assert mock_extract_compute_diff.call_count == 2
    