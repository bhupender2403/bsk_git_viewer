

from bsk_git_viewer.models import  CommitWithPreDiff


def extract_candidates_for_similarity(commit:CommitWithPreDiff, commit_list:list[CommitWithPreDiff]):
    
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
    