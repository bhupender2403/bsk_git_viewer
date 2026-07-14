
from dataclasses import dataclass
from unittest.mock import MagicMock


from bsk_git_viewer.inference.compute_commit_similarity import extract_candidates_for_similarity
from bsk_git_viewer.models import CommitInfo, CommitWithPreDiff, FileChange, TreeDiff


def test_extract_candidates_for_similarity():
    commit = get_commit_with_pre_diff("id",[ChangeMark(path="path1",status="added")])
    result = extract_candidates_for_similarity(commit,[])

    assert len(result)==0

@dataclass
class ChangeMark:
    path:str
    status:str


def to_file_change(mark:ChangeMark) -> FileChange:
    change = MagicMock(spec = FileChange)
    change.path = mark.path
    change.status = mark.status
    return change


def get_commit_with_pre_diff(commit_id:str, changes:list[ChangeMark])-> CommitWithPreDiff:
    commit = MagicMock(spec = CommitWithPreDiff)
    commit.commit = MagicMock(spec = CommitInfo) 
    commit.commit.commit_id = commit_id
    commit.pre_diff = MagicMock(spec = TreeDiff)
    commit.pre_diff.files = [to_file_change(x) for x in changes]
    return commit


def test_extract_candidates_for_similarity_correct_match():
    commit = get_commit_with_pre_diff("commit",[
        ChangeMark(path="path1",status="added"),
        ChangeMark(path="path2",status="deleted"),
        ChangeMark(path="path3",status="modified")])
    
    candidate1 = get_commit_with_pre_diff("c1",[
        ChangeMark(path="path1",status="added"),
        ChangeMark(path="path21",status="deleted"),
        ChangeMark(path="path31",status="modified")])
    
    candidate2 = get_commit_with_pre_diff("c2",[
        ChangeMark(path="path11",status="added"),
        ChangeMark(path="path21",status="deleted"),
        ChangeMark(path="path31",status="modified")])
    
    candidate3 = get_commit_with_pre_diff("c3",[
        ChangeMark(path="path1",status="added"),
        ChangeMark(path="path2",status="deleted"),
        ChangeMark(path="path3",status="modified")])
    
    result = extract_candidates_for_similarity(commit,[candidate1,candidate2,candidate3])

    assert len(result)==2
    assert "c1" in {x.commit.commit_id for x in result}
    assert "c2" not in {x.commit.commit_id for x in result}
    assert "c3" in {x.commit.commit_id for x in result}



def test_extract_candidates_for_similarity_no_match():
    commit = get_commit_with_pre_diff("commit",[
        ChangeMark(path="path1",status="added"),
        ChangeMark(path="path2",status="deleted"),
        ChangeMark(path="path3",status="modified")])
    
    candidate1 = get_commit_with_pre_diff("c1",[
        ChangeMark(path="path11",status="added"),
        ChangeMark(path="path21",status="deleted"),
        ChangeMark(path="path31",status="modified")])
    
    candidate2 = get_commit_with_pre_diff("c2",[
        ChangeMark(path="path11",status="added"),
        ChangeMark(path="path21",status="deleted"),
        ChangeMark(path="path31",status="modified")])
    
    candidate3 = get_commit_with_pre_diff("c3",[
        ChangeMark(path="path31",status="added"),
        ChangeMark(path="path32",status="deleted"),
        ChangeMark(path="path33",status="modified")])
    
    result = extract_candidates_for_similarity(commit,[candidate1,candidate2,candidate3])

    assert len(result)==0

