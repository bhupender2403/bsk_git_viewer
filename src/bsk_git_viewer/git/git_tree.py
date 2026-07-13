
from dulwich.repo import Repo
from dulwich.objects import Tree, Blob

from bsk_git_viewer.models import GitTreeNode



class DulwichTreeLoader:
    """
    Loads GitTreeNode for each commit in the repository

    - Read and create only the structure, does not load data in blobs.
    """
    def __init__(self, repo: Repo):
        self.repo = repo
        self.store = self.repo.object_store

    def load_commit_tree(self, commit_id: str) -> GitTreeNode:
        commit = self.store[commit_id.encode()]
        tree = self.store[commit.tree]

        return self._load_tree(
            tree=tree,
            name="",
            path="",
            object_id=commit.tree.decode(),
            mode="040000",
        )

    def _load_tree(
        self,
        tree: Tree,
        name: str,
        path: str,
        object_id: str,
        mode: str,
    ) -> GitTreeNode:
        node = GitTreeNode(
            name=name,
            path=path,
            type="tree",
            object_id=object_id,
            mode=mode,
        )

        for entry in tree.iteritems():
            child_name = entry.path.decode()
            child_path = f"{path}/{child_name}" if path else child_name
            child_id = entry.sha
            child_obj = self.store[child_id]

            if isinstance(child_obj, Tree):
                child_node = self._load_tree(
                    tree=child_obj,
                    name=child_name,
                    path=child_path,
                    object_id=child_id.decode(),
                    mode=oct(entry.mode),
                )
            elif isinstance(child_obj, Blob):
                child_node = GitTreeNode(
                    name=child_name,
                    path=child_path,
                    type="blob",
                    object_id=child_id.decode(),
                    mode=oct(entry.mode),
                )
            else:
                child_node = GitTreeNode(
                    name=child_name,
                    path=child_path,
                    type=type(child_obj).__name__,
                    object_id=child_id.decode(),
                    mode=oct(entry.mode),
                )

            node.children.append(child_node)

        return node