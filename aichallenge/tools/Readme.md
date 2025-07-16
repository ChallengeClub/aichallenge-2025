# tools
このディレクトリには、開発補助・前処理用のスクリプトが含まれています。

---
# tools ディレクトリ

このディレクトリには、Pure Pursuit制御のパラメータ調整および評価用のスクリプトが含まれています。

---
## `optuna_tune_pure_pursuit.py`, `evaluate_wrapper.py`
### `optuna_tune_pure_pursuit.py`

Optunaを用いて、Pure Pursuit制御の以下のパラメータを自動最適化します。適宜変更してください。
- `lookahead_gain`
- `lookahead_min`
- `speed_gain`

各試行で `evaluate_wrapper.py` を呼び出してスコア（走行タイム）を取得し、最適化を行います。
60秒だけ実行して、最初のファイルのラップタイムだけで評価しています。

### `evaluate_wrapper.py`

指定されたパラメータを環境変数として `reference.launch.xml.template` に埋め込み、  
生成された `reference.launch.xml` を使って走行評価（60秒）を実行し、  
最小走行時間 (`min_time`) を `result-summary.json` から抽出します。

---

###  実行方法

Docker内で以下のコマンドを実行することでOptunaによる最適化を開始できます：

```bash
cd aichallenge
python3 tools/optuna_tune_pure_pursuit.py
```

### 出力ファイル
各試行の結果は optuna_logs/ ディレクトリにCSV形式で保存されます。

ファイル例：optuna_logs/tuning_result_YYYYMMDD-HHMMSS.csv

### 前提ファイル構成
```
.
├── tools/
│   ├── optuna_tune_pure_pursuit.py
│   ├── evaluate_wrapper.py
│   └── optuna_logs/
├── workspace/
│   └── src/
│       └── aichallenge_submit/
│           └── aichallenge_submit_launch/
│               └── launch/
│                   ├── reference.launch.xml.template
│                   └── reference.launch.xml  ← 自動生成される
├── run_evaluation_60sec.bash
└── output/
    └── ...（評価結果ディレクトリ）
```

### 補足
`optuna_tune_pure_pursuit.py` 内で `tools/evaluate_wrapper.py` を相対パスで呼び出すため、プロジェクトルートから実行してください。
環境変数を使ったテンプレート埋め込みには envsubst を使用しています。
評価実行には `run_evaluation_60sec.bash` が必要です。
