import os
import sys
import subprocess
import glob
import json
import time

print("--- evaluate_wrapper.py ---")

lookahead_gain = sys.argv[1]
lookahead_min = sys.argv[2]
speed_gain = sys.argv[3]

# 環境変数を設定（envsubst用）
os.environ["PURE_PURSUIT_LOOKAHEAD_GAIN"] = lookahead_gain
os.environ["PURE_PURSUIT_LOOKAHEAD_MIN"] = lookahead_min
os.environ["PURE_PURSUIT_SPEED_GAIN"] = speed_gain

# launchテンプレート置換（in-place）
print("launchテンプレート置換（in-place）")
ret = subprocess.run([
    "bash", "-c",
    "envsubst < workspace/src/aichallenge_submit/aichallenge_submit_launch/launch/reference.launch.xml.template > workspace/src/aichallenge_submit/aichallenge_submit_launch/launch/reference.launch.xml"
], capture_output=True, text=True)

# デバッグ出力
print("envsubst stdout:", ret.stdout)
print("envsubst stderr:", ret.stderr)

# ファイルが存在するか確認
launch_file_path = "workspace/src/aichallenge_submit/aichallenge_submit_launch/launch/reference.launch.xml"
if not os.path.exists(launch_file_path):
    print("🚨 ERROR: reference.launch.xml が生成されていません")
    print("⛏️ 環境変数または template ファイルの構文エラーを確認してください")
    sys.exit(1)

# 評価スクリプトを実行（上書きされたlaunchを使用）
subprocess.run(["bash", "./run_evaluation_60sec.bash"])

# 結果ファイルを探してスコアを抽出
time.sleep(3)
paths = sorted(glob.glob("output/*/result-summary.json"))
if not paths:
    print("9999")
    sys.exit()

with open(paths[-1]) as f:
    data = json.load(f)

score = data.get("min_time", 9999)
print(score)
