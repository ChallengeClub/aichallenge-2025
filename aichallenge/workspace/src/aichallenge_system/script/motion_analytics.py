#!/usr/bin/env python3
import argparse
from datetime import datetime
import json
import os
import sys
import math
from pathlib import Path

import plotly.graph_objects as go
from plotly.subplots import make_subplots

from rosbag2_py import ConverterOptions
from rosbag2_py import SequentialReader
from rosbag2_py import StorageOptions

from rclpy.serialization import deserialize_message
from rosidl_runtime_py.utilities import get_message


def save_and_show_plot(fig, output_dir, file_name):
    output_dir_path = Path(output_dir)
    output_dir_path.mkdir(parents=True, exist_ok=True)
    [name, suffix] = file_name.split(".")
    timestamp = datetime.now().strftime("%y-%m-%d-%H-%M-%S")
    try:
        fig.write_image(output_dir_path / f"{name}-{timestamp}.{suffix}", width=1800, height=600)
    except Exception as e:
        print(f"Warning: Could not write image file. Error: {e}")
    output_path_html = output_dir_path / f"{name}-{timestamp}.html"
    fig.write_html(output_path_html)


def infer_configs(
    bag_uri: str,
    storage_ids={".db3": ("sqlite3", "cdr", "cdr"), ".mcap": ("mcap", "", "")},
) -> tuple:
    bag_uri_path = Path(bag_uri)
    if os.path.isfile(bag_uri):
        data_file = bag_uri_path
    else:
        data_file = next(p for p in bag_uri_path.glob("*") if p.suffix in storage_ids)
        if data_file.suffix not in storage_ids:
            raise ValueError(f"Unsupported storage id: {data_file.suffix}")
    return storage_ids[data_file.suffix]


def create_reader(input_uri: str) -> SequentialReader:
    """Create a reader object from the given input uri. The input uri could be a directory or a file."""
    storage_id, isf, osf = infer_configs(input_uri)
    storage_options = StorageOptions(
        uri=input_uri,
        storage_id=storage_id,
    )
    converter_options = ConverterOptions(
        input_serialization_format=isf,
        output_serialization_format=osf,
    )

    reader = SequentialReader()
    reader.open(storage_options, converter_options)
    return reader


def sync_topic(data1, data2) -> list:
    """
    Synchronizes data2 to data1 based on timestamps.
    For each timestamp in data1, it finds the latest data in data2 with a timestamp less than or equal to it.
    This implementation is O(N+M) assuming both lists are sorted by timestamp.
    """
    sync_data = []
    if not data1 or not data2:
        return []
    idx2 = 0
    for idx1 in range(len(data1)):
        while idx2 + 1 < len(data2) and data2[idx2 + 1][0] <= data1[idx1][0]:
            idx2 += 1
        sync_data.append(data2[idx2])
    return sync_data


analyze_topic_list = [
    "/localization/kinematic_state",
    "/localization/acceleration",
    "/vehicle/status/steering_status",
]


class Analyzer:
    def __init__(self, input_dir, output_dir):
        self.input_bag_dir = input_dir
        self.output_dir = output_dir
        self.window_size = 10
        self.file_name = "motion_analytics.png"
        self.poses = []
        self.velocities = []
        self.max_long_accel = None
        self.min_long_accel = None
        self.max_lat_accel = None
        self.min_lat_accel = None

    def _read_laps_data(self):
        """lapsデータをresult-details.jsonから読み込む""" 
        original_details_path = Path(self.input_bag_dir).parent / "result-details.json"
        laps_data = []
        if original_details_path.exists():
            try:
                with open(original_details_path, "r") as f:
                    original_data = json.load(f)
                    laps_data = original_data.get("laps", [])
            except (json.JSONDecodeError, FileNotFoundError):
                # ファイルが存在しない、または中身が不正な場合は空のリストを返す
                pass
        return laps_data

    def _read_bag_data(self):
        reader = create_reader(self.input_bag_dir)
        pose_time_stamp = []
        pose_speed = []
        pose_acceleration = []
        pose_lateral_acceleration = []
        pose_steering = []
        topic_type_list = {}

        for topic_type in reader.get_all_topics_and_types():
            topic_type_list[topic_type.name] = topic_type.type

        while reader.has_next():
            topic_name, msg, stamp = reader.read_next()
            stamp = stamp * 1e-9
            if topic_name in analyze_topic_list:
                data = deserialize_message(msg, get_message(topic_type_list[topic_name]))
                if topic_name == "/localization/kinematic_state":
                    if data.pose.pose.position.x != 0.0 or data.pose.pose.position.y != 0.0:
                        pose_time_stamp.append(
                            [stamp, data.pose.pose.position.x, data.pose.pose.position.y]
                        )
                        # For result-details.json
                        self.poses.append({
                            "position": {
                                "x": data.pose.pose.position.x,
                                "y": data.pose.pose.position.y,
                                "z": data.pose.pose.position.z
                            },
                            "orientation": {
                                "x": data.pose.pose.orientation.x,
                                "y": data.pose.pose.orientation.y,
                                "z": data.pose.pose.orientation.z,
                                "w": data.pose.pose.orientation.w
                            }
                        })
                        self.velocities.append({
                            "x": data.twist.twist.linear.x,
                            "y": data.twist.twist.linear.y,
                            "z": data.twist.twist.linear.z
                        })
                        pose_speed.append([stamp, data.twist.twist.linear.x])
                        
                        # Calculate lateral acceleration from kinematic state
                        v_x = data.twist.twist.linear.x
                        omega_z = data.twist.twist.angular.z
                        lat_accel = v_x * omega_z
                        pose_lateral_acceleration.append([stamp, lat_accel])

                elif topic_name == "/localization/acceleration":
                    pose_acceleration.append([stamp, data.accel.accel.linear.x])
                elif topic_name == "/vehicle/status/steering_status":
                    pose_steering.append([stamp, math.degrees(data.steering_tire_angle)])
        
        return pose_time_stamp, pose_speed, pose_acceleration, pose_lateral_acceleration, pose_steering, topic_type_list

    def _sync_and_filter_data(self, pose_time_stamp, pose_speed, pose_acceleration, pose_lateral_acceleration, pose_steering):
        if pose_speed and pose_time_stamp:
            pose_speed_filter = sync_topic(pose_time_stamp, pose_speed)
        else:
            pose_speed_filter = []

        if pose_acceleration and pose_time_stamp:
            pose_acceleration_filter = sync_topic(pose_time_stamp, pose_acceleration)
        else:
            pose_acceleration_filter = []

        if pose_lateral_acceleration and pose_time_stamp:
            pose_lateral_acceleration_filter = sync_topic(pose_time_stamp, pose_lateral_acceleration)
        else:
            pose_lateral_acceleration_filter = []

        if pose_steering and pose_time_stamp:
            pose_steering_filter = sync_topic(pose_time_stamp, pose_steering)
        else:
            pose_steering_filter = []

        return pose_speed_filter, pose_acceleration_filter, pose_lateral_acceleration_filter, pose_steering_filter
    
    def _create_plots(self, pose_time_stamp, pose_speed_filter, pose_acceleration_filter, pose_steering_filter):
        fig = make_subplots(rows=1, cols=3, subplot_titles=("Velocity", "Acceleration", "Steering Angle"))

        if not pose_time_stamp:
            # データがない場合は空のプロットを返す
            return fig

        pose_x = [d[1] for d in pose_time_stamp]
        pose_y = [d[2] for d in pose_time_stamp]
        speed_values = [d[1] for d in pose_speed_filter]
        accel_values = [d[1] for d in pose_acceleration_filter]
        steering_values = [d[1] for d in pose_steering_filter]

        # 速度のプロット
        if speed_values:
            fig.add_trace(go.Scatter(
                x=pose_x, y=pose_y, mode='markers',
                marker=dict(
                    size=3, color=speed_values, colorscale='Viridis', showscale=True,
                    cmin=min(speed_values), cmax=max(speed_values),  # Set color range to data range
                    colorbar=dict(title='Velocity [m/s]', thickness=15, x=1.02, y=0.83, len=0.3)
                ),
                name='Velocity'
            ), row=1, col=1)

        # 加速度のプロット
        if accel_values:
            fig.add_trace(go.Scatter(
                x=pose_x, y=pose_y, mode='markers',
                marker=dict(
                    size=3, color=accel_values, colorscale='Plasma', showscale=True,
                    cmin=min(accel_values), cmax=max(accel_values),  # Set color range to data range
                    colorbar=dict(title='Acceleration [m/s^2]', thickness=15, x=1.02, y=0.5, len=0.3)
                ),
                name='Acceleration'
            ), row=1, col=2)

        # ステアリングのプロット
        if steering_values:
            fig.add_trace(go.Scatter(
                x=pose_x, y=pose_y, mode='markers',
                marker=dict(
                    size=3, color=steering_values, colorscale='RdBu', showscale=True,
                    cmin=-5.0, cmax=5.0,
                    colorbar=dict(title='Steering [deg]', thickness=15, x=1.02, y=0.17, len=0.3)
                ),
                name='Steering'
            ), row=1, col=3)

        # レイアウトの更新
        fig.update_xaxes(title_text="x [m]", row=1, col=1)
        fig.update_yaxes(title_text="y [m]", row=1, col=1)
        fig.update_xaxes(title_text="x [m]", row=1, col=2)
        fig.update_yaxes(row=1, col=2)
        fig.update_xaxes(title_text="x [m]", row=1, col=3)
        fig.update_yaxes(row=1, col=3)
        
        fig.update_layout(
            width=1800,
            height=600,
            template='plotly_dark',
            font=dict(size=16),
            showlegend=False,
            margin=dict(r=180)  # 右マージンを増やしてカラーバーのスペースを確保
        )

        return fig

    def plot(self):
        pose_time_stamp, pose_speed, pose_acceleration, pose_lateral_acceleration, pose_steering, _ = self._read_bag_data()

        # 1周目のデータをプロットから除外する
        laps_data = self._read_laps_data()
        if laps_data and len(laps_data) > 0 and pose_time_stamp:
            first_lap_duration = laps_data[0]
            start_time = pose_time_stamp[0][0]
            first_lap_end_time = start_time + first_lap_duration

            # 2周目が始まる最初のインデックスを見つける
            start_index_for_plot = -1
            for i, (ts, _, _) in enumerate(pose_time_stamp):
                if ts > first_lap_end_time:
                    start_index_for_plot = i
                    break

            if start_index_for_plot != -1:
                print(f"INFO: 1周目のデータをグラフから除外します。({start_index_for_plot}番目のデータから表示)")
                pose_time_stamp = pose_time_stamp[start_index_for_plot:]
            else:
                print("INFO: 2周目以降のデータが見つからなかったため、グラフは空になります。")
                pose_time_stamp = []  # 2周目のデータがなければプロットしない

        pose_speed_filter, pose_acceleration_filter, pose_lateral_acceleration_filter, pose_steering_filter = self._sync_and_filter_data(
            pose_time_stamp, pose_speed, pose_acceleration, pose_lateral_acceleration, pose_steering
        )

        long_accel_values = [d[1] for d in pose_acceleration_filter]
        if long_accel_values:
            self.max_long_accel = max(long_accel_values)
            self.min_long_accel = min(long_accel_values)
            print(f"Longitudinal Acceleration - Max: {self.max_long_accel:.2f} m/s^2, Min: {self.min_long_accel:.2f} m/s^2")

        lat_accel_values = [d[1] for d in pose_lateral_acceleration_filter]
        if lat_accel_values:
            self.max_lat_accel = max(lat_accel_values)
            self.min_lat_accel = min(lat_accel_values)
            print(f"Lateral Acceleration - Max: {self.max_lat_accel:.2f} m/s^2, Min: {self.min_lat_accel:.2f} m/s^2")


        fig = self._create_plots(pose_time_stamp, pose_speed_filter, pose_acceleration_filter, pose_steering_filter)

        save_and_show_plot(fig, self.output_dir, self.file_name)

    def save_details_json(self):
        # AWSIMが生成するlapsは利用価値があるので、もしあれば読み込んでマージする
        laps_data = self._read_laps_data()

        output_data = {
            "laps": laps_data,
            "velocities": self.velocities,
            "poses": self.poses,
            "seed": 0,
            "max_longitudinal_acceleration": self.max_long_accel,
            "min_longitudinal_acceleration": self.min_long_accel,
            "max_lateral_acceleration": self.max_lat_accel,
            "min_lateral_acceleration": self.min_lat_accel,
        }
        output_path = Path(self.output_dir) / "result-details-from-bag.json"
        with open(output_path, "w") as f:
            json.dump(output_data, f, indent=4)
        print(f"✅ Saved full details to: {output_path}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input")
    parser.add_argument("--output", default=datetime.now().strftime("%y-%m-%d-%H-%M-%S"))
    parser.add_argument("--save-details", action="store_true", help="Save pose and velocity data to a json file.")
    args = parser.parse_args()

    analyzer = Analyzer(args.input, args.output)
    analyzer.plot()

    if args.save_details:
        analyzer.save_details_json()


if __name__ == "__main__":
    main()
