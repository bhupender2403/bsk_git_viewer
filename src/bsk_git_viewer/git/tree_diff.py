from dataclasses import dataclass, field
from difflib import SequenceMatcher
from typing import Any, Literal

from bsk_git_viewer.models import FileChange, GitTreeNode, LineChange, TreeDiff






def flatten_tree(node: GitTreeNode) -> dict[str, GitTreeNode]:
    result: dict[str, GitTreeNode] = {}

    def walk(n: GitTreeNode) -> None:
        if n.type == "blob":
            result[n.path] = n
            return

        for child in n.children:
            walk(child)

    walk(node)
    return result


def is_probably_binary(data: bytes) -> bool:
    if b"\x00" in data:
        return True

    if not data:
        return False

    text_chars = bytearray({7, 8, 9, 10, 12, 13, 27})
    text_chars.extend(range(32, 127))

    non_text = data.translate(None, text_chars)
    return len(non_text) / len(data) > 0.30


def read_blob_bytes(repo, node: GitTreeNode) -> bytes:
    blob = repo.object_store[node.object_id.encode()]
    return blob.data


def read_blob_text(repo, node: GitTreeNode) -> str:
    data = read_blob_bytes(repo, node)
    return data.decode("utf-8", errors="replace")


def diff_text_lines(
    old_text: str,
    new_text: str,
) -> tuple[list[LineChange], list[LineChange]]:
    old_lines = old_text.splitlines()
    new_lines = new_text.splitlines()

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


def extract_tree_diff(
    repo,
    current_tree: GitTreeNode,
    parent_tree: GitTreeNode | None = None,
) -> TreeDiff:
    """
    Calculates diff between the given pair of GitTreeNode

    """
    diff = TreeDiff()

    current_files = flatten_tree(current_tree)
    parent_files = flatten_tree(parent_tree) if parent_tree else {}

    all_paths = sorted(set(current_files.keys()) | set(parent_files.keys()))

    for path in all_paths:
        old_node = parent_files.get(path)
        new_node = current_files.get(path)

        if old_node is None and new_node is not None:
            data = read_blob_bytes(repo, new_node)

            file_change = FileChange(
                path=path,
                status="added",
                old_object_id=None,
                new_object_id=new_node.object_id,
            )

            if is_probably_binary(data):
                file_change.status = "binary_changed"
            else:
                new_text = data.decode("utf-8", errors="replace")
                for line_no, line in enumerate(new_text.splitlines(), start=1):
                    file_change.additions.append(
                        LineChange(
                            type="add",
                            old_line=None,
                            new_line=line_no,
                            content=line,
                        )
                    )

            diff.files.append(file_change)

        elif old_node is not None and new_node is None:
            data = read_blob_bytes(repo, old_node)

            file_change = FileChange(
                path=path,
                status="deleted",
                old_object_id=old_node.object_id,
                new_object_id=None,
            )

            if is_probably_binary(data):
                file_change.status = "binary_changed"
            else:
                old_text = data.decode("utf-8", errors="replace")
                for line_no, line in enumerate(old_text.splitlines(), start=1):
                    file_change.deletions.append(
                        LineChange(
                            type="delete",
                            old_line=line_no,
                            new_line=None,
                            content=line,
                        )
                    )

            diff.files.append(file_change)

        elif old_node is not None and new_node is not None:
            if old_node.object_id == new_node.object_id:
                continue

            old_data = read_blob_bytes(repo, old_node)
            new_data = read_blob_bytes(repo, new_node)

            file_change = FileChange(
                path=path,
                status="modified",
                old_object_id=old_node.object_id,
                new_object_id=new_node.object_id,
            )

            if is_probably_binary(old_data) or is_probably_binary(new_data):
                file_change.status = "binary_changed"
                diff.files.append(file_change)
                continue

            old_text = old_data.decode("utf-8", errors="replace")
            new_text = new_data.decode("utf-8", errors="replace")

            additions, deletions = diff_text_lines(old_text, new_text)

            file_change.additions.extend(additions)
            file_change.deletions.extend(deletions)

            diff.files.append(file_change)

    return diff