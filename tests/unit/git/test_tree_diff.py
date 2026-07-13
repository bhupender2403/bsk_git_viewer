
from unittest.mock import MagicMock

from dulwich.objects import Blob
from dulwich.repo import Repo

from bsk_git_viewer.git.tree_diff import diff_text_lines, extract_tree_diff, flatten_tree, is_probably_binary
from bsk_git_viewer.models import FileChange, GitTreeNode

#========================================================================================
# flatten tree test
#========================================================================================

def test_flatten_tree_return_single_node():

    node = MagicMock(spec = GitTreeNode)
    node.type = "blob"
    node.path = "node"
    result = flatten_tree(node=node)

    assert len(result)== 1
    assert "node" in result


def test_flatten_tree_return_node_recursively():
    root = MagicMock(spec = GitTreeNode)
    root.type = "tree"
    root.path = "root"

    child = MagicMock(spec = GitTreeNode)
    child.type = "blob"
    child.path = "child"
    root.children = [child]

    result = flatten_tree(root)

    assert len(result) ==  1
    assert "root" not in result
    assert "child" in result


#========================================================================================
# diff text tests
#========================================================================================

def test_diff_test_no_change():
    additions,deletions = diff_text_lines("text","text")
    assert len(additions)==0
    assert len(deletions) == 0

def test_diff_test_pure_deletions():
    first_text = "line1"
    second_text = ""
    additions,deletions = diff_text_lines(first_text,second_text)

    assert len(deletions)==1
    assert len(additions)==0
    assert deletions[0].content=="line1"

def test_diff_test_pure_additions():
    first_text = ""
    second_text = "line1"
    additions,deletions = diff_text_lines(first_text,second_text)

    assert len(deletions)==0
    assert len(additions)==1
    assert additions[0].content=="line1"

def test_diff_test_both_addition_deletion():
    first_text ="f1\nf2\nf3"
    second_text = "f2\nf4\nf3"

    additions,deletions = diff_text_lines(first_text,second_text)

    assert len(deletions)==1
    assert len(additions)==1
    assert additions[0].content=="f4"
    assert deletions[0].content=="f1"



#========================================================================================
# tree diff tests
#========================================================================================

def make_mock_tree(path:str, type:str,object_id:str):
    tree = MagicMock(spec = GitTreeNode)
    tree.name = path
    tree.path = path
    tree.type = type
    tree.object_id = object_id
    tree.mode = "default"
    tree.children = []
    return tree


def test_extract_tree_diff_same_structure_no_diff():
    first_tree = make_mock_tree("first","tree", "first_id")

    first_file = make_mock_tree("first_file","blob","first_file_id")

    first_tree.children = [first_file]

    second_tree = make_mock_tree("second","tree","second_id")
    second_file = make_mock_tree("first_file","blob","first_file_id")
    second_tree.children = [second_file]

    repo = MagicMock(spec = Repo)
    store = MagicMock()
    repo.object_store = store
    
    # def fake_store_get(object_id):
        # return b"Same data is returned"
    
    store.__getitem__.side_effect = b"Same data is returned"

    result = extract_tree_diff(repo , first_tree, second_tree)

    assert len(result.files)==0


def test_extract_tree_diff_file_added():
    first_tree = make_mock_tree("first","tree", "first_id")


    second_tree = make_mock_tree("second","tree","second_id")
    second_file = make_mock_tree("first_file","blob","first_file_id")
    second_tree.children = [second_file]

    repo = MagicMock(spec = Repo)
    store = MagicMock()
    repo.object_store = store
    
    # def fake_store_get(object_id):
        # return b"Same data is returned"
    
    blob = MagicMock(Blob)
    blob.data = b"Same data is returned\nThis is new"

    store.__getitem__.side_effect = lambda x:blob


    result = extract_tree_diff(repo , first_tree, second_tree)

    assert len(result.files)==1
    assert check_present(result.files,"first_file","deleted")


def test_extract_tree_diff_file_deleted():
    first_tree = make_mock_tree("first","tree", "first_id")


    second_tree = make_mock_tree("second","tree","second_id")
    second_file = make_mock_tree("first_file","blob","first_file_id")
    first_tree.children = [second_file]

    repo = MagicMock(spec = Repo)
    store = MagicMock()
    repo.object_store = store
    
    # def fake_store_get(object_id):
        # return b"Same data is returned"
    
    blob = MagicMock(Blob)
    blob.data = b"Same data is returned\nThis is new"

    store.__getitem__.side_effect = lambda x:blob


    result = extract_tree_diff(repo , first_tree, second_tree)

    assert len(result.files)==1
    assert check_present(result.files,"first_file","added")


def test_extract_tree_diff_file_multiple_change():

    third_tree = make_mock_tree("third","tree","third_id")
    third_file = make_mock_tree("third_file","blob","third_file_id")
    third_tree.children = [third_file]


    first_tree = make_mock_tree("first","tree", "first_id")
    first_file = make_mock_tree("first_file","blob","first_file_id")
    first_tree.children = [first_file, third_tree]


    fourth_tree = make_mock_tree("third","tree","fourth_id")
    fourth_file = make_mock_tree("third_file","blob","third_file_id2")
    fourth_tree.children = [fourth_file]    

    second_tree = make_mock_tree("second","tree","second_id")
    second_file = make_mock_tree("second_file","blob","second_file_id")
    second_tree.children = [second_file, fourth_tree]

    repo = MagicMock(spec = Repo)
    store = MagicMock()
    repo.object_store = store
    
    def fake_store_get(object_id):
        blob = MagicMock(Blob)
        blob.data = object_id
        return blob

    store.__getitem__.side_effect = fake_store_get


    result = extract_tree_diff(repo , first_tree, second_tree)

    assert len(result.files)==3
    assert check_present(result.files,"first_file","added")
    assert check_present(result.files,"second_file","deleted")
    assert check_present(result.files,"third_file","modified")

def check_present(files:list[FileChange],file_path:str, status:str):
    for f in files:
        if f.path==file_path and f.status==status:
            return True
    return False


#========================================================================================
# is_probably_binary
#========================================================================================

def test_is_probably_binary():
    result = is_probably_binary(b"This is text")
    assert not result