#!/usr/bin/env python3
"""
Run a simple Git scenario language against a target directory using Dulwich.

Example scenario
----------------
init
write#src/tmp.txt#new#add initial file
data to be written
write_end
write#src/tmp.txt#append#append more data
data to write
write_end
create_branch#feature
change_branch#feature
write#src/tmp.txt#append#update file on feature
feature data
write_end
change_branch_main
merge_branch_with_main#feature

Supported commands
------------------
init
init#main_branch
write#path#new|append|overwrite#commit_message
    <multiline content>
write_end
write_no_commit#path#new|append|overwrite
    <multiline content>
write_end
mkdir#path
touch#path
delete#path#commit_message
rename#old_path#new_path#commit_message
copy#source_path#destination_path#commit_message
add#path
add_all
commit#message
create_branch#name
create_branch#name#start_point
change_branch#name
change_branch_main
merge_branch#name
merge_branch#name#commit_message
merge_branch_with_main
merge_branch_with_main#name
delete_branch#name
tag#name
tag#name#message
delete_tag#name
reset_hard#commit_or_ref
reset_mixed#commit_or_ref
status
log
log#count
show_head
list_branches
list_tags
current_branch
comment#anything
# anything

Notes
-----
* Paths are resolved inside the target directory. Escaping it with ".." is
  rejected.
* A write/delete/rename/copy command stages and commits automatically when a
  commit message is supplied.
* `merge_branch_with_main` merges the currently checked-out non-main branch
  into the configured main branch. It first switches to main.
* The script is intended for constructing test repositories and Git histories.
"""

from __future__ import annotations

import argparse
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from dulwich import porcelain
from dulwich.errors import NotGitRepository
from dulwich.repo import Repo


DEFAULT_AUTHOR = b"Git Scenario Runner <scenario@example.com>"


class ScenarioError(RuntimeError):
    """Raised when a scenario command is invalid or cannot be executed."""


@dataclass(frozen=True)
class ParsedCommand:
    """A single parsed scenario command."""

    name: str
    args: tuple[str, ...]
    line_number: int
    block: str | None = None


class GitScenarioRunner:
    """Execute scenario commands against one working-tree repository."""

    def __init__(
        self,
        directory: str | Path,
        *,
        author: bytes = DEFAULT_AUTHOR,
        default_main_branch: str = "main",
        verbose: bool = True,
    ) -> None:
        self.root = Path(directory).expanduser().resolve()
        self.author = author
        self.main_branch = default_main_branch
        self.verbose = verbose
        self.last_created_branch: str | None = None

    def run(self, commands: Iterable[ParsedCommand]) -> None:
        """Execute parsed commands in order."""

        self.root.mkdir(parents=True, exist_ok=True)

        for command in commands:
            self._print(
                f"[line {command.line_number}] "
                f"{command.name}"
                + (f"#{'#'.join(command.args)}" if command.args else "")
            )
            self.execute(command)

    def execute(self, command: ParsedCommand) -> None:
        """Dispatch one command to its implementation."""

        handlers = {
            "init": self._cmd_init,
            "write": self._cmd_write,
            "write_no_commit": self._cmd_write_no_commit,
            "mkdir": self._cmd_mkdir,
            "touch": self._cmd_touch,
            "delete": self._cmd_delete,
            "rename": self._cmd_rename,
            "copy": self._cmd_copy,
            "add": self._cmd_add,
            "add_all": self._cmd_add_all,
            "commit": self._cmd_commit,
            "create_branch": self._cmd_create_branch,
            "change_branch": self._cmd_change_branch,
            "change_branch_main": self._cmd_change_branch_main,
            "merge_branch": self._cmd_merge_branch,
            "merge_branch_with_main": self._cmd_merge_branch_with_main,
            "delete_branch": self._cmd_delete_branch,
            "tag": self._cmd_tag,
            "delete_tag": self._cmd_delete_tag,
            "reset_hard": self._cmd_reset_hard,
            "reset_mixed": self._cmd_reset_mixed,
            "status": self._cmd_status,
            "log": self._cmd_log,
            "show_head": self._cmd_show_head,
            "list_branches": self._cmd_list_branches,
            "list_tags": self._cmd_list_tags,
            "current_branch": self._cmd_current_branch,
            "comment": lambda _: None,
        }

        handler = handlers.get(command.name)
        if handler is None:
            raise ScenarioError(
                f"Line {command.line_number}: unknown command "
                f"{command.name!r}"
            )

        try:
            handler(command)
        except ScenarioError:
            raise
        except Exception as exc:
            raise ScenarioError(
                f"Line {command.line_number}: {command.name} failed: {exc}"
            ) from exc

    # ------------------------------------------------------------------
    # Repository helpers
    # ------------------------------------------------------------------

    def _repo(self) -> Repo:
        try:
            return Repo(str(self.root))
        except NotGitRepository as exc:
            raise ScenarioError(
                f"{self.root} is not initialized. Run 'init' first."
            ) from exc

    def _safe_path(self, relative_path: str) -> Path:
        if not relative_path:
            raise ScenarioError("Path cannot be empty")

        candidate = (self.root / relative_path).resolve()

        try:
            candidate.relative_to(self.root)
        except ValueError as exc:
            raise ScenarioError(
                f"Path escapes target directory: {relative_path!r}"
            ) from exc

        if candidate == self.root:
            raise ScenarioError("Command cannot target repository root")

        return candidate

    def _relative_path(self, path: Path) -> str:
        return path.relative_to(self.root).as_posix()

    def _head_exists(self, repo: Repo) -> bool:
        try:
            repo.head()
            return True
        except Exception:
            return False

    def _current_branch_name(self, repo: Repo | None = None) -> str | None:
        repo = repo or self._repo()
        head_ref = repo.refs.read_ref(b"HEAD")

        if head_ref is None:
            return None

        if isinstance(head_ref, bytes) and head_ref.startswith(
            b"refs/heads/"
        ):
            return head_ref.removeprefix(b"refs/heads/").decode(
                "utf-8",
                errors="replace",
            )

        return None

    def _branch_ref(self, branch_name: str) -> bytes:
        clean_name = branch_name.strip()
        if not clean_name:
            raise ScenarioError("Branch name cannot be empty")
        return b"refs/heads/" + clean_name.encode("utf-8")

    def _switch_branch(self, branch_name: str) -> None:
        """
        Switch HEAD and update the working tree.

        `porcelain.checkout_branch` is used when available. The fallback uses
        `porcelain.checkout`, which is present in newer Dulwich releases.
        """

        repo = self._repo()
        branch_ref = self._branch_ref(branch_name)

        if branch_ref not in repo.refs:
            raise ScenarioError(f"Branch does not exist: {branch_name!r}")

        checkout_branch = getattr(porcelain, "checkout_branch", None)
        if callable(checkout_branch):
            checkout_branch(repo, branch_name)
            return

        checkout = getattr(porcelain, "checkout", None)
        if callable(checkout):
            checkout(repo, branch_name)
            return

        raise ScenarioError(
            "This Dulwich version has neither checkout_branch() nor "
            "checkout(). Upgrade Dulwich."
        )

    def _stage_and_commit(self, paths: list[str], message: str) -> bytes:
        repo = self._repo()

        if paths:
            porcelain.add(repo, paths=paths)

        return porcelain.commit(
            repo,
            message=message.encode("utf-8"),
            author=self.author,
            committer=self.author,
        )

    def _print(self, message: object) -> None:
        if self.verbose:
            print(message)

    # ------------------------------------------------------------------
    # Commands
    # ------------------------------------------------------------------

    def _cmd_init(self, command: ParsedCommand) -> None:
        self._require_arg_count(command, minimum=0, maximum=1)

        if (self.root / ".git").exists():
            raise ScenarioError(f"Repository already exists at {self.root}")

        if command.args:
            self.main_branch = command.args[0]

        repo = porcelain.init(str(self.root))

        # Configure the unborn HEAD before the first commit.
        repo.refs.set_symbolic_ref(
            b"HEAD",
            self._branch_ref(self.main_branch),
        )

        self._print(
            f"Initialized repository with main branch "
            f"{self.main_branch!r}"
        )

    def _cmd_write(self, command: ParsedCommand) -> None:
        self._require_arg_count(command, minimum=3, maximum=3)
        path_arg, mode, message = command.args

        self._write_file(path_arg, mode, command.block)

        self._stage_and_commit([path_arg], message)

    def _cmd_write_no_commit(self, command: ParsedCommand) -> None:
        self._require_arg_count(command, minimum=2, maximum=2)
        path_arg, mode = command.args
        self._write_file(path_arg, mode, command.block)

    def _write_file(
        self,
        path_arg: str,
        mode: str,
        content: str | None,
    ) -> None:
        path = self._safe_path(path_arg)
        path.parent.mkdir(parents=True, exist_ok=True)

        normalized_mode = mode.strip().lower()
        content = content or ""

        if normalized_mode == "new":
            if path.exists():
                raise ScenarioError(
                    f"File already exists for 'new' mode: {path_arg!r}"
                )
            path.write_text(content, encoding="utf-8")

        elif normalized_mode in {"overwrite", "replace"}:
            path.write_text(content, encoding="utf-8")

        elif normalized_mode == "append":
            with path.open("a", encoding="utf-8") as file:
                file.write(content)

        else:
            raise ScenarioError(
                "Write mode must be one of: new, append, overwrite"
            )

    def _cmd_mkdir(self, command: ParsedCommand) -> None:
        self._require_arg_count(command, minimum=1, maximum=1)
        self._safe_path(command.args[0]).mkdir(
            parents=True,
            exist_ok=True,
        )

    def _cmd_touch(self, command: ParsedCommand) -> None:
        self._require_arg_count(command, minimum=1, maximum=1)
        path = self._safe_path(command.args[0])
        path.parent.mkdir(parents=True, exist_ok=True)
        path.touch(exist_ok=True)

    def _cmd_delete(self, command: ParsedCommand) -> None:
        self._require_arg_count(command, minimum=2, maximum=2)
        path_arg, message = command.args
        path = self._safe_path(path_arg)

        if not path.exists():
            raise ScenarioError(f"Path does not exist: {path_arg!r}")

        if path.is_dir():
            shutil.rmtree(path)
        else:
            path.unlink()

        # `porcelain.add` records tracked deletions when passed the path.
        self._stage_and_commit([path_arg], message)

    def _cmd_rename(self, command: ParsedCommand) -> None:
        self._require_arg_count(command, minimum=3, maximum=3)
        old_arg, new_arg, message = command.args
        old_path = self._safe_path(old_arg)
        new_path = self._safe_path(new_arg)

        if not old_path.exists():
            raise ScenarioError(f"Source path does not exist: {old_arg!r}")
        if new_path.exists():
            raise ScenarioError(
                f"Destination already exists: {new_arg!r}"
            )

        new_path.parent.mkdir(parents=True, exist_ok=True)
        old_path.rename(new_path)

        self._stage_and_commit([old_arg, new_arg], message)

    def _cmd_copy(self, command: ParsedCommand) -> None:
        self._require_arg_count(command, minimum=3, maximum=3)
        source_arg, destination_arg, message = command.args
        source = self._safe_path(source_arg)
        destination = self._safe_path(destination_arg)

        if not source.exists() or not source.is_file():
            raise ScenarioError(
                f"Source file does not exist: {source_arg!r}"
            )

        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)

        self._stage_and_commit([destination_arg], message)

    def _cmd_add(self, command: ParsedCommand) -> None:
        self._require_arg_count(command, minimum=1, maximum=1)
        porcelain.add(self._repo(), paths=[command.args[0]])

    def _cmd_add_all(self, command: ParsedCommand) -> None:
        self._require_arg_count(command, minimum=0, maximum=0)
        porcelain.add(self._repo(), paths=["."])

    def _cmd_commit(self, command: ParsedCommand) -> None:
        self._require_arg_count(command, minimum=1, maximum=1)
        porcelain.commit(
            self._repo(),
            message=command.args[0].encode("utf-8"),
            author=self.author,
            committer=self.author,
        )

    def _cmd_create_branch(self, command: ParsedCommand) -> None:
        self._require_arg_count(command, minimum=1, maximum=2)
        branch_name = command.args[0]
        start_point = command.args[1] if len(command.args) == 2 else None

        if not self._head_exists(self._repo()) and start_point is None:
            raise ScenarioError(
                "Create the first commit before creating a branch"
            )

        kwargs = {}
        if start_point is not None:
            kwargs["objectish"] = start_point

        porcelain.branch_create(
            self._repo(),
            branch_name,
            **kwargs,
        )
        self.last_created_branch = branch_name

    def _cmd_change_branch(self, command: ParsedCommand) -> None:
        self._require_arg_count(command, minimum=1, maximum=1)
        self._switch_branch(command.args[0])

    def _cmd_change_branch_main(self, command: ParsedCommand) -> None:
        self._require_arg_count(command, minimum=0, maximum=0)
        self._switch_branch(self.main_branch)

    def _cmd_merge_branch(self, command: ParsedCommand) -> None:
        self._require_arg_count(command, minimum=1, maximum=2)
        branch_name = command.args[0]
        message = (
            command.args[1]
            if len(command.args) == 2
            else f"Merge branch '{branch_name}'"
        )

        porcelain.merge(
            self._repo(),
            branch_name,
            message=message.encode("utf-8"),
            author=self.author,
            committer=self.author,
        )

    def _cmd_merge_branch_with_main(
        self,
        command: ParsedCommand,
    ) -> None:
        self._require_arg_count(command, minimum=0, maximum=1)

        source_branch = (
            command.args[0]
            if command.args
            else self._current_branch_name()
        )

        if source_branch == self.main_branch:
            source_branch = self.last_created_branch

        if not source_branch:
            raise ScenarioError(
                "Cannot determine branch to merge. Use "
                "'merge_branch_with_main#branch_name'."
            )

        self._switch_branch(self.main_branch)

        message = f"Merge branch '{source_branch}' into {self.main_branch}"
        porcelain.merge(
            self._repo(),
            source_branch,
            message=message.encode("utf-8"),
            author=self.author,
            committer=self.author,
        )

    def _cmd_delete_branch(self, command: ParsedCommand) -> None:
        self._require_arg_count(command, minimum=1, maximum=1)
        branch_name = command.args[0]

        if branch_name == self._current_branch_name():
            raise ScenarioError("Cannot delete the current branch")

        porcelain.branch_delete(self._repo(), branch_name)

    def _cmd_tag(self, command: ParsedCommand) -> None:
        self._require_arg_count(command, minimum=1, maximum=2)
        tag_name = command.args[0]

        if len(command.args) == 1:
            porcelain.tag_create(self._repo(), tag_name)
        else:
            porcelain.tag_create(
                self._repo(),
                tag_name,
                message=command.args[1].encode("utf-8"),
                tagger=self.author,
            )

    def _cmd_delete_tag(self, command: ParsedCommand) -> None:
        self._require_arg_count(command, minimum=1, maximum=1)
        porcelain.tag_delete(self._repo(), command.args[0])

    def _cmd_reset_hard(self, command: ParsedCommand) -> None:
        self._require_arg_count(command, minimum=1, maximum=1)
        self._reset(command.args[0], mode="hard")

    def _cmd_reset_mixed(self, command: ParsedCommand) -> None:
        self._require_arg_count(command, minimum=1, maximum=1)
        self._reset(command.args[0], mode="mixed")

    def _reset(self, target: str, *, mode: str) -> None:
        """
        Use the modern enum when available and fall back to legacy arguments.
        """

        reset_mode = getattr(porcelain, "ResetMode", None)

        if reset_mode is not None:
            enum_value = getattr(reset_mode, mode.upper())
            porcelain.reset(
                self._repo(),
                mode=enum_value,
                treeish=target,
            )
            return

        if mode == "hard":
            porcelain.reset(
                self._repo(),
                target,
                hard=True,
            )
        else:
            porcelain.reset(self._repo(), target)

    def _cmd_status(self, command: ParsedCommand) -> None:
        self._require_arg_count(command, minimum=0, maximum=0)
        self._print(porcelain.status(self._repo()))

    def _cmd_log(self, command: ParsedCommand) -> None:
        self._require_arg_count(command, minimum=0, maximum=1)
        count = int(command.args[0]) if command.args else None
        porcelain.log(self._repo(), max_entries=count)

    def _cmd_show_head(self, command: ParsedCommand) -> None:
        self._require_arg_count(command, minimum=0, maximum=0)
        repo = self._repo()

        if not self._head_exists(repo):
            self._print("HEAD is unborn")
            return

        commit = repo[repo.head()]
        self._print(
            {
                "commit_id": commit.id.decode("ascii"),
                "parents": [
                    parent.decode("ascii")
                    for parent in commit.parents
                ],
                "message": commit.message.decode(
                    "utf-8",
                    errors="replace",
                ).rstrip(),
            }
        )

    def _cmd_list_branches(self, command: ParsedCommand) -> None:
        self._require_arg_count(command, minimum=0, maximum=0)
        branches = [
            branch.decode("utf-8", errors="replace")
            if isinstance(branch, bytes)
            else str(branch)
            for branch in porcelain.branch_list(self._repo())
        ]
        self._print(branches)

    def _cmd_list_tags(self, command: ParsedCommand) -> None:
        self._require_arg_count(command, minimum=0, maximum=0)
        tags = [
            tag.decode("utf-8", errors="replace")
            if isinstance(tag, bytes)
            else str(tag)
            for tag in porcelain.tag_list(self._repo())
        ]
        self._print(tags)

    def _cmd_current_branch(self, command: ParsedCommand) -> None:
        self._require_arg_count(command, minimum=0, maximum=0)
        self._print(self._current_branch_name())

    def _git_directory(self) -> Path:
        """
        Return the repository's Git metadata directory.
        """

        dot_git = self.root / ".git"

        if dot_git.is_dir():
            return dot_git

        if dot_git.is_file():
            content = dot_git.read_text(
                encoding="utf-8",
                errors="replace",
            ).strip()

            prefix = "gitdir:"

            if content.lower().startswith(prefix):
                git_dir = content[len(prefix):].strip()
                return (self.root / git_dir).resolve()

        raise ScenarioError(
            f"Could not locate Git metadata directory for {self.root}"
        )


    def _is_rebase_in_progress(self) -> bool:
        git_dir = self._git_directory()

        return (
            (git_dir / "rebase-merge").exists()
            or (git_dir / "rebase-apply").exists()
        )
    
    def _cmd_rebase_onto(self, command: ParsedCommand) -> None:
        """
        Rebase commits after `upstream` onto `new_base`.

        Scenario syntax:

            rebase_onto#new_base#upstream

        Equivalent to:

            git rebase --onto new_base upstream
        """

        self._require_arg_count(
            command,
            minimum=2,
            maximum=2,
        )

        new_base, upstream = command.args

        result = self._run_native_git(
            "rebase",
            "--onto",
            new_base,
            upstream,
            check=False,
        )

        if result.returncode != 0:
            if self._is_rebase_in_progress():
                raise ScenarioError(
                    "Rebase stopped because of conflicts. Resolve and stage "
                    "the files, then run 'rebase_continue'."
                )

            details = result.stderr.strip() or result.stdout.strip()
            raise ScenarioError(f"Rebase failed: {details}")

    def _cmd_rebase_continue(
        self,
        command: ParsedCommand,
    ) -> None:
        """
        Continue a rebase after conflicts have been resolved and staged.
        """

        self._require_arg_count(
            command,
            minimum=0,
            maximum=0,
        )

        if not self._is_rebase_in_progress():
            raise ScenarioError("No rebase is currently in progress")

        result = self._run_native_git(
            "rebase",
            "--continue",
            check=False,
        )

        if result.returncode != 0:
            details = result.stderr.strip() or result.stdout.strip()

            if self._is_rebase_in_progress():
                raise ScenarioError(
                    "Rebase could not continue. There may still be unresolved "
                    f"conflicts.\n{details}"
                )

            raise ScenarioError(f"Rebase continue failed: {details}")


    def _cmd_rebase_abort(
        self,
        command: ParsedCommand,
    ) -> None:
        """
        Abort the current rebase and restore its original branch state.
        """

        self._require_arg_count(
            command,
            minimum=0,
            maximum=0,
        )

        if not self._is_rebase_in_progress():
            raise ScenarioError("No rebase is currently in progress")

        self._run_native_git(
            "rebase",
            "--abort",
        )

    def _cmd_rebase_skip(
        self,
        command: ParsedCommand,
    ) -> None:
        """
        Skip the current commit during an active rebase.
        """

        self._require_arg_count(
            command,
            minimum=0,
            maximum=0,
        )

        if not self._is_rebase_in_progress():
            raise ScenarioError("No rebase is currently in progress")

        result = self._run_native_git(
            "rebase",
            "--skip",
            check=False,
        )

        if result.returncode != 0:
            details = result.stderr.strip() or result.stdout.strip()
            raise ScenarioError(f"Rebase skip failed: {details}")


    @staticmethod
    def _require_arg_count(
        command: ParsedCommand,
        *,
        minimum: int,
        maximum: int,
    ) -> None:
        count = len(command.args)

        if minimum <= count <= maximum:
            return

        if minimum == maximum:
            expected = str(minimum)
        else:
            expected = f"{minimum}-{maximum}"

        raise ScenarioError(
            f"Line {command.line_number}: command {command.name!r} "
            f"expects {expected} arguments, got {count}"
        )


def parse_scenario(text: str) -> list[ParsedCommand]:
    """
    Parse scenario text into commands.

    `write` and `write_no_commit` consume all following lines until
    `write_end`. The block content preserves line breaks.
    """

    lines = text.splitlines(keepends=True)
    commands: list[ParsedCommand] = []
    index = 0

    while index < len(lines):
        raw_line = lines[index]
        line_number = index + 1
        stripped = raw_line.strip()
        index += 1

        if not stripped:
            continue

        if stripped.startswith("#"):
            continue

        parts = [part.strip() for part in stripped.split("#")]
        command_name = parts[0].lower()
        args = tuple(parts[1:])

        if command_name in {"write", "write_no_commit"}:
            content_lines: list[str] = []

            while index < len(lines):
                candidate = lines[index]

                if candidate.strip() == "write_end":
                    index += 1
                    break

                content_lines.append(candidate)
                index += 1
            else:
                raise ScenarioError(
                    f"Line {line_number}: write block has no write_end"
                )

            commands.append(
                ParsedCommand(
                    name=command_name,
                    args=args,
                    line_number=line_number,
                    block="".join(content_lines),
                )
            )
            continue

        if command_name == "write_end":
            raise ScenarioError(
                f"Line {line_number}: unexpected write_end"
            )

        commands.append(
            ParsedCommand(
                name=command_name,
                args=args,
                line_number=line_number,
            )
        )

    return commands


def run_scenario_file(
    scenario_path: str | Path,
    target_directory: str | Path,
    *,
    author_name: str = "Git Scenario Runner",
    author_email: str = "scenario@example.com",
    default_main_branch: str = "main",
    verbose: bool = True,
) -> None:
    """Read and execute a scenario file."""

    scenario_file = Path(scenario_path).expanduser().resolve()

    if not scenario_file.is_file():
        raise ScenarioError(
            f"Scenario file does not exist: {scenario_file}"
        )

    author = f"{author_name} <{author_email}>".encode("utf-8")
    commands = parse_scenario(
        scenario_file.read_text(encoding="utf-8")
    )

    runner = GitScenarioRunner(
        target_directory,
        author=author,
        default_main_branch=default_main_branch,
        verbose=verbose,
    )
    runner.run(commands)


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Execute a line-based Git scenario against a directory "
            "using Dulwich."
        )
    )
    parser.add_argument(
        "scenario",
        help="Path to the scenario text file",
    )
    parser.add_argument(
        "directory",
        help="Directory in which to create or modify the repository",
    )
    parser.add_argument(
        "--author-name",
        default="Git Scenario Runner",
    )
    parser.add_argument(
        "--author-email",
        default="scenario@example.com",
    )
    parser.add_argument(
        "--main-branch",
        default="main",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
    )
    return parser


def main() -> int:
    parser = build_argument_parser()
    args = parser.parse_args()

    try:
        run_scenario_file(
            scenario_path=args.scenario,
            target_directory=args.directory,
            author_name=args.author_name,
            author_email=args.author_email,
            default_main_branch=args.main_branch,
            verbose=not args.quiet,
        )
    except ScenarioError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())