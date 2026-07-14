

from difflib import SequenceMatcher

from bsk_git_viewer.models import LineChange


def match_sequences(old_lines, new_lines):
    additions: list[LineChange] = []
    deletions: list[LineChange] = []

    matcher = SequenceMatcher(None, old_lines, new_lines)

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            continue

        if tag in ("delete", "replace"):
            for old_line_no, line in enumerate(old_lines[i1:i2], start=i1 + 1):
                deletions.append(
                    LineChange(
                        type="delete",
                        old_line=old_line_no,
                        new_line=None,
                        content=line,
                    )
                )

        if tag in ("insert", "replace"):
            for new_line_no, line in enumerate(new_lines[j1:j2], start=j1 + 1):
                additions.append(
                    LineChange(
                        type="add",
                        old_line=None,
                        new_line=new_line_no,
                        content=line,
                    )
                )

    return additions, deletions
