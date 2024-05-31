# alt-bins

alt-bins is a line-oriented query alt linux binary packages tool.
Outputs JSON with all packages that are in the aux branch but are missing in main branch,
all packages that are in the main branch but are missing in aux branch, also all packages
in main which have higher version than in aux branch.

**package**

```json
{
    "name": "string",
    "epoch": 0,
    "version": "string",
    "release": "string",
    "arch": "string",
    "disttag": "string",
    "buildtime": 0,
    "source": "string"
}
```

**result output**

```json
{
    "arch": "string",
    "total_uniq_<aux_branch>": 0,
    "total_uniq_<main_branch>": 0,
    "total_higher_version": 0,
    "uniq_<aux_branch>": [package],
    "uniq_<main_branch>": [package],
    "higher_version": [package]
}
```
## Install

```bash
git clone https://github.com/a-shahov/test-task.git
cd test-task
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install "."
```

## Usage

```bash
alt-bins <main_branch> <aux_branch> <arch>
alt-bins --help
```

