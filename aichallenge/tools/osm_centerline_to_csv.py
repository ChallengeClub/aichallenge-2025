#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
lanelet2_map.osm の centerline を CSV に変換するスクリプト
- centerline は <relation type="lanelet"> の <member type="way" role="centerline"> を走査して取得
- ノード座標は node の <tag k="local_x"/"local_y">（なければ "x"/"y"）から取得
- クォータニオンは 2D（Yaw のみ）: (xq, yq, zq, wq) = (0, 0, sin(yaw/2), cos(yaw/2))
- 速度は固定値（km/h 指定 → m/s に変換して全点に設定）

出力 CSV 列: x, y, z, x_quat, y_quat, z_quat, w_quat, speed
"""

import xml.etree.ElementTree as ET
import math
import csv
from pathlib import Path
from typing import Dict, List, Tuple

# -------- ユーティリティ --------

def _node_tags(node: ET.Element) -> Dict[str, str]:
    return {t.get("k"): t.get("v") for t in node.findall("tag")}

def _rel_tags(rel: ET.Element) -> Dict[str, str]:
    return {t.get("k"): t.get("v") for t in rel.findall("tag")}

def _yaw_from(p0: Tuple[float, float], p1: Tuple[float, float]) -> float:
    dx = p1[0] - p0[0]
    dy = p1[1] - p0[1]
    return math.atan2(dy, dx)

def _quat_from_yaw(yaw: float) -> Tuple[float, float, float, float]:
    half = 0.5 * yaw
    return (0.0, 0.0, math.sin(half), math.cos(half))  # (x, y, z, w)

# -------- OSM 読み込み --------

def load_map(osm_path: Path):
    tree = ET.parse(osm_path)
    root = tree.getroot()

    # node -> (x, y)
    node_xy: Dict[int, Tuple[float, float]] = {}
    for n in root.findall("node"):
        nid = int(n.get("id"))
        tags = _node_tags(n)
        if "local_x" in tags and "local_y" in tags:
            try:
                node_xy[nid] = (float(tags["local_x"]), float(tags["local_y"]))
            except ValueError:
                pass
        elif "x" in tags and "y" in tags:
            try:
                node_xy[nid] = (float(tags["x"]), float(tags["y"]))
            except ValueError:
                pass

    # way id -> [node ids]
    way_nodes: Dict[int, List[int]] = {}
    for w in root.findall("way"):
        wid = int(w.get("id"))
        way_nodes[wid] = [int(nd.get("ref")) for nd in w.findall("nd") if nd.get("ref")]

    # relation から centerline の way id を収集
    centerline_way_ids: List[int] = []
    for r in root.findall("relation"):
        tags = _rel_tags(r)
        if tags.get("type") == "lanelet":
            for m in r.findall("member"):
                if m.get("type") == "way" and m.get("role") == "centerline" and m.get("ref"):
                    centerline_way_ids.append(int(m.get("ref")))

    if not centerline_way_ids:
        raise RuntimeError("relation(lanelet) 内に role=centerline の way が見つかりませんでした。")

    return node_xy, way_nodes, centerline_way_ids

# -------- Centerline の連結（簡易） --------

def chain_centerlines(way_nodes: Dict[int, List[int]], centerline_way_ids: List[int]) -> List[int]:
    """
    centerline の Way 群を端点一致で貪欲に連結する。
    向きが合わなければ反転。余ったものは最後にベタ結合（簡易）。
    """
    sequences: List[List[int]] = []
    for wid in centerline_way_ids:
        seq = way_nodes.get(wid)
        if seq and len(seq) >= 2:
            sequences.append(seq[:])

    if not sequences:
        raise RuntimeError("centerline のノード列が見つかりませんでした。")

    chained: List[int] = sequences[0][:]
    used = [False] * len(sequences)
    used[0] = True

    progress = True
    while progress:
        progress = False
        # 末尾側に延長
        last = chained[-1]
        for i, seq in enumerate(sequences):
            if used[i]:
                continue
            if seq[0] == last:
                chained.extend(seq[1:])
                used[i] = True
                progress = True
                break
            if seq[-1] == last:
                chained.extend(list(reversed(seq[:-1])))
                used[i] = True
                progress = True
                break
        # 先頭側に延長
        if not progress:
            head = chained[0]
            for i, seq in enumerate(sequences):
                if used[i]:
                    continue
                if seq[-1] == head:
                    chained = seq[:-1] + chained
                    used[i] = True
                    progress = True
                    break
                if seq[0] == head:
                    chained = list(reversed(seq[1:])) + chained
                    used[i] = True
                    progress = True
                    break

    # まだ未使用があれば最後に結合（ベストエフォート）
    for i, seq in enumerate(sequences):
        if not used[i]:
            if chained[-1] == seq[0]:
                chained.extend(seq[1:])
            elif chained[-1] == seq[-1]:
                chained.extend(list(reversed(seq[:-1])))
            else:
                chained += seq

    # 連続重複削除
    dedup = [chained[0]]
    for nid in chained[1:]:
        if nid != dedup[-1]:
            dedup.append(nid)
    return dedup

# -------- CSV 出力 --------

def write_csv(
    node_xy: Dict[int, Tuple[float, float]],
    node_ids: List[int],
    out_path: Path,
    speed_kmh: float = 30.0,
    z_value: float = 0.0,
):
    # 実在する点のみにフィルタ
    pts: List[Tuple[int, Tuple[float, float]]] = [(nid, node_xy[nid]) for nid in node_ids if nid in node_xy]
    if len(pts) < 2:
        raise RuntimeError("有効な (x,y) 点が2点未満のため、CSVを出力できません。")

    speed_mps = speed_kmh / 3.6

    with out_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["x", "y", "z", "x_quat", "y_quat", "z_quat", "w_quat", "speed"])
        for i, (_nid, (x, y)) in enumerate(pts):
            if i == 0:
                yaw = _yaw_from((x, y), pts[i + 1][1])
            else:
                yaw = _yaw_from(pts[i - 1][1], (x, y))
            xq, yq, zq, wq = _quat_from_yaw(yaw)
            w.writerow([x, y, z_value, xq, yq, zq, wq, speed_mps])

# -------- エントリポイント（サンプル実行） --------

if __name__ == "__main__":
    # 例：手元のパスに合わせて変更してください
    OSM_PATH = Path("lanelet2_map.osm")
    OUT_CSV = Path("raceline_from_centerline.csv")

    # 固定速度[km/h]と z 値
    SPEED_KMH = 25.0
    Z_VALUE = 0.0

    node_xy, way_nodes, centerline_way_ids = load_map(OSM_PATH)
    node_ids = chain_centerlines(way_nodes, centerline_way_ids)
    write_csv(node_xy, node_ids, OUT_CSV, speed_kmh=SPEED_KMH, z_value=Z_VALUE)

    print(f"Generated: {OUT_CSV} (points: {len(node_ids)})")
