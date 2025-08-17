# OSM to lane CSV converter
import xml.etree.ElementTree as ET
import csv
from collections import defaultdict, deque
import argparse

# コマンドライン引数の処理
parser = argparse.ArgumentParser(description="Convert lanelet2 OSM to lane.csv format.")
parser.add_argument("--osm_path", type=str, default="../../workspace/src/aichallenge_submit/aichallenge_submit_launch/map/lanelet2_map.osm", help="input OSM file path")
parser.add_argument("--csv_path", type=str, default="../../workspace/src/aichallenge_submit/aichallenge_submit_launch/map/lanelet2_map.osm.csv", help="output CSV file path")
args = parser.parse_args()
osm_path = args.osm_path
csv_path = args.csv_path

tree = ET.parse(osm_path)
root = tree.getroot()

# node情報を辞書化
nodes = {}
for node in root.findall("node"):
    node_id = node.attrib["id"]
    tags = {tag.attrib["k"]: tag.attrib["v"] for tag in node.findall("tag")}
    if "local_x" in tags and "local_y" in tags:
        nodes[node_id] = (float(tags["local_x"]), float(tags["local_y"]))

# laneletのleft/right way idを抽出
left_way_ids, right_way_ids = [], []
for relation in root.findall("relation"):
    tags = {tag.attrib["k"]: tag.attrib["v"] for tag in relation.findall("tag")}
    if tags.get("type") == "lanelet":
        for member in relation.findall("member"):
            if member.attrib["role"] == "left":
                left_way_ids.append(member.attrib["ref"])
            elif member.attrib["role"] == "right":
                right_way_ids.append(member.attrib["ref"])

# way id -> node id 列
def get_way_nodes():
    way_nodes = {}
    for way in root.findall("way"):
        way_id = way.attrib["id"]
        node_list = [nd.attrib["ref"] for nd in way.findall("nd")]
        way_nodes[way_id] = node_list
    return way_nodes

way_nodes = get_way_nodes()

# wayを端点でつなげて連続したノード列を作る
def connect_ways(way_id_list):
    # 端点からwayを引く辞書
    endpoints = defaultdict(list)
    for wid in way_id_list:
        nlist = way_nodes[wid]
        endpoints[nlist[0]].append((wid, True))   # 順方向
        endpoints[nlist[-1]].append((wid, False)) # 逆方向

    used = set()
    result = []

    # 先頭からスタート
    queue = deque()
    start_wid = way_id_list[0]
    queue.append((start_wid, True))
    used.add(start_wid)

    while queue:
        wid, forward = queue.popleft()
        nlist = way_nodes[wid]
        nlist = nlist if forward else list(reversed(nlist))
        if not result:
            result.extend(nlist)
        else:
            # つなぎ目が重複しないように
            if result[-1] == nlist[0]:
                result.extend(nlist[1:])
            else:
                result.extend(nlist)
        # 次のwayを探す
        next_node = nlist[-1]
        for next_wid, next_forward in endpoints[next_node]:
            if next_wid not in used:
                queue.append((next_wid, next_forward))
                used.add(next_wid)
                break
    return result

left_nodes = connect_ways(left_way_ids)
right_nodes = connect_ways(right_way_ids)

# ノード数を揃える
min_len = min(len(left_nodes), len(right_nodes))
left_nodes = left_nodes[:min_len]
right_nodes = right_nodes[:min_len]

# ループを閉じるため、左側の最初の点を最後に追加
lx0, ly0 = nodes.get(left_nodes[0], (None, None))
rx0, ry0 = nodes.get(right_nodes[0], (None, None))
if None not in (lx0, ly0, rx0, ry0):
    left_nodes.append(left_nodes[0])
    right_nodes.append(right_nodes[0])

# CSV出力
with open(csv_path, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    for l, r in zip(left_nodes, right_nodes):
        lx, ly = nodes.get(l, (None, None))
        rx, ry = nodes.get(r, (None, None))
        if None not in (lx, ly, rx, ry):
            writer.writerow([lx, ly, rx, ry])

print(f"{csv_path} を出力しました")
