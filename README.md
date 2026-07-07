# Git Commands Viewer
---

Git Command Viewer is an interactive visualizer that reconstructs the possible git commands used in the history of a given git repository. It analyzes the data stored in the .git folders and objects to infer the git commands used and the order in which these are used. The git history is shown in an interactive way through a local web application where users can traverse through the git commands and can see how each command affected the git structure. 

This tool is useful for the beginners who are starting with the git and want to understand the git internals by looking at the effect of each command on the git repository in an interactive way. Also sometimes we or somebody else ask for our help in understanding why they are not able to checkin or push, this tool saves time in understanding how we have arrived at the current configuration. In addition to the current configuration it also shows some of the recently lost commits or refheads which help in recovering the correct configuration.

---

## Features
- Easy to use
- Zero configuration

---

## How does it work
- Parses the local git repository.
- Reconstruct the possible commit history
- Infer possible git commands that are used 
- Build the graph with the timeline
- Serve this information on local UI

---

## Installation
This tool can be installed using `pip install bks-git-viewer`

---

## Quick start
Once the library is installed just run the command `python -p  <todo> <path_to_local_repository>`

---

## Limitations
- Work only with local repositories.
- Not all the commands can be inferred right now.
- Read only does not change and affect git structure in any way.
- It can help identify the problem but can not fix it.
- It can be slow for bigger repositories

---

## License 
MIT License

---
