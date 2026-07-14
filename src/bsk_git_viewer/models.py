from dataclasses import dataclass
from pathlib import Path
from dataclasses import  field
from typing import Any, Literal

@dataclass
class RepoContext:
    git_path:Path|str
    repo_path:Path|str


@dataclass
class CommitInfo:
    commit_id:str
    author:str
    message:str
    commit_time:int
    parents:list[str]

@dataclass
class TreeInfo:
    hash:str

@dataclass
class BranchInfo:
    name:str
    head_commit:str



@dataclass
class Repository:
    name:str
    commits:dict[str,CommitInfo]
    branches:dict[str,BranchInfo]



@dataclass
class GitTreeNode:
    name: str
    path: str
    type: str  # "tree" or "blob"
    object_id: str
    mode: str
    children: list["GitTreeNode"] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "path": self.path,
            "type": self.type,
            "object_id": self.object_id,
            "mode": self.mode,
            "children": [child.to_dict() for child in self.children],
        }
    

@dataclass
class LineChange:
    type: Literal["add", "delete"]
    old_line: int | None
    new_line: int | None
    content: str


@dataclass
class FileChange:
    path: str
    status: Literal["added", "deleted", "modified", "binary_changed"]
    old_object_id: str | None = None
    new_object_id: str | None = None
    additions: list[LineChange] = field(default_factory=list)
    deletions: list[LineChange] = field(default_factory=list)





@dataclass
class TreeDiff:
    files: list[FileChange] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "files": [
                {
                    "path": f.path,
                    "status": f.status,
                    "old_object_id": f.old_object_id,
                    "new_object_id": f.new_object_id,
                    "additions": [a.__dict__ for a in f.additions],
                    "deletions": [d.__dict__ for d in f.deletions],
                }
                for f in self.files
            ]
        }
    
@dataclass
class CommitWithTree:
    commit:CommitInfo
    gittree:GitTreeNode

@dataclass 
class CommitWithPreDiff:
    commit:CommitInfo
    pre_diff:TreeDiff