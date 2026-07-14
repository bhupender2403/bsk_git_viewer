
from dataclasses import dataclass
from unittest.mock import MagicMock

import pytest


from bsk_git_viewer.inference.compute_commit_similarity import compute_changeset_score, compute_similarity_score_for_change, extract_candidates_for_similarity
from bsk_git_viewer.models import CommitInfo, CommitWithPreDiff, FileChange, LineChange, TreeDiff


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


@pytest.mark.parametrize(
        "sequences1,sequences2,score_exp,match,total",
        [
            ([],[],25, 0, 0),
            (["a1"],[],0 , 0, 1),
            (["a1","a2"],["a2"],66.67, 1, 3),
            (["a1","a2"],["a1","a2"],100, 2, 4),
            (["a1","a2","a3"],["a1","a4","a3"],66.66, 2, 6),
        ]
)
def test_compute_changeset_score(sequences1, sequences2, score_exp, match, total):
    score = compute_changeset_score(sequences1, sequences2)

    assert score.score == pytest.approx(score_exp,abs=1e-2)
    assert score.match_count == match
    assert score.total == total



@pytest.mark.parametrize(
        "addition1, deletion1, addition2, deletion2, score_exp",
        [
           ([],[],[],[],40),
           (["a1"],[],[],[],20),
           (["a1"],[],[],["a2"],20),
           (["a1"],[],["a1"],["a2"],60),
           (["a1"],["a2"],["a1"],["a2"],100),
           (["a1","a4","a5"],["a2"],["a1","a4","a5","a6"],["a2"],94.29),
           (["a1","a4","a5"],["a2"],["a11","a41","a5","a61"],["a21"],31.42),

        ]
)
def test_compute_similarity_score_for_change_file_modification(addition1, deletion1, addition2, deletion2, score_exp):
    

    def mock_change(pathV,status,additions, deletions):
        change1 = MagicMock(spec = FileChange)
        change1.path = pathV
        change1.status = status
        add_list = []
        for x in additions:
            add_v = MagicMock(spec = LineChange)
            add_v.content = x
            add_v.type = "add"
            add_list.append(add_v)
        
        del_list = []
        for x in deletions:
            del_v = MagicMock(spec = LineChange)
            del_v.content = x
            del_v.type = "delete"
            del_list.append(del_v)
        
        change1.additions = add_list
        change1.deletions = del_list
        return change1


    change1 = mock_change("f1","modified",addition1, deletion1)
    change2 = mock_change("f1","modified",addition2, deletion2)
    
    score = compute_similarity_score_for_change(change1, change2)
    assert score == pytest.approx(score_exp,0.01)


@pytest.mark.parametrize(
        "status1, status2, score_exp",
        [
            ("added","added",100),
            ("deleted","deleted",100),
            ("added","deleted", 0),
            ("deleted","added", 0),
            ("deleted","modified", 0),
            ("modified","added", 20),
        ]
)
def test_compute_similarity_score_for_change_status(status1, status2, score_exp):
    change1 = MagicMock(spec = FileChange)
    change1.path = "f1"
    change1.status = status1

    change2 = MagicMock(spec = FileChange)
    change2.path = "f1"
    change2.status = status2

    score = compute_similarity_score_for_change(change1, change2)
    assert score == score_exp