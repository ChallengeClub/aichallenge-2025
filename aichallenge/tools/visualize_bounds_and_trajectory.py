#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
境界CSV（left/right/centerline）と raceline_awsim_30km.csv を重ねて2D可視化するスクリプト。
- 出力: PNG（保存）と画面表示
- 依存: matplotlib, pandas（pip install matplotlib pandas）
"""

import os
import math
import pandas as pd
import matplotlib.pyplot as plt

# ====== 設定（ベタ書き） ======
BOUND_DIR = "./tools/extracted_bounds"  # left.csv / right.csv / centerline.csv
TRAJ_CSV  = "workspace/src/aichallenge_submit/simple_trajectory_generator/data/raceline_awsim_30km.csv"
SAVE_PNG  = "./tools/extracted_bounds/preview_bounds_and_trajectory.png"

# 軽量化：重い場合は間引き
BOUND_STRIDE = 1
TRAJ_STRIDE  = 1

# 描画
FIG_SIZE = (10, 10)
ALPHA_BOUNDS = 0.9
ALPHA_TRAJ   = 0.9
DOT_SIZE_BOUNDS = 5
DOT_SIZE_TRAJ   = 8


def equirectangular_xy(lat, lon, lat0, lon0):
    """緯度経度(度) -> 原点(lat0,lon0)基準の等距離図法近似XY[m]"""
    R = 6371000.0
    phi1 = math.radians(lat0)
    phi2 = math.radians(lat)
    dphi = math.radians(lat - lat0)
    dlmb = math.radians(lon - lon0)
    x = R * math.cos((phi1 + phi2) * 0.5) * dlmb
    y = R * dphi
    return x, y


def load_bound_xy(csv_path: str, prefer_local: bool = False) -> pd.DataFrame:
    """
    境界CSVを読み、(x,y)のDataFrame（2列のみ）を返す（常に列名は x,y に統一）。
    優先順:
      1) prefer_local=True かつ local_x, local_y が存在 → それを x,y に改名して返す
      2) x,y が存在 → そのまま返す
      3) latitude, longitude が存在 → 等距離図法近似で x,y を生成
    """
    df = pd.read_csv(csv_path)

    if prefer_local and {'local_x', 'local_y'}.issubset(df.columns):
        return df[['local_x', 'local_y']].rename(columns={'local_x': 'x', 'local_y': 'y'})

    if {'x', 'y'}.issubset(df.columns):
        return df[['x', 'y']].copy()

    if {'latitude', 'longitude'}.issubset(df.columns) and len(df) > 0:
        lat0 = float(df['latitude'].iloc[0])
        lon0 = float(df['longitude'].iloc[0])
        xs, ys = [], []
        for lat, lon in zip(df['latitude'], df['longitude']):
            x, y = equirectangular_xy(lat, lon, lat0, lon0)
            xs.append(x); ys.append(y)
        return pd.DataFrame({'x': xs, 'y': ys})

    raise ValueError(f"Unsupported boundary CSV schema: {csv_path}\nColumns: {list(df.columns)}")


def synthesize_centerline_from_left_right(left_xy: pd.DataFrame | None, right_xy: pd.DataFrame | None) -> pd.DataFrame | None:
    """
    left/right の x,y（できれば local 由来）から中点の centerline を合成。
    長さが違う場合は短い方に合わせる（単純なインデックス対応）。
    """
    if left_xy is None or right_xy is None:
        return None
    n = min(len(left_xy), len(right_xy))
    if n == 0:
        return None
    L = left_xy.iloc[:n].reset_index(drop=True)
    R = right_xy.iloc[:n].reset_index(drop=True)
    C = pd.DataFrame({'x': (L['x'] + R['x']) * 0.5, 'y': (L['y'] + R['y']) * 0.5})
    return C


def load_trajectory_xy(csv_path: str | None):
    if csv_path is None:
        return None
    df = pd.read_csv(csv_path)
    if not {'x', 'y'}.issubset(df.columns):
        raise ValueError(f"Trajectory CSV must contain x,y columns: {csv_path}\nColumns: {list(df.columns)}")
    return df[['x', 'y']].copy()


def maybe_load(path):
    return path if os.path.isfile(path) else None


def main():
    # ファイルパス
    left_csv  = maybe_load(os.path.join(BOUND_DIR, "left.csv"))
    right_csv = maybe_load(os.path.join(BOUND_DIR, "right.csv"))
    center_csv= maybe_load(os.path.join(BOUND_DIR, "centerline.csv"))
    traj_csv  = maybe_load(TRAJ_CSV)

    if not any([left_csv, right_csv, center_csv]):
        raise FileNotFoundError(f"No boundary CSVs found in {BOUND_DIR}")

    # 読み込み（left/right/centerline すべて local_x,local_y を優先）
    left_xy   = load_bound_xy(left_csv,   prefer_local=True) if left_csv   else None
    right_xy  = load_bound_xy(right_csv,  prefer_local=True) if right_csv  else None
    cent_xy   = load_bound_xy(center_csv, prefer_local=True) if center_csv else None

    # centerline に local が無ければ、left/right の local から合成
    if (cent_xy is None or len(cent_xy) == 0) and (left_xy is not None and right_xy is not None):
        cent_xy = synthesize_centerline_from_left_right(left_xy, right_xy)

    traj_xy = load_trajectory_xy(traj_csv) if traj_csv else None

    # 間引き
    if left_xy is not None and BOUND_STRIDE > 1:   left_xy  = left_xy.iloc[::BOUND_STRIDE, :]
    if right_xy is not None and BOUND_STRIDE > 1:  right_xy = right_xy.iloc[::BOUND_STRIDE, :]
    if cent_xy is not None and BOUND_STRIDE > 1:   cent_xy  = cent_xy.iloc[::BOUND_STRIDE, :]
    if traj_xy is not None and TRAJ_STRIDE > 1:    traj_xy  = traj_xy.iloc[::TRAJ_STRIDE, :]

    # 描画（点のみ）
    plt.figure(figsize=FIG_SIZE)

    if left_xy is not None and len(left_xy) > 0:
        plt.scatter(left_xy['x'].values, left_xy['y'].values,
                    s=DOT_SIZE_BOUNDS, label="left bound", alpha=ALPHA_BOUNDS)
    if right_xy is not None and len(right_xy) > 0:
        plt.scatter(right_xy['x'].values, right_xy['y'].values,
                    s=DOT_SIZE_BOUNDS, label="right bound", alpha=ALPHA_BOUNDS)
    if cent_xy is not None and len(cent_xy) > 0:
        plt.scatter(cent_xy['x'].values, cent_xy['y'].values,
                    s=DOT_SIZE_BOUNDS, label="centerline", alpha=ALPHA_BOUNDS)

    # トラジェクトリ（必要なら点表示）
    if traj_xy is not None and len(traj_xy) > 0:
        plt.scatter(traj_xy['x'].values, traj_xy['y'].values,
                    s=DOT_SIZE_TRAJ, label="trajectory", alpha=ALPHA_TRAJ)

    plt.gca().set_aspect('equal', adjustable='box')
    plt.grid(True, linestyle=":", linewidth=0.6)
    plt.xlabel("X [m]")
    plt.ylabel("Y [m]")
    plt.title("Lane Bounds & Trajectory (points)")
    plt.legend(loc="best")

    # 保存
    outdir = os.path.dirname(SAVE_PNG)
    if outdir:
        os.makedirs(outdir, exist_ok=True)
    plt.savefig(SAVE_PNG, dpi=200, bbox_inches="tight")
    print(f"[save] {SAVE_PNG}")

    plt.show()


if __name__ == "__main__":
    main()
