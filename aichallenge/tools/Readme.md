# tools

このディレクトリには、開発補助・前処理用のスクリプトが含まれています。

---
## trajectory_raceline.py

カーブの曲率に応じて車両の速度を調整するツールです。  
特にカーブの「入口で減速」「出口で加速」するように速度プロファイルを補正します。

### 主な機能

- 軌道CSVファイルを読み込み
- 曲率を自動計算
- 曲率の変化（未来・過去）を基に速度を補正
- 新しい速度カラムを含んだCSVを保存

### 入出力ファイル例

- 入力: `workspace/src/aichallenge_submit/simple_trajectory_generator/data/raceline_awsim_15km.csv`
- 出力: `workspace/src/aichallenge_submit/simple_trajectory_generator/data/raceline_awsim_35km_adjusted.csv`

### 実行方法

Docker内で実行してください。
```bash
$ cd /aichallenge
$ python3 tools/trajectory_raceline.py 
```

## lanelet2_bounds_to_csv.py

Lanelet2形式（OSM）の地図からレーン境界線を抽出し、CSVとして出力するツールです。  
出力CSVには `local_x, local_y`（ローカル座標系）や緯度経度が含まれます。

### 主な機能
- Lanelet2の`relation`タグまたは`subtype`タグから境界線を自動抽出
- 左境界（left）、右境界（right）、センターライン（centerline）ごとに個別CSV出力
- すべての境界をまとめた単一CSV出力も可能

### 出力例（left.csv）
| lanelet_or_way_id | role  | index | latitude    | longitude   | local_x   | local_y   |
|-------------------|-------|-------|-------------|-------------|-----------|-----------|
| 101               | left  | 0     | 35.12345678 | 135.1234567 | 89630.123 | 43130.456 |

### 実行方法
Docker内で実行してください。
```bash
$ cd /aichallenge
$ python3 tools/lanelet2_bounds_to_csv.py
```
※ デフォルトで workspace/src/aichallenge_submit/aichallenge_submit_launch/map/lanelet2_map.osm を入力に、
tools/extracted_bounds/ に left.csv / right.csv / centerline.csv を出力します。

## visualize_bounds_and_trajectory.py

lanelet2_bounds_to_csv.py で出力した境界CSVと、走行軌跡（trajectory）CSVを重ねて2D表示するツールです。
境界はローカル座標系（local_x, local_y）で表示され、トラジェクトリと座標系を揃えられます。

### 主な機能

- 左・右・センターライン境界の点群描画（local座標系）
- トラジェクトリ（例: raceline_awsim_30km.csv）の点描画
- 像として保存（PNG）

### 実行方法
```
$ cd /aichallenge
$ python3 tools/visualize_bounds_and_trajectory.py
```
実行後、tools/extracted_bounds/preview_bounds_and_trajectory.png 
また、実行環境によっては同時にウィンドウ表示されます。
## edit_trajectory.py

レーン境界（left/right/centerline）の点群を背景に、トラジェクトリCSVをGUI上で編集できるツールです。  
トラジェクトリの各点は速度[km/h]に応じて着色され（カラーマップ: `jet`）、マウスやキーボードで位置や速度を変更できます。  
保存時は元のCSV構造を極力維持しつつ、`x`,`y`,`speed`（m/s）を上書きします。

### 主な機能
- レーン左右・センターを黒い細点で表示（`local_x,local_y` を優先的に利用）
- トラジェクトリの散布図を速度[km/h]で色分け
- トラジェクトリの編集機能（点の移動・追加・削除、速度変更、Undo/Redo）
- 保存時にGUIのファイル保存ダイアログから出力先とファイル名を指定可能  
  （ダイアログが利用できない場合は既定の `SAVE_CSV` に保存）

### 依存関係
- Python 3.9+
- `matplotlib`, `pandas`, `numpy`, `tkinter`（GUI保存ダイアログに使用）

### 入出力
- 入力（既定値）
  - レーン境界: `tools/extracted_bounds/{left.csv,right.csv,centerline.csv}`
  - トラジェクトリ: `workspace/src/aichallenge_submit/simple_trajectory_generator/data/raceline_awsim_30km.csv`
- 出力（既定値）
  - 編集後トラジェクトリ: `workspace/src/aichallenge_submit/simple_trajectory_generator/data/edited_trajectory.csv`  
    ※ 表示時は速度[km/h]、保存時は m/s 単位で保存

### 実行方法
Docker内での実行例:
```bash
cd /aichallenge
python3 tools/edit_trajectory.py
```

### 操作方法（ウィンドウ上で）
- 左クリック＋ドラッグ: 最寄り点を選択し、位置を移動
- 右クリック: クリック位置に点を追加（速度は近傍点の平均で設定）
- Delete / Backspace: 最寄り点を削除
- マウスホイール上/下: 選択点の速度を ±1.0 km/h 変更
- `[` / `]`: 選択点の速度を −/+ 1.0 km/h
- `{` / `}`: 選択点の速度を −/+ 5.0 km/h
- `Z` / `Ctrl+Z`: Undo
- `Y` / `Ctrl+Y`: Redo
- `S`: CSV保存（ファイルダイアログが開き、保存先とファイル名を指定可能）
- `Q` / `Esc`: 終了

### 備考
- レーン境界CSVに `local_x,local_y` が存在しない場合は、`x,y`、それもなければ `latitude,longitude` から近似変換してXY座標を生成します。
- 速度表示は km/h ですが、保存時は互換性のため m/s で出力します。
