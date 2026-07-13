
from unittest.mock import Mock, patch

import pytest

from bsk_git_viewer.inference.commit_sequence_extraction import extract_main_commits


@patch("bsk_git_viewer.inference.commit_sequence_extraction.to_commit_info")
def test_extract_main_commits_reads_commit_from_main_ref(
    mock_to_commit_info:Mock
)->None:
    repo = Mock()

    main_ref = b"main_commit_id"

    repo.refs = {
        b"refs/heads/main":main_ref
    }

    walker_entry1 = Mock("walk_entry1")
    walker_entry2 = Mock("walk_entry2")

    repo.get_walker.return_value = [walker_entry1,walker_entry2]

    mock_to_commit_info.side_effect = ["commit-info1","commit-info2"]

    result = extract_main_commits(repo)

    assert result==["commit-info1","commit-info2"]

    repo.get_walker.assert_called_once_with(
        include=[main_ref],
    )

    assert mock_to_commit_info.call_count==2
    mock_to_commit_info.assert_any_call(walker_entry1)
    mock_to_commit_info.assert_any_call(walker_entry2)



@patch("bsk_git_viewer.inference.commit_sequence_extraction.to_commit_info")
def test_extract_main_commits_error_on_missing_main_ref(
        mock_to_commit_info=Mock()
):
    repo = Mock()

    repo.refs = {
        b"refs/heads/develop":"heads_develop"
    }

    with pytest.raises(
        ValueError,
        match = "Repository does not contain a main branch"
    ):
        extract_main_commits(repo)

    repo.get_walker.assert_not_called()
    mock_to_commit_info.assert_not_called()

@patch("bsk_git_viewer.inference.commit_sequence_extraction.to_commit_info")
def test_extract_main_commits_walks_from_main_ref(
    mock_to_commit_info = Mock
):
    repo = Mock()

    repo.refs = {
        b"refs/heads/main":"heads_main",
        b"refs/heads/develop":"heads_develop"
    }

    walker_entry1 = Mock(name="walk_entry1")
    walker_entry2 = Mock(name="walk_entry2")

    def fake_get_walker(include):
        if include[0]=="heads_main" and len(include)==1:
            return [walker_entry1, walker_entry2]
        raise ValueError("Not calling the correct method")

    repo.get_walker.side_effect = fake_get_walker

    mock_to_commit_info.side_effect = ["commit-id1","commit-id2"]

    result = extract_main_commits(repo)

    assert result == ["commit-id1","commit-id2"]

    repo.get_walker.assert_called_once_with(
        include=["heads_main"]
    )

    assert mock_to_commit_info.call_count==2
    mock_to_commit_info.assert_any_call(walker_entry1)
    mock_to_commit_info.assert_any_call(walker_entry2)





