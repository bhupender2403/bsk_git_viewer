
import os

from dulwich.errors import NotGitRepository
from dulwich.repo import Repo
import pytest

from bsk_git_viewer.gitcreate.git_sceneria_creator import GitScenarioRunner, ScenarioError, parse_scenario


@pytest.mark.parametrize(
        "to_parse,count",
    [
        ("""init""", 1),
        (
"""init
write#src/tmp.txt#new#add initial file
data to be written
write_end
write#src/tmp.txt#append#append more data
data to write
write_end
create_branch#feature
""",4
        ),
        (
"""merge_branch#name#commit_message
merge_branch_with_main
merge_branch_with_main#name
delete_branch#name
tag#name
tag#name#message
delete_tag#name
reset_hard#commit_or_ref
reset_mixed#commit_or_ref
""",
       9 )

    ]
)
def test_parse_scenerios(to_parse, count):
    parsed = parse_scenario(to_parse)
    assert len(parsed)==count



def run_commands(command_text, target_directory):

    commands = parse_scenario(
        command_text
    )

    runner = GitScenarioRunner(target_directory)
    runner.run(commands)

def read_data(file_path):
    with open(file_path,"rt") as fd:
        return fd.read()

def test_git_scenerio_creator_basic_git_init(tmp_path):
    commandtext = """init"""
    
    with pytest.raises(NotGitRepository):
        repo = Repo(tmp_path)

    run_commands(commandtext, tmp_path)
    repo = Repo(tmp_path)
    assert repo is not None


    
def test_git_scenrio_creator_commit_and_delete(tmp_path):
    commandtext = """init
write#Readme.md#new#adding readme
This is a readme file
write_end"""

    assert not os.path.exists(tmp_path/"Readme.md")

    run_commands(commandtext, tmp_path)

    assert read_data(tmp_path/"Readme.md") == "This is a readme file\n"

    assert os.path.exists(tmp_path/"Readme.md")

    move_commands = """rename#Readme.md#Readme.v2#renaming file"""

    run_commands(move_commands, tmp_path)

    assert os.path.exists(tmp_path/"Readme.v2")

    assert not os.path.exists(tmp_path/"Readme.md")


    next_commands = """delete#Readme.v2#deleting readme file"""

    run_commands(next_commands,tmp_path)

    assert not os.path.exists(tmp_path/"Readme.v2")



def test_git_scenrio_creator_branch(tmp_path):
    commands =  """init
write#Readme.md#new#adding readme
This is a readme file
write_end"""

    run_commands(commands, tmp_path)

    assert os.path.exists(tmp_path/"Readme.md")

    createbranchcommands = """create_branch#feature
change_branch#feature
write#Readme.v2#new#adding readme
This is a readme file
write_end"""

    run_commands(createbranchcommands, tmp_path)

    assert os.path.exists(tmp_path/"Readme.md")

    assert os.path.exists(tmp_path/"Readme.v2")

    commands = "change_branch#main"

    run_commands(commands, tmp_path)

    assert os.path.exists(tmp_path/"Readme.md")

    assert not os.path.exists(tmp_path/"Readme.v2") 

    repo = Repo(tmp_path)
    branches = {
        ref.decode(): sha.decode()
        for ref, sha in repo.refs.as_dict().items()
        if ref.startswith(b"refs/heads/")
    }
    assert len(branches) == 2




def test_git_scenrio_merge(tmp_path):
    commands =  """init
write#Readme.md#new#adding readme
This is a readme file
write_end"""

    run_commands(commands, tmp_path)

    assert os.path.exists(tmp_path/"Readme.md")

    createbranchcommands = """create_branch#feature
change_branch#feature
write#Readme.v2#new#adding readme
This is a readme file
write_end"""

    run_commands(createbranchcommands, tmp_path)

    assert os.path.exists(tmp_path/"Readme.md")

    assert os.path.exists(tmp_path/"Readme.v2")

    commands = "change_branch#main"

    run_commands(commands, tmp_path)

    assert os.path.exists(tmp_path/"Readme.md")

    assert not os.path.exists(tmp_path/"Readme.v2") 

    repo = Repo(tmp_path)
    branches = {
        ref.decode(): sha.decode()
        for ref, sha in repo.refs.as_dict().items()
        if ref.startswith(b"refs/heads/")
    }
    assert len(branches) == 2

    merge_command = """merge_branch_with_main#feature
change_branch#main"""

    run_commands(merge_command,tmp_path)

    assert os.path.exists(tmp_path/"Readme.md")

    assert  os.path.exists(tmp_path/"Readme.v2") 






def test_git_scenrio_rebase(tmp_path):
    commands =  """init
write#Readme.md#new#adding readme
This is a readme file
write_end"""

    run_commands(commands, tmp_path)

    assert os.path.exists(tmp_path/"Readme.md")

    createbranchcommands = """create_branch#feature
change_branch#feature
write#Readme.v2#new#adding readme
This is a readme file
write_end"""

    run_commands(createbranchcommands, tmp_path)

    assert os.path.exists(tmp_path/"Readme.md")

    assert os.path.exists(tmp_path/"Readme.v2")

    commands = """change_branch_main
write#Readme.v3#new#adding readme
This is a readme file
write_end"""

    run_commands(commands, tmp_path)

    assert os.path.exists(tmp_path/"Readme.md")

    assert not os.path.exists(tmp_path/"Readme.v2") 

    assert os.path.exists(tmp_path/"Readme.v3") 

    repo = Repo(tmp_path)
    branches = {
        ref.decode(): sha.decode()
        for ref, sha in repo.refs.as_dict().items()
        if ref.startswith(b"refs/heads/")
    }
    assert len(branches) == 2

    run_commands("list_branches\nshow_head\nchange_branch#feature", tmp_path)

    merge_command = """rebase#main"""

    run_commands(merge_command,tmp_path)

    assert os.path.exists(tmp_path/"Readme.md")

    assert  os.path.exists(tmp_path/"Readme.v2") 

@pytest.mark.parametrize(
        "conflict_handler",
        [
            ("abort"),
            ("skip"),
            ("continue")
        ]
        
)
def test_git_scenrio_rebase_with_conflict(tmp_path, conflict_handler):
    commands =  """init
write#Readme.md#new#adding readme
This is a readme file
write_end"""

    run_commands(commands, tmp_path)

    assert os.path.exists(tmp_path/"Readme.md")

    createbranchcommands = """create_branch#feature
change_branch#feature
write#Readme.v2#new#adding readme
This is a readme file
write_end
write#src/Readme.v5#new#adding readme
This is a readme file
write_end
write#src/Readme.v6#new#adding readme
This is a readme file
write_end"""

    run_commands(createbranchcommands, tmp_path)

    assert os.path.exists(tmp_path/"Readme.md")

    assert os.path.exists(tmp_path/"Readme.v2")

    commands = """change_branch_main
write#Readme.v3#new#adding readme
This is a readme file
write_end
write#src/Readme.v5#new#adding readme
This is a removed file
something els is written
write_end"""

    run_commands(commands, tmp_path)

    with open(tmp_path/"src/Readme.v5","rt") as fd:
        v5main_data = fd.read()

    assert os.path.exists(tmp_path/"Readme.md")

    assert not os.path.exists(tmp_path/"Readme.v2") 

    assert os.path.exists(tmp_path/"Readme.v3") 

    repo = Repo(tmp_path)
    branches = {
        ref.decode(): sha.decode()
        for ref, sha in repo.refs.as_dict().items()
        if ref.startswith(b"refs/heads/")
    }
    assert len(branches) == 2

    run_commands("change_branch#feature", tmp_path)

    merge_command = """rebase#main"""

    with pytest.raises(ScenarioError):
        run_commands(merge_command,tmp_path)

    
    if conflict_handler=="abort":    
        resolve_commands = "rebase_abort"
    elif conflict_handler=="skip":
        resolve_commands = "rebase_skip"
    elif conflict_handler=="continue":
        final_data = """This is the data
with resolve"""
        resolve_commands = """write_no_commit#src/Readme.v5#overwrite
"""+final_data+"""
write_end
add#src/Readme.v5
rebase_continue
"""        


    run_commands(resolve_commands,tmp_path)

    commands = """change_branch#main"""
    run_commands(commands, tmp_path)

    if conflict_handler=="abort":
        assert not os.path.exists(tmp_path/"src/Readme.v6")        
        assert not os.path.exists(tmp_path/"Readme.v2")
    elif conflict_handler=="skip":
        commands = "rebase#feature"
        run_commands(commands,tmp_path)

        assert os.path.exists(tmp_path/"Readme.v2")

        assert os.path.exists(tmp_path/"src/Readme.v6")    
        assert os.path.exists(tmp_path/"src/Readme.v5")    
        
        with open(tmp_path/"src/Readme.v5","rt") as fd:
            v5main_data_after_rebase_skip = fd.read()
        assert v5main_data == v5main_data_after_rebase_skip
    elif conflict_handler =="conflict":
        commands = "rebase#feature"
        run_commands(commands,tmp_path)

        assert os.path.exists(tmp_path/"Readme.v2")

        assert os.path.exists(tmp_path/"src/Readme.v6")    
        assert os.path.exists(tmp_path/"src/Readme.v5")    
        
        with open(tmp_path/"src/Readme.v5","rt") as fd:
            v5main_data_after_rebase_continue = fd.read()
        assert final_data == v5main_data_after_rebase_continue

        
    
    











