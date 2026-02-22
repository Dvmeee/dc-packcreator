# dc-packcreator

A simple Python tool that bundles a folder into a `.zip` pack file.

---

## Folder structure

```
dc-packcreator/
├── src/
│   ├── __init__.py
│   └── packcreator.py   ← main script
├── tests/
│   ├── __init__.py
│   └── test_packcreator.py
├── output/              ← generated packs are saved here
├── .gitignore
├── requirements.txt
└── README.md
```

---

## Prerequisites

| Requirement | Version |
|-------------|---------|
| Python      | ≥ 3.10  |
| VSCode      | latest  |

> **Tip:** Install the official **Python** extension for VSCode
> (`ms-python.python`) for syntax highlighting, IntelliSense and integrated
> debugging.

---

## Setup in VSCode

### 1 – Open the project

**Mac / Windows:**  
`File → Open Folder …` and select the `dc-packcreator` folder.

---

### 2 – Create a virtual environment

Open the integrated terminal (`View → Terminal` or `` Ctrl+` ``) and run:

**Mac / Linux**
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

**Windows (PowerShell)**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

> If PowerShell blocks script execution, run
> `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once.

---

### 3 – Select the Python interpreter in VSCode

1. Press `Ctrl+Shift+P` (Mac: `Cmd+Shift+P`) → **Python: Select Interpreter**
2. Choose the interpreter inside `.venv` (shown as `('.venv': venv)`).

---

## Usage

Run the script from the project root:

**Mac / Linux**
```bash
python -m src.packcreator <source_folder> [--output output/] [--name my_pack]
```

**Windows (PowerShell / CMD)**
```powershell
python -m src.packcreator <source_folder> [--output output/] [--name my_pack]
```

### Example

```bash
# Pack a folder called "my_datapack" into output/my_datapack_20260101_120000.zip
python -m src.packcreator my_datapack
```

```bash
# Give the pack a custom name
python -m src.packcreator my_datapack --name release_v1
# → output/release_v1.zip
```

---

## Run tests

```bash
python -m unittest discover -s tests
```

---

## Run & Debug in VSCode (optional)

Create `.vscode/launch.json` in the project root with the following content to
enable **Run → Start Debugging** (`F5`):

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "dc-packcreator",
      "type": "debugpy",
      "request": "launch",
      "module": "src.packcreator",
      "args": ["my_datapack", "--name", "debug_pack"],
      "cwd": "${workspaceFolder}",
      "console": "integratedTerminal"
    }
  ]
}
```

Adjust the `args` list to point to the folder you want to pack.
