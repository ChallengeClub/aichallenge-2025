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

## aichallenge-trajectory-editor

経路編集ツールをモディファイしております

### 主な機能

- コースファイル(osm) から レーンファイル(csv) を作成 (csv_from_osm)
- トラジェクトリファイル(csv)のGUI編集 (csv_editor)
  - 速度ラベルの編集
  - 曲線のスムーズ機能（あまりつかってない）
  - 速度の振り直し（速度から自動調整）（最低、最高速度、加速度などの設定）

###

- [詳細はこちらの README.md へ](aichallenge-trajectory-editor/README.md)
