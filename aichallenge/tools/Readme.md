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