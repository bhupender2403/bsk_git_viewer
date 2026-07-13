from dataclasses import dataclass
from pathlib import Path
from dataclasses import  field
from typing import Any

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