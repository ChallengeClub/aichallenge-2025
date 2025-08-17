import pandas as pd

# CSVファイルのパス
csv_file1 = './inner_lane_bound.csv'
csv_file2 = './out_lane_bound.csv'
output_csv = 'lane.csv'

# CSVファイルを読み込む
df1 = pd.read_csv(csv_file1, usecols=[0, 1])
df2 = pd.read_csv(csv_file2, usecols=[0, 1])

# データフレームを結合する
merged_df = pd.concat([df1, df2], axis=1)

# 新しいCSVファイルとして保存する
merged_df.to_csv(output_csv, index=False)