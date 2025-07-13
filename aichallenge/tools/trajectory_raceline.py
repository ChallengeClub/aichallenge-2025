import pandas as pd
import numpy as np

# 入出力ファイル
input_csv = "workspace/src/aichallenge_submit/simple_trajectory_generator/data/raceline_awsim_15km.csv"
output_csv = "workspace/src/aichallenge_submit/simple_trajectory_generator/data/raceline_awsim_35km_adjusted.csv"

# 読み込み
columns = ["x", "y", "z", "x_quat", "y_quat", "z_quat", "w_quat", "speed"]
df = pd.read_csv(input_csv, comment="#", names=columns, skiprows=1)

# 曲率計算
x = df["x"].values
y = df["y"].values
dx = np.gradient(x)
dy = np.gradient(y)
ddx = np.gradient(dx)
ddy = np.gradient(dy)
curvature = (dx * ddy - dy * ddx) / np.power(dx**2 + dy**2, 1.5)

# 基本速度マップ（曲率に応じて）
def base_speed(c):
    abs_c = abs(c)
    if abs_c < 0.02:
        return 10.50  # 35 km/h * 1,1
    elif abs_c < 0.05:
        return 10.45
    elif abs_c < 0.1:
        return 10.20
    else:
        return 9.9  # 最も減速しても 9.0 m/s

# 未来（＋5）・過去（−5）の曲率を見る
adjusted_speed = []
lookahead = 5  # 速度補正の先読み距離

for i in range(len(curvature)):
    base = base_speed(curvature[i])
    
    # カーブ入口の判定：未来で曲率が大きく増える
    if i + lookahead < len(curvature) and (curvature[i + lookahead] - curvature[i]) > 0.001:
        adjusted_speed.append(base * 0.95)  # 5% 減速
    # カーブ出口の判定：過去と比べて曲率が減少
    elif i - lookahead >= 0 and (curvature[i - lookahead] - curvature[i]) > 0.001:
        adjusted_speed.append(min(base * 1.10, 10.50))  # 5% 加速（上限あり）
    else:
        adjusted_speed.append(base)

df["speed"] = adjusted_speed

# 保存
df.to_csv(output_csv, index=False, header=True)
print(f"✅ Saved adjusted CSV with entry/exit curve handling to: {output_csv}")
