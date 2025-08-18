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

- csv editor

```bash
cd aichallenge-trajectopry-editor
source .venv/bin/activate
./cmd_line/csv_editor
```

- csv converter from osm

  - デフォルトで、"../../workspace/src/aichallenge_submit/aichallenge_submit_launch/map/lanelet2_map.osm" を変換
  - "../../workspace/src/aichallenge_submit/aichallenge_submit_launch/map/lanelet2_map.osm" が生成される

    ```bash
    cd aichallenge-trajectopry-editor
    ./cmd_line/csv_from_osm
    ```

  - 引数指定で任意のファイルを変換

    ```bash
    cd aichallenge-trajectopry-editor
    ./cmd_line/csv_from_osm (osmファイル) (lane.csvファイル)
    ```

### 経路設計の考え方(isshy的な)

- 加速優先ライン（次の直線で最高速を稼ぐ）
- ステアはブレーキと考え、35kphの世界ではブレーキ無しで設計し、最後に調整
  - 現在の加減速制御に対する司令は難しい
- できるだけニュートラルステアで直進加速
- コーナーのクリッピングポイントを目指してカーブ経路
  - 第一コーナーは１周目の車速が低いのでマージンは多めに取る
    - 周回数による経路選択をすればもう少し攻めることが可能になる
- 複合コーナーは一つのコーナーと考えて経路設計
- インベタで走るか、減速を避けて大きく回るかはコーナーによる
- コーナー終了時に経路追従で左右にステアが振れてしまうので揺れ無いよう経路点を打つ
- 乱数要素で同一の経路は走れないのである程度のマージンは必要

#### 登録経路ファイルについて

- simple_pure_pursuit の初期状態での最速
  - aichallenge/workspace/src/aichallenge_submit/simple_trajectory_generator/data/raceline_awsim_isshy_35kph_11.csv
- simple_pure_pursuit に速度リミッタを入れた状態の最速経路
  - aichallenge/workspace/src/aichallenge_submit/simple_trajectory_generator/data/raceline_awsim_isshy_35kph_12.csv

### 経路追従に対して

- 経路点群ではなく、目標点だけの経路追従にしたい
- 目標点までの直進、目標点までの旋回 の繰り返しとする
- 減速が必要な場合、アクセルOFFとブレーキの使い方は定義したい
- システムとしてアクセルとブレーキの同時踏みが許可されているなら制御も変わる
  - おそらくブレーキONでアクセルOFFだろう。実車に乗ればわかる。  
