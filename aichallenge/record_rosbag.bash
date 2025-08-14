#!/bin/bash

# shellcheck disable=SC1091
source "/aichallenge/workspace/install/setup.bash"

# Topics with data (excluding 0-message topics from original bag)
# For debugging, only record essential topics to reduce load.
# Restore all topics to ensure the evaluation system gets all required data.
TOPICS=(
    "/aichallenge/awsim/status"
    "/awsim/control_cmd"
    "/clock"
    "/control/command/actuation_cmd"
    "/control/command/control_cmd"
    "/control/debug/lookahead_point"
    "/diagnostics"
    "/localization/acceleration"
    "/localization/biased_pose"
    "/localization/biased_pose_with_covariance"
    "/localization/debug"
    "/localization/estimated_yaw_bias"
    "/localization/gyro_twist"
    "/localization/gyro_twist_raw"
    "/localization/imu_gnss_poser/pose_with_covariance"
    "/localization/kinematic_state"
    "/localization/pose"
    "/localization/pose_with_covariance"
    "/localization/twist"
    "/localization/twist_estimator/twist_with_covariance"
    "/localization/twist_estimator/twist_with_covariance_raw"
    "/localization/twist_with_covariance"
    "/map/vector_map"
    "/map/vector_map_marker"
    "/output/raw_control_cmd"
    "/parameter_events"
    "/planning/mission_planning/goal"
    "/planning/scenario_planning/trajectory"
    "/robot_description"
    "/rosout"
    "/sensing/gnss/gnss_fixed"
    "/sensing/gnss/nav_sat_fix"
    "/sensing/gnss/pose"
    "/sensing/gnss/pose_with_covariance"
    "/sensing/imu/imu_data"
    "/sensing/imu/imu_raw"
    "/sensing/vehicle_velocity_converter/twist_with_covariance"
    "/system/system_monitor/cpu_monitor/cpu_usage"
    "/tf"
    "/tf_static"
    "/vehicle/status/control_mode"
    "/vehicle/status/gear_status"
    "/vehicle/status/hazard_lights_status"
    "/vehicle/status/steering_status"
    "/vehicle/status/velocity_status"
)

ros2 bag record "${TOPICS[@]}" -o rosbag2_autoware
