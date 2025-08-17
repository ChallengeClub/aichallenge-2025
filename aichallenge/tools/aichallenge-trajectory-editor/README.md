# aichallenge-trajectory-editor

Provides a trajectory editor and a tool for generating trajectory from raceline

## how to run

```bash
export PATH="$PATH:$HOME/aichallenge2024-trajectory-editor/cmd_line/"
```

run editor

```bash
csv_editor
```

run enerating trajectory from raceline

```bash
raceline_to_traj
```

## 本環境の作成情報

### 以下の手順でリポジトリをクローンしてgit情報を削除しております

```bash
# リポジトリをクローン
git clone https://github.com/AutomotiveAIChallenge/aichallenge-trajectory-editor.git

# ディレクトリに移動
cd aichallenge-trajectory-editor

# .git ディレクトリを削除し、履歴を消去
rm -rf .git
```

### 使い方

- python 環境

```bsh
cd aichallenge^trajectopry-editor
pyenv install 3.11.13
pyenv local 3.11.13
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

- editor

```bash
cd aichallenge^trajectopry-editor
./cmd_line/csv_editor
```
