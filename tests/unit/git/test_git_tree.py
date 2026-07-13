

from unittest.mock import MagicMock

from dulwich.objects import Blob, Commit, Tree
from dulwich.repo import Repo

from bsk_git_viewer.git.git_tree import DulwichTreeLoader, GitTreeNode


def make_entry(path: bytes, sha:bytes, mode:int):
    entry = MagicMock()
    entry.path = path
    entry.sha = sha
    entry.mode = mode
    return entry

def test_init_stores_repo_and_object_store():
    repo = MagicMock(spec = Repo)
    repo.object_store = MagicMock()

    loader = DulwichTreeLoader(repo)

    assert loader.repo is repo
    assert loader.store is repo.object_store

def test_laod_commit_tree_loads_root_tree(monkeypatch):
    repo = MagicMock(spec=Repo)
    store = MagicMock()
    repo.object_store = store

    commit = MagicMock(spec=Commit)
    commit.tree = b"root-tree-id"


    root_tree = MagicMock(spec = Tree)
    
    store.__getitem__.side_effect = lambda object_id:{
        b"commit-id":commit,
        b"root-tree-id":root_tree
    }[object_id]

    loader = DulwichTreeLoader(repo)

    expected_node = MagicMock(spec=GitTreeNode)
    mock_load_tree = MagicMock(return_value=expected_node)

    monkeypatch.setattr(loader,"_load_tree", mock_load_tree)

    result = loader.load_commit_tree("commit-id")

    assert result is expected_node

    mock_load_tree.assert_called_once_with(
        tree = root_tree,
        name = "",
        path = "",
        object_id = "root-tree-id",
        mode = "040000",
    )
    


def test_tree_load_add_child_blobs():
    repo = MagicMock(spec = Repo)
    store = MagicMock()
    repo.object_store = store

    blob = MagicMock(spec = Blob)
    blob_id = b"a"*40

    entry = make_entry(
        path  = b"README.md",
        sha = blob_id,
        mode = 0o100644,
    )

    tree = MagicMock(spec = Tree)
    tree.iteritems.return_value = [entry]

    store.__getitem__.return_value = blob

    loader = DulwichTreeLoader(repo)

    result = loader._load_tree(
        tree = tree,
        name = "",
        path = "",
        object_id = "root-id",
        mode= "040000"
    )

    assert result.name == ""
    assert result.path == ""
    assert result.type == "tree"
    assert result.object_id == "root-id"
    assert result.mode == "040000"

    assert len(result.children) == 1

    child = result.children[0]

    assert child.name == "README.md"
    assert child.path == "README.md"
    assert child.type == "blob"
    assert child.object_id == blob_id.decode()
    assert child.mode == oct(0o100644)


def test_load_tree_load_recursive_tree():
    repo = MagicMock(spec = Repo)
    store = MagicMock()
    repo.object_store = store

    directory_id = b"d"*40
    file_id = b"f"*40

    directory_entry = make_entry(
        path = b"src",
        sha = directory_id,
        mode = 0o040000
    )

    file_entry = make_entry(
        path = b"main.py",
        sha = file_id,
        mode = 0o100644
    )

    root_tree = MagicMock(spec = Tree)
    root_tree.iteritems.return_value = [directory_entry]

    src_tree = MagicMock(spec = Tree)
    src_tree.iteritems.return_value = [file_entry]

    blob = MagicMock(spec = Blob)
    

    store.__getitem__.side_effect = lambda object_id:{
        directory_id:src_tree,
        file_id : blob
    }[object_id]

    loader = DulwichTreeLoader(repo)

    result = loader._load_tree(
        tree = root_tree,
        name = "",
        path = "",
        object_id = "root-id",
        mode = "040000"
    )

    assert len(result.children)==1

    src_node = result.children[0]

    assert len(src_node.children) == 1
    assert src_node.object_id == directory_id.decode()

    file_node = src_node.children[0]

    assert file_node.object_id == file_id.decode()
    
    


    