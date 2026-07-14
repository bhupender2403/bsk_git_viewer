

from dataclasses import dataclass

from bsk_git_viewer.models import  CommitWithPreDiff, FileChange, TreeDiff
from bsk_git_viewer.utils.sequence_matching import match_sequences


def extract_candidates_for_similarity(commit:CommitWithPreDiff, commit_list:list[CommitWithPreDiff]):
    """
    Return candidates for similarity based on paths with changes in commits. Any commit sharing a path
    with change are considered to be a candidate for similarity.
    """
    
    file_change_paths =  {x.path for x in commit.pre_diff.files}

    
    if len(file_change_paths)==0:
        return []
    else:
        candidates = []


        for candidate in commit_list:
            candiate_paths = {x.path for x in candidate.pre_diff.files}
            if candiate_paths.intersection(file_change_paths):
                candidates.append(candidate)

        return candidates
    

def compute_similarity_score(diff_one:TreeDiff, diff_two:TreeDiff):
    paths = {x.path:x for x in diff_one.files}

    other_paths = {x.path:x for x in diff_two.files}
    
    similar_paths = set(paths.keys()).intersection(set(other_paths.keys()))

    if len(similar_paths)==0:
        return 0
    
    total_score = 0

    for path in similar_paths:
        change1 =  paths[path]
        change2 = other_paths[path]
        
        total_score+= compute_similarity_score_for_change(change1, change2)
        
    return total_score/len(similar_paths) if len(similar_paths)>0 else 0



def compute_similarity_score_for_change(change:FileChange, other_change:FileChange):
    if change.path!=other_change.path:
        return 0
    else:
        if change.status!=other_change.status:
            if change.status=="deleted" or other_change.status=="deleted":
                return 0
            else:
                return 20
        else:
            if change.status!="modified":
                return 100
            else:
                additions1 = [x.content for x in change.additions]
                additions2 = [x.content for x in other_change.additions]

                deletions1 = [x.content for x in change.deletions]
                deletions2 = [x.content for x in other_change.deletions]

                add_score = compute_changeset_score(additions1, additions2)
                del_score = compute_changeset_score(deletions1, deletions2)
            
                matching_score = 0
                if add_score.total==0:
                    matching_score = del_score.score
                elif del_score.total==0:
                    matching_score = add_score.score
                else:
                    matching_score = (add_score.score+del_score.score)/2
                
                return 20+ matching_score*80/100
    
@dataclass
class SimilarityScore:
    score:float
    match_count:int
    total:int

def compute_changeset_score(sequence1:list[str], sequence2:list[str]) -> SimilarityScore:
    additions, deletions = match_sequences(sequence1, sequence2)

    not_matched = len(additions)+len(deletions)
    total = len(sequence1)+len(sequence2)
    matched =  total - not_matched

    # Matches are counted twice
    unique_match_count = int(matched/2)

    final_score = matched/total*100 if total>0 else 25

    return SimilarityScore(final_score, unique_match_count, total)
    
