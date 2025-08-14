#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
edit_trajectory.py
- レーン境界(left/right/centerline)を黒い細点で表示（local_x,local_y を優先）
- raceline_awsim_30km.csv のトラジェクトリを色付き散布図で表示
  - カラーマップ: jet
  - 色は速度[km/h]で表現（表示のみ。保存は m/s で互換維持）
- マウス/キーボードでトラジェクトリ点を編集（移動/追加/削除/速度編集/Undo/Redo/保存）

依存: matplotlib, pandas, numpy
pip install matplotlib pandas numpy
"""

import os
import math
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
try:
    import tkinter as tk
    from tkinter import filedialog
    _HAS_TK = True
except Exception:
    _HAS_TK = False


# ========= 設定（必要に応じて変更） =========
BOUND_DIR   = "./tools/extracted_bounds"  # left.csv / right.csv / centerline.csv
TRAJ_CSV    = "workspace/src/aichallenge_submit/simple_trajectory_generator/data/raceline_awsim_35km_adjusted.csv"
SAVE_CSV    = "./tools/extracted_bounds/edited_trajectory.csv"

# 表示調整
FIG_SIZE        = (10, 10)
LANE_DOT_SIZE   = 2.0      # レーン点の大きさ（黒・細）
LANE_DOT_ALPHA  = 0.8
TRAJ_DOT_SIZE   = 14       # トラジェクトリ点の大きさ
TRAJ_ALPHA      = 0.95
PICK_RADIUS_PX  = 8        # ピックしやすさ（ピクセル）
SPEED_MIN_KPH   = 0.0      # 表示/編集下限
SPEED_MAX_KPH   = 200.0    # 表示/編集上限（必要なら変更）
SPEED_STEP_KPH  = 1.0      # 速度編集の基本刻み（キー/ホイール）
SPEED_BIGSTEP_KPH = 5.0    # 速度編集の大刻み
# ==========================================


def equirectangular_xy(lat, lon, lat0, lon0):
    """緯度経度 -> 原点基準ローカルXY（等距離図法近似, m）"""
    R = 6371000.0
    phi1 = math.radians(lat0)
    phi2 = math.radians(lat)
    dphi = math.radians(lat - lat0)
    dlmb = math.radians(lon - lon0)
    x = R * math.cos((phi1 + phi2) * 0.5) * dlmb
    y = R * dphi
    return x, y


def load_bound_xy(csv_path: str, prefer_local: bool = True) -> pd.DataFrame | None:
    """
    境界CSV -> DataFrame[['x','y']]
    優先: local_x,local_y -> x,y
    次点: x,y
    次点: latitude,longitude -> 近似XY
    """
    if not os.path.isfile(csv_path):
        return None
    df = pd.read_csv(csv_path)
    cols = set(df.columns)
    if prefer_local and {'local_x', 'local_y'}.issubset(cols):
        return df[['local_x', 'local_y']].rename(columns={'local_x': 'x', 'local_y': 'y'})
    if {'x', 'y'}.issubset(cols):
        return df[['x', 'y']].copy()
    if {'latitude', 'longitude'}.issubset(cols) and len(df) > 0:
        lat0, lon0 = float(df['latitude'].iloc[0]), float(df['longitude'].iloc[0])
        xs, ys = [], []
        for lat, lon in zip(df['latitude'], df['longitude']):
            x, y = equirectangular_xy(lat, lon, lat0, lon0)
            xs.append(x); ys.append(y)
        return pd.DataFrame({'x': xs, 'y': ys})
    return None


def load_bounds_all(bound_dir: str):
    left  = load_bound_xy(os.path.join(bound_dir, "left.csv"),  prefer_local=True)
    right = load_bound_xy(os.path.join(bound_dir, "right.csv"), prefer_local=True)
    cent  = load_bound_xy(os.path.join(bound_dir, "centerline.csv"), prefer_local=True)
    return left, right, cent


def load_trajectory(csv_path: str) -> pd.DataFrame:
    """
    トラジェクトリCSVを読み込み、少なくとも x,y を持つDataFrameを返す。
    speed が無ければ 0 で埋める。その他の列は保持。
    速度は m/s を前提（表示は km/h に変換）。
    """
    if not os.path.isfile(csv_path):
        raise FileNotFoundError(csv_path)
    df = pd.read_csv(csv_path)
    if not {'x', 'y'}.issubset(df.columns):
        raise ValueError(f"x,y が見つかりません: {csv_path} -> {list(df.columns)}")
    if 'speed' not in df.columns:
        df['speed'] = 0.0
    return df


class TrajectoryEditor:
    """
    Matplotlib上でトラジェクトリ点のドラッグ移動/追加/削除/速度編集/Undo/Redo/保存を行う簡易エディタ。
    - 左クリック: 近い点を選択してドラッグで移動
    - 右クリック: その位置に点を追加（速度は近傍点から補間）
    - Delete/Backspace: 最寄り点を削除
    - Z / Ctrl+Z: Undo
    - Y / Ctrl+Y: Redo
    - S: 保存（SAVE_CSVへ）
    - Q / Esc: 終了
    - 速度編集:
        ・マウスホイール上/下: 選択点の速度を +/− (SPEED_STEP_KPH) [km/h]
        ・[/]: −/＋ (SPEED_STEP_KPH) [km/h]
        ・{/}: −/＋ (SPEED_BIGSTEP_KPH) [km/h]
        ・カーソルが近い点が自動選択されます（ドラッグで位置も編集可能）
    """
    def __init__(self, traj_df: pd.DataFrame, left: pd.DataFrame | None,
                 right: pd.DataFrame | None, center: pd.DataFrame | None):
        self.left = left
        self.right = right
        self.center = center

        # 編集対象（速度は m/s を保持、表示は kph）
        self.df = traj_df.copy()
        self.xy = self.df[['x', 'y']].to_numpy(dtype=float)
        self.sp_mps = self.df['speed'].to_numpy(dtype=float)

        # 履歴（簡易）
        self.undo_stack: list[tuple[np.ndarray, np.ndarray]] = []
        self.redo_stack: list[tuple[np.ndarray, np.ndarray]] = []

        # Matplotlib 準備
        self.fig, self.ax = plt.subplots(figsize=FIG_SIZE)
        self._plot_static_bounds()

        self.scat = self.ax.scatter(
            self.xy[:, 0], self.xy[:, 1],
            c=self._sp_kph(), s=TRAJ_DOT_SIZE, alpha=TRAJ_ALPHA,
            cmap='jet', picker=True
        )
        self.cbar = self.fig.colorbar(self.scat, ax=self.ax, label='speed [km/h]')
        self.ax.set_aspect('equal', adjustable='box')
        self.ax.grid(True, linestyle=":", linewidth=0.6)
        self.ax.set_xlabel("X [m]"); self.ax.set_ylabel("Y [m]")
        self.ax.set_title("Edit Trajectory (drag/add/delete, speed edit: wheel/[/]/[{/}], S=save, Z=undo, Y=redo, Q=quit)")

        # 状態
        self.pressed = False
        self.dragging_idx: int | None = None
        self.selected_idx: int | None = None  # 速度編集対象点
        self._status_text = self.ax.text(0.02, 0.98, "", transform=self.ax.transAxes,
                                         va='top', ha='left')

        # コールバック
        self.cid_pick    = self.fig.canvas.mpl_connect('pick_event', self.on_pick)
        self.cid_press   = self.fig.canvas.mpl_connect('button_press_event', self.on_press)
        self.cid_release = self.fig.canvas.mpl_connect('button_release_event', self.on_release)
        self.cid_motion  = self.fig.canvas.mpl_connect('motion_notify_event', self.on_motion)
        self.cid_key     = self.fig.canvas.mpl_connect('key_press_event', self.on_key)
        self.cid_scroll  = self.fig.canvas.mpl_connect('scroll_event', self.on_scroll)

        # ピック範囲
        self.scat.set_picker(PICK_RADIUS_PX)

    # ---------- 便利関数 ----------
    def _sp_kph(self) -> np.ndarray:
        return self.sp_mps * 3.6

    def _clamp_speed_kph(self, v_kph: float) -> float:
        return float(np.clip(v_kph, SPEED_MIN_KPH, SPEED_MAX_KPH))

    def _set_status(self, msg: str):
        self._status_text.set_text(msg)
        self.fig.canvas.draw_idle()

    def _ask_save_path(self) -> str | None:
        """
        Tk のファイル保存ダイアログを開いて保存先パスを返す。
        キャンセル時や Tk 未導入/使用不可の場合は None を返す。
        """
        # 既定のディレクトリ/ファイル名
        init_dir = os.path.dirname(SAVE_CSV) or "."
        init_file = os.path.basename(SAVE_CSV) or "edited_trajectory.csv"

        if not _HAS_TK:
            # Tk が使えない環境では None を返し、呼び出し側でフォールバックさせる
            print("[warn] tkinter が利用できません。SAVE_CSV へ保存します。")
            return SAVE_CSV

        try:
            root = tk.Tk()
            root.withdraw()
            path = filedialog.asksaveasfilename(
                initialdir=init_dir,
                initialfile=init_file,
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
                title="Save edited trajectory as..."
            )
            root.destroy()
            return path if path else None
        except Exception as e:
            print(f"[warn] save dialog error: {e} -> SAVE_CSV に保存します。")
            return SAVE_CSV

    # ---------- 描画 ----------
    def _plot_static_bounds(self):
        # レーン境界/センターは黒い細点
        if self.left is not None and len(self.left) > 0:
            self.ax.scatter(self.left['x'], self.left['y'], s=LANE_DOT_SIZE, c='k', alpha=LANE_DOT_ALPHA, label='left')
        if self.right is not None and len(self.right) > 0:
            self.ax.scatter(self.right['x'], self.right['y'], s=LANE_DOT_SIZE, c='k', alpha=LANE_DOT_ALPHA, label='right')
        if self.center is not None and len(self.center) > 0:
            self.ax.scatter(self.center['x'], self.center['y'], s=LANE_DOT_SIZE, c='k', alpha=LANE_DOT_ALPHA, label='centerline')
        self.ax.legend(loc='best')

    def _refresh_scatter(self):
        self.scat.set_offsets(self.xy)
        self.scat.set_array(self._sp_kph())
        self.fig.canvas.draw_idle()

    # ---------- 履歴 ----------
    def _push_undo(self):
        self.undo_stack.append((self.xy.copy(), self.sp_mps.copy()))
        self.redo_stack.clear()

    def _undo(self):
        if not self.undo_stack:
            return
        self.redo_stack.append((self.xy.copy(), self.sp_mps.copy()))
        self.xy, self.sp_mps = self.undo_stack.pop()
        self._refresh_scatter()

    def _redo(self):
        if not self.redo_stack:
            return
        self.undo_stack.append((self.xy.copy(), self.sp_mps.copy()))
        self.xy, self.sp_mps = self.redo_stack.pop()
        self._refresh_scatter()

    # ---------- 近傍探索 ----------
    def _nearest_index(self, x, y, max_dist_px=PICK_RADIUS_PX):
        if self.xy.size == 0:
            return None
        trans = self.ax.transData.transform
        pts_disp = trans(self.xy)
        click_disp = trans(np.array([[x, y]]))[0]
        d2 = np.sum((pts_disp - click_disp) ** 2, axis=1)
        idx = int(np.argmin(d2))
        if np.sqrt(d2[idx]) <= max_dist_px:
            return idx
        return None

    def _select_nearest(self, x, y):
        idx = self._nearest_index(x, y)
        self.selected_idx = idx
        if idx is not None:
            self._set_status(f"Selected idx={idx}, speed={self._sp_kph()[idx]:.1f} km/h")
        else:
            self._set_status("")

    # ---------- イベント ----------
    def on_pick(self, event):
        pass

    def on_press(self, event):
        if event.inaxes != self.ax or event.xdata is None or event.ydata is None:
            return
        if event.button == 1:  # 左クリック: 近傍選択 + ドラッグ開始
            idx = self._nearest_index(event.xdata, event.ydata)
            self.selected_idx = idx
            if idx is not None:
                self._push_undo()
                self.pressed = True
                self.dragging_idx = idx
                self._set_status(f"Drag idx={idx}, speed={self._sp_kph()[idx]:.1f} km/h")
            else:
                self._set_status("")
        elif event.button == 3:  # 右クリック: 点追加
            self._push_undo()
            self._add_point(event.xdata, event.ydata)

    def on_motion(self, event):
        if not self.pressed or self.dragging_idx is None:
            return
        if event.inaxes != self.ax or event.xdata is None or event.ydata is None:
            return
        self.xy[self.dragging_idx, 0] = event.xdata
        self.xy[self.dragging_idx, 1] = event.ydata
        self._refresh_scatter()

    def on_release(self, event):
        self.pressed = False
        self.dragging_idx = None

    def on_key(self, event):
        key_str = (event.key or "").lower()
        ctrl = key_str.startswith("ctrl+")
        k = key_str.replace("ctrl+", "") if ctrl else key_str

        if k in ('delete', 'backspace'):
            self._delete_selected_nearest(event)
        elif k == 's':
            # ダイアログで保存先/ファイル名を選択（キャンセル時は何もしない）
            save_path = self._ask_save_path()
            if save_path:
                self._save(save_path)
        elif k in ('q', 'escape'):
            plt.close(self.fig)
        elif k == 'z' and ctrl:
            self._undo()
        elif k == 'y' and ctrl:
            self._redo()
        elif k in ('[', ']', '{', '}'):
            if self.selected_idx is None and event.xdata is not None and event.ydata is not None:
                self._select_nearest(event.xdata, event.ydata)
            if self.selected_idx is not None:
                self._push_undo()
                if k == '[':
                    self._bump_speed(self.selected_idx, -SPEED_STEP_KPH)
                elif k == ']':
                    self._bump_speed(self.selected_idx, +SPEED_STEP_KPH)
                elif k == '{':
                    self._bump_speed(self.selected_idx, -SPEED_BIGSTEP_KPH)
                elif k == '}':
                    self._bump_speed(self.selected_idx, +SPEED_BIGSTEP_KPH)

    def on_scroll(self, event):
        # ホイールで速度微調整（選択点が必要）
        if event.inaxes != self.ax:
            return
        if self.selected_idx is None:
            self._select_nearest(event.xdata, event.ydata)
        if self.selected_idx is None:
            return
        self._push_undo()
        delta = SPEED_STEP_KPH * (1 if event.button == 'up' else -1)
        self._bump_speed(self.selected_idx, delta)

    # ---------- 操作 ----------
    def _delete_selected_nearest(self, event):
        if event.inaxes != self.ax or event.xdata is None or event.ydata is None:
            return
        idx = self._nearest_index(event.xdata, event.ydata)
        if idx is None or len(self.xy) <= 1:
            return
        self._push_undo()
        self.xy = np.delete(self.xy, idx, axis=0)
        self.sp_mps = np.delete(self.sp_mps, idx, axis=0)
        self.selected_idx = None
        self._refresh_scatter()
        self._set_status("Deleted point")

    def _add_point(self, x, y):
        # 近傍2点の平均速度(m/s)を新規速度に
        if len(self.xy) >= 2:
            d = np.linalg.norm(self.xy - np.array([x, y]), axis=1)
            nn = np.argsort(d)[:2]
            sp_new = float(np.mean(self.sp_mps[nn]))
        elif len(self.xy) == 1:
            sp_new = float(self.sp_mps[0])
        else:
            sp_new = 0.0
        self.xy = np.vstack([self.xy, [x, y]])
        self.sp_mps = np.hstack([self.sp_mps, [sp_new]])
        self.selected_idx = len(self.xy) - 1
        self._refresh_scatter()
        self._set_status(f"Added point idx={self.selected_idx}, speed={self._sp_kph()[self.selected_idx]:.1f} km/h")

    def _bump_speed(self, idx: int, delta_kph: float):
        cur_kph = self._sp_kph()[idx]
        new_kph = self._clamp_speed_kph(cur_kph + delta_kph)
        self.sp_mps[idx] = new_kph / 3.6
        self._refresh_scatter()
        self._set_status(f"Speed idx={idx}: {new_kph:.1f} km/h")

    def _save(self, path: str):
        # 編集した x,y, speed(m/s) を DataFrame に反映し保存
        n = len(self.xy)
        base = self.df.copy()
        if len(base) != n:
            # 行数差分を調整
            if n < len(base):
                base = base.iloc[:n].reset_index(drop=True)
            else:
                extra = n - len(base)
                add_df = pd.DataFrame(index=range(extra), columns=base.columns)
                base = pd.concat([base, add_df], ignore_index=True)

        base.loc[:, 'x'] = pd.to_numeric(base.get('x', np.nan), errors='coerce')
        base.loc[:, 'y'] = pd.to_numeric(base.get('y', np.nan), errors='coerce')
        base.loc[:, 'speed'] = pd.to_numeric(base.get('speed', np.nan), errors='coerce')

        base['x'] = self.xy[:, 0]
        base['y'] = self.xy[:, 1]
        base['speed'] = self.sp_mps  # m/s で保存（互換性維持）

        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        base.to_csv(path, index=False)
        print(f"[save] {path} ({len(base)} rows)")

def main():
    # レーン境界
    left, right, center = load_bounds_all(BOUND_DIR)
    if left is None and right is None and center is None:
        raise FileNotFoundError(f"No boundary CSVs in {BOUND_DIR}")

    # トラジェクトリ
    traj_df = load_trajectory(TRAJ_CSV)

    # エディタ起動
    editor = TrajectoryEditor(traj_df, left, right, center)
    plt.show()  # GUI ループ

if __name__ == "__main__":
    main()