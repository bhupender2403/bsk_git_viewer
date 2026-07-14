
import pytest

from bsk_git_viewer.utils.sequence_matching import match_sequences


@pytest.mark.parametrize(
        "first_sequences, second_sequences, additions_exp, deletions_exp",
        [
            ([],[],[],[]),
            (["a1"],[],[],["a1"]),
            ([],["a1"],["a1"],[]),
            (["a1"],["a1"],[],[]),
            (["a1","a2"],["a2"],[],["a1"]),
            (["a1","a2"],["a1"],[],["a2"]),
            (["a1"],["a2","a1"],["a2"],[]),
            (["a1"],["a1","a2"],["a2"],[]),
            (["a1","a2","a3","a4","a5","a6","a8"],["a1","a3","a4","a7","a6","a9","a8"],["a7","a9"],["a2","a5"]),
        ]
)
def test_match_sequences(first_sequences, second_sequences, additions_exp, deletions_exp):
    additions, deletions = match_sequences(first_sequences, second_sequences)

    assert len(additions) == len(additions_exp)
    assert len(deletions) == len(deletions_exp)

    for added in additions:
        assert added.content in additions_exp
    
    for deleted in deletions:
        assert deleted.content in deletions_exp

