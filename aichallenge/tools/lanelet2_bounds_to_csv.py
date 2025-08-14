#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import argparse
import csv
import math
import os
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional, Iterable

try:
    from pyproj import CRS, Transformer  # 任意
    _HAS_PYPROJ = True
except Exception:
    _HAS_PYPROJ = False

LatLon = Tuple[float, float]

@dataclass
class WayData:
    node_ids: List[str]
    tags: Dict[str, str]

@dataclass
class RelationMember:
    type: str
    ref: str
    role: str

@dataclass
class RelationData:
    members: List[RelationMember]
    tags: Dict[str, str]

class OSMExtractor:
    def __init__(self, osm_file_path: str, origin_latlon: Optional[LatLon] = None):
        self.osm_file_path = osm_file_path
        tree = ET.parse(osm_file_path)
        self.root = tree.getroot()
        # nodes: node_id -> {"lat": float, "lon": float, "local_x": Optional[float], "local_y": Optional[float]}
        self.nodes: Dict[str, Dict[str, Optional[float]]] = {}
        self.ways: Dict[str, WayData] = {}
        self.relations: Dict[str, RelationData] = {}
        self.origin_latlon = origin_latlon
        self._transformer: Optional['Transformer'] = None

    # ---------- Parse ----------
    def parse_nodes(self) -> None:
        for node in self.root.findall('node'):
            nid = node.get('id'); lat = node.get('lat'); lon = node.get('lon')
            if not (nid and lat and lon):
                continue
            try:
                lat_f = float(lat)
                lon_f = float(lon)
            except ValueError:
                continue

            # 追加: nodeタグから local_x / local_y を拾う
            local_x = None
            local_y = None
            for tag in node.findall('tag'):
                k = tag.get('k'); v = tag.get('v')
                if k == 'local_x' and v is not None:
                    try:
                        local_x = float(v)
                    except ValueError:
                        pass
                elif k == 'local_y' and v is not None:
                    try:
                        local_y = float(v)
                    except ValueError:
                        pass

            self.nodes[nid] = {
                "lat": lat_f,
                "lon": lon_f,
                "local_x": local_x,
                "local_y": local_y,
            }

        # 原点未指定なら最初のノードのlat/lonを原点に
        if self.origin_latlon is None and self.nodes:
            any_node = next(iter(self.nodes.values()))
            self.origin_latlon = (any_node["lat"], any_node["lon"])  # type: ignore[arg-type]

    def parse_ways(self) -> None:
        for way in self.root.findall('way'):
            wid = way.get('id')
            if not wid:
                continue
            node_refs, tags = [], {}
            for nd in way.findall('nd'):
                r = nd.get('ref')
                if r:
                    node_refs.append(r)
            for tag in way.findall('tag'):
                k, v = tag.get('k'), tag.get('v')
                if k is not None and v is not None:
                    tags[k] = v
            self.ways[wid] = WayData(node_ids=node_refs, tags=tags)

    def parse_relations(self) -> None:
        for rel in self.root.findall('relation'):
            rid = rel.get('id')
            if not rid:
                continue
            members, tags = [], {}
            for m in rel.findall('member'):
                t, r, role = m.get('type'), m.get('ref'), m.get('role', '')
                if t and r:
                    members.append(RelationMember(type=t, ref=r, role=role))
            for tag in rel.findall('tag'):
                k, v = tag.get('k'), tag.get('v')
                if k is not None and v is not None:
                    tags[k] = v
            self.relations[rid] = RelationData(members=members, tags=tags)

    # ---------- Coord ----------
    def _maybe_init_projection(self) -> None:
        if not _HAS_PYPROJ or self._transformer is not None or not self.origin_latlon:
            return
        lat0, lon0 = self.origin_latlon
        try:
            zone = int((lon0 + 180) / 6) + 1
            utm = CRS.from_user_input(f"+proj=utm +zone={zone} +datum=WGS84 +units=m +no_defs")
            self._transformer = Transformer.from_crs(CRS.from_epsg(4326), utm, always_xy=True)
        except Exception:
            self._transformer = None

    def latlon_to_xy(self, lat: float, lon: float) -> Tuple[float, float]:
        if self.origin_latlon is None:
            if not self.nodes:
                raise RuntimeError("Call parse_nodes() before converting coordinates.")
            any_node = next(iter(self.nodes.values()))
            self.origin_latlon = (any_node["lat"], any_node["lon"])  # type: ignore[arg-type]
        lat0, lon0 = self.origin_latlon
        if _HAS_PYPROJ:
            self._maybe_init_projection()
            if self._transformer:
                x, y = self._transformer.transform(lon, lat)
                x0, y0 = self._transformer.transform(lon0, lat0)
                return x - x0, y - y0
        # equirectangular fallback
        R = 6371000.0
        phi1 = math.radians(lat0); phi2 = math.radians(lat)
        dphi = math.radians(lat - lat0); dlambda = math.radians(lon - lon0)
        x = R * math.cos((phi1 + phi2) * 0.5) * dlambda
        y = R * dphi
        return x, y

    # ---------- Helpers ----------
    def _coords_of_way(self, way_id: str) -> List[Tuple[float, float, Optional[float], Optional[float]]]:
        """
        Wayに含まれるノード列を (lat, lon, local_x, local_y) に展開。
        """
        way = self.ways.get(way_id)
        if not way:
            return []
        out: List[Tuple[float, float, Optional[float], Optional[float]]] = []
        for nid in way.node_ids:
            nd = self.nodes.get(nid)
            if nd:
                out.append((nd["lat"], nd["lon"], nd["local_x"], nd["local_y"]))
        return out

    # ---------- Extract (relation first) ----------
    def iter_lanelet_relations(self) -> Iterable[Tuple[str, RelationData]]:
        for rid, rel in self.relations.items():
            if rel.tags.get('type') == 'lanelet':
                yield rid, rel

    def extract_by_relations(self) -> Dict[str, List[Tuple[str, int, Tuple[float, float, Optional[float], Optional[float]]]]]:
        res = {'left': [], 'right': [], 'centerline': []}
        for rid, rel in self.iter_lanelet_relations():
            role2way: Dict[str, str] = {}
            for m in rel.members:
                if m.type == 'way' and m.role in ('left', 'right', 'centerline'):
                    role2way.setdefault(m.role, m.ref)
            for role in ('left', 'right', 'centerline'):
                wid = role2way.get(role)
                if not wid:
                    continue
                coords = self._coords_of_way(wid)
                for idx, ll in enumerate(coords):
                    res[role].append((rid, idx, ll))
        return res

    # ---------- Extract (fallback by Way subtype) ----------
    def extract_by_way_subtype(self) -> Dict[str, List[Tuple[str, int, Tuple[float, float, Optional[float], Optional[float]]]]]:
        """
        ChallengeClubのOSMのように、Wayの `subtype` で境界が表現されているケースに対応。
        マッピング:
          left_lane_bound  -> left
          right_lane_bound -> right
          center_lane_line -> centerline
        """
        map_subtype_to_role = {
            'left_lane_bound': 'left',
            'right_lane_bound': 'right',
            'center_lane_line': 'centerline',
            # 必要ならここに追加: 'lane_start_bound': 'start' など
        }
        res = {'left': [], 'right': [], 'centerline': []}
        for wid, way in self.ways.items():
            st = way.tags.get('subtype') or way.tags.get('lane_subtype') or ''
            role = map_subtype_to_role.get(st)
            if not role:
                continue
            coords = self._coords_of_way(wid)
            # lanelet_id が無いので wid を代用
            for idx, ll in enumerate(coords):
                res[role].append((wid, idx, ll))
        return res

    def extract_lane_bounds(self) -> Dict[str, List[Tuple[str, int, Tuple[float, float, Optional[float], Optional[float]]]]]:
        """
        まず relation からの抽出を試し、0件なら Way subtype にフォールバック。
        """
        rel_res = self.extract_by_relations()
        total_rel = sum(len(v) for v in rel_res.values())
        if total_rel > 0:
            print(f"[info] extracted (relations): left={len(rel_res['left'])}, right={len(rel_res['right'])}, centerline={len(rel_res['centerline'])}")
            return rel_res

        way_res = self.extract_by_way_subtype()
        print(f"[info] extracted (way-subtype): left={len(way_res['left'])}, right={len(way_res['right'])}, centerline={len(way_res['centerline'])}")
        return way_res

    # ---------- Export ----------
    def export_role_to_csv(self, role: str, output_file: str) -> int:
        if role not in ('left', 'right', 'centerline'):
            raise ValueError("role must be one of: 'left', 'right', 'centerline'")
        self.parse_nodes(); self.parse_ways(); self.parse_relations()
        bounds = self.extract_lane_bounds()
        rows = bounds.get(role, [])
        os.makedirs(os.path.dirname(output_file) or ".", exist_ok=True)
        with open(output_file, 'w', newline='', encoding='utf-8') as fp:
            w = csv.writer(fp)
            # 追加: local_x, local_y を出力
            w.writerow(['lanelet_or_way_id', 'role', 'index', 'latitude', 'longitude', 'x', 'y', 'local_x', 'local_y'])
            for lid, idx, (lat, lon, lox, loy) in rows:
                x, y = self.latlon_to_xy(lat, lon)
                w.writerow([
                    lid, role, idx,
                    f"{lat:.10f}", f"{lon:.10f}",
                    f"{x:.4f}", f"{y:.4f}",
                    "" if lox is None else f"{lox:.4f}",
                    "" if loy is None else f"{loy:.4f}",
                ])
        print(f"[write] {output_file}: {len(rows)} rows")
        return len(rows)

    def export_all_roles_to_dir(self, output_dir: str) -> Dict[str, int]:
        self.parse_nodes(); self.parse_ways(); self.parse_relations()
        bounds = self.extract_lane_bounds()
        os.makedirs(output_dir, exist_ok=True)
        counts: Dict[str, int] = {}
        for role in ('left', 'right', 'centerline'):
            rows = bounds.get(role, [])
            path = os.path.join(output_dir, f"{role}.csv")
            with open(path, 'w', newline='', encoding='utf-8') as fp:
                w = csv.writer(fp)
                # 追加: local_x, local_y を出力
                w.writerow(['lanelet_or_way_id', 'role', 'index', 'latitude', 'longitude', 'x', 'y', 'local_x', 'local_y'])
                for lid, idx, (lat, lon, lox, loy) in rows:
                    x, y = self.latlon_to_xy(lat, lon)
                    w.writerow([
                        lid, role, idx,
                        f"{lat:.10f}", f"{lon:.10f}",
                        f"{x:.4f}", f"{y:.4f}",
                        "" if lox is None else f"{lox:.4f}",
                        "" if loy is None else f"{loy:.4f}",
                    ])
            counts[role] = len(rows)
            print(f"[write] {path}: {counts[role]} rows")
        return counts

    def export_all_to_single_csv(self, output_file: str) -> int:
        self.parse_nodes(); self.parse_ways(); self.parse_relations()
        bounds = self.extract_lane_bounds()
        total = 0
        os.makedirs(os.path.dirname(output_file) or ".", exist_ok=True)
        with open(output_file, 'w', newline='', encoding='utf-8') as fp:
            w = csv.writer(fp)
            # 追加: local_x, local_y を出力
            w.writerow(['lanelet_or_way_id', 'role', 'index', 'latitude', 'longitude', 'x', 'y', 'local_x', 'local_y'])
            for role in ('left', 'right', 'centerline'):
                for lid, idx, (lat, lon, lox, loy) in bounds.get(role, []):
                    x, y = self.latlon_to_xy(lat, lon)
                    w.writerow([
                        lid, role, idx,
                        f"{lat:.10f}", f"{lon:.10f}",
                        f"{x:.4f}", f"{y:.4f}",
                        "" if lox is None else f"{lox:.4f}",
                        "" if loy is None else f"{loy:.4f}",
                    ])
                    total += 1
        print(f"[write] {output_file}: total {total} rows")
        return total

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--osm", required=True)
    p.add_argument("--outdir")
    p.add_argument("--single-csv")
    p.add_argument("--origin-lat", type=float)
    p.add_argument("--origin-lon", type=float)
    args = p.parse_args()

    origin = (args.origin_lat, args.origin_lon) if (args.origin_lat is not None and args.origin_lon is not None) else None
    ex = OSMExtractor(args.osm, origin_latlon=origin)

    if args.outdir:
        ex.export_all_roles_to_dir(args.outdir)
    if args.single_csv:
        ex.export_all_to_single_csv(args.single_csv)
    if not args.outdir and not args.single_csv:
        ex.export_all_roles_to_dir("./extracted_bounds")

if __name__ == "__main__":
    # ==== デフォルト設定 ====
    DEFAULT_OSM = "workspace/src/aichallenge_submit/aichallenge_submit_launch/map/lanelet2_map.osm"
    DEFAULT_OUTDIR = "./tools/extracted_bounds"
    DEFAULT_SINGLE_CSV = None  # 例: "./bounds_all.csv" にしたい場合は文字列で指定

    # ==== 実行 ====
    origin = None  # (lat, lon) を指定したい場合はここにタプルで入れる
    ex = OSMExtractor(DEFAULT_OSM, origin_latlon=origin)

    if DEFAULT_OUTDIR:
        ex.export_all_roles_to_dir(DEFAULT_OUTDIR)
    if DEFAULT_SINGLE_CSV:
        ex.export_all_to_single_csv(DEFAULT_SINGLE_CSV)
    if not DEFAULT_OUTDIR and not DEFAULT_SINGLE_CSV:
        ex.export_all_roles_to_dir("./extracted_bounds")
