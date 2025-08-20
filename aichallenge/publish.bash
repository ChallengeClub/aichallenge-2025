#!/bin/bash

# Help function to display usage
usage() {
    echo "Usage: $0 [OPTION]"
    echo "Options:"
    echo "  screen      Capture screen via service call"
    echo "  control     Request control mode change"
    echo "  initial     Set initial pose"
    echo "  all         Execute all commands in sequence"
    echo "  help        Display this help message"
    exit 1
}

# Function to capture screen
capture_screen() {
    echo "Capturing screen..."
    timeout 10s ros2 service call /debug/service/capture_screen std_srvs/srv/Trigger >/dev/null
    if [ $? -eq 124 ]; then
        echo "Warning: Screen capture service call timed out after 10 seconds"
    else
        echo "Screen capture requested successfully"
    fi
}

# Function to request control mode
request_control() {
    echo "Requesting control mode change..."
    timeout 20s ros2 service call /control/control_mode_request autoware_auto_vehicle_msgs/srv/ControlModeCommand '{mode: 1}' >/dev/null
    if [ $? -eq 124 ]; then
        echo "Warning: Control mode request timed out after 20 seconds"
    else
        echo "Control mode change requested successfully"
    fi
}

# Function to set initial pose
set_initial_pose() {
    echo "Setting initial pose..."
    timeout 20s bash -c '
    ros2 topic pub -1 /initialpose geometry_msgs/msg/PoseWithCovarianceStamped "{ 
      header: {
        frame_id: \"map\"
      },
      pose: {
        pose: {
          position: {
            x: 89666.01577151686,
            y: 43124.3307874416,
            z: 0.0
          },
          orientation: {
            x: 0.0,
            y: 0.0,
            z: -0.9683930510846941,
            w: 0.24942914547196962
          }
        }
      }
    }"' >/dev/null
    if [ $? -eq 124 ]; then
        echo "Warning: Initial pose publication timed out after 20s"
    else
        echo "Initial pose set successfully"
    fi
}

check_awsim() {
    timeout_seconds=60
    elapsed=0
    while ! timeout 10s ros2 topic echo /awsim/control_cmd 2>/dev/null | grep -q "sec:"; do
        sleep 0.5
        elapsed=$((elapsed + 10))
        echo "Waiting for /awsim/control_cmd topic to be available... (${elapsed}s elapsed)"

        if [ $elapsed -ge $timeout_seconds ]; then
            echo "Warning: /awsim/control_cmd topic not available after ${timeout_seconds}s timeout. Continuing anyway..."
            break
        fi
    done
    sleep 1
    echo "System is ready, executing publish commands..."
}

check_capture() {
    # Start recording rviz2
    echo "Check if screen capture is ready"
    timeout_seconds=60 # 1 minute timeout
    elapsed=0
    until (ros2 service type /debug/service/capture_screen >/dev/null); do
        sleep 5
        elapsed=$((elapsed + 5))
        echo "Screen capture is not ready (${elapsed}s elapsed)"

        if [ $elapsed -ge $timeout_seconds ]; then
            echo "Warning: Screen capture service not available after ${timeout_seconds}s timeout. Continuing anyway..."
            break
        fi
    done
}

# Check if an argument was provided
if [ $# -eq 0 ]; then
    usage
fi

# Process based on provided argument
case "$1" in
check)
    check_capture
    check_awsim
    ;;
screen)
    capture_screen
    ;;
control)
    request_control
    ;;
initial)
    set_initial_pose
    ;;
all)
    sleep 5
    set_initial_pose
    request_control
    ;;
help)
    usage
    ;;
*)
    echo "Error: Invalid option '$1'"
    usage
    ;;
esac

exit 0
