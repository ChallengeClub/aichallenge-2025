import tkinter as tk
from tkinter import filedialog
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrow

def calculate_yaw(x_quat, y_quat, z_quat, w_quat):
    """クォータニオンからyaw角度を計算"""
    siny_cosp = 2 * (w_quat * z_quat + x_quat * y_quat)
    cosy_cosp = 1 - 2 * (y_quat ** 2 + z_quat ** 2)
    yaw = np.arctan2(siny_cosp, cosy_cosp)
    return yaw

def plot_data(df):
    """CSVデータをプロット"""
    x = df['x']
    y = df['y']
    speed = df['speed']
    yaw_angles = [calculate_yaw(row['x_quat'], row['y_quat'], row['z_quat'], row['w_quat']) for _, row in df.iterrows()]

    fig, ax = plt.subplots()
    sc = ax.scatter(x, y, c=speed, cmap='viridis', label='Speed')
    plt.colorbar(sc, label='Speed')
    
    # 各ポイントに矢印を描画
    for i in range(len(x)):
        dx = np.cos(yaw_angles[i]) * 0.1  # 矢印の長さを調整
        dy = np.sin(yaw_angles[i]) * 0.1
        ax.add_patch(FancyArrow(x[i], y[i], dx, dy, width=0.5, color='red'))
    
    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_title('2D Visualization of Coordinates with Direction')
    plt.show()

def open_file():
    """ファイルを開き、データを読み込んでプロット"""
    file_path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
    if file_path:
        df = pd.read_csv(file_path)
        plot_data(df)

# GUI設定
root = tk.Tk()
root.title("CSV Visualizer")

open_button = tk.Button(root, text="Select CSV File", command=open_file)
open_button.pack()

root.mainloop()
