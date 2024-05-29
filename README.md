# alt-bins

alt-bins is a line-oriented query alt linux binary packages tool.
Outputs JSON with all packages that are in the p10 branch but are missing in sisyphus,
all packages that are in the sisyphus branch but are missing in p10, also all packages
in sisyphus which have higher version than in p10 branch.

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
    "total_uniq_p10": 0,
    "total_uniq_sisyphus": 0,
    "total_higher_version": 0,
    "uniq_p10": [package],
    "uniq_sisyphus": [package],
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
alt-bins <arch>
alt-bins --help
```

