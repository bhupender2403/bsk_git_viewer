



from dulwich.repo import Repo

from bsk_git_viewer.git.commit_sequence_extraction import extract_main_commits, extract_other_commits
from bsk_git_viewer.git.git_tree import DulwichTreeLoader
from bsk_git_viewer.inference.compute_commit_similarity import compute_similarity_score, extract_candidates_for_similarity
from bsk_git_viewer.inference.compute_pre_diffs import compute_diffs_with_parent
from bsk_git_viewer.models import CommitInfo, CommitWithPreDiff, CommitWithTree


def infer_commands(repo):
    """
        Extract the structure of all the commits from all the brances and infer the possible sequence of git commands
        which were used to arrive the current configuration.

    """
    main_commits = extract_main_commits(repo)

    other_commits = extract_other_commits(repo, main_commits)
    
    main_trees:dict[str,dict] = get_tree_nodes(main_commits)
    
    other_trees:dict[str,dict] = get_tree_nodes(other_commits)

    main_pre_diff:dict[str,CommitWithPreDiff] = compute_diffs_with_parent(main_trees)

    other_pre_diff:dict[str, CommitWithPreDiff] = compute_diffs_with_parent(other_trees)

    commit_similarity_score:dict[str, dict[str,float]] = {}

    for commit_id in main_pre_diff:
        commit = main_pre_diff[commit_id]

        candidates:list[CommitWithPreDiff] = extract_candidates_for_similarity(commit,[x[1] for x in list(other_pre_diff.items())])
        
        score_map:dict[str,float] = {}
        for candidate in candidates:
            score = compute_similarity_score(commit, score_map)
            score_map[candidate.commit.commit_id] = score
        commit_similarity_score[commit.commit.commit_id] = score_map
    

    # extract main commits
    # extract all the other commits
    # for each main commits find similarity scores of prediffs with all the other branch kids
    # create possible sequences
    # assign type and confidence score to each possible sequence
    # filter the low scoring overlapping sequence
    # and show the remaining in the UI







def get_tree_nodes(repo:Repo, commits:list[CommitInfo]) -> dict[str,CommitWithTree]:
    loader = DulwichTreeLoader(repo)
    return {x.commit_id:CommitWithTree(x,loader.load_commit_tree(x)) for x in commits}



    
