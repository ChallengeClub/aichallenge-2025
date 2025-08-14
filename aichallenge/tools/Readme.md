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