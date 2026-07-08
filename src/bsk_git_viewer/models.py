from dataclasses import dataclass
from pathlib import Path


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



