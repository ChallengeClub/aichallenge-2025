#!/bin/bash

# Create a temporary file to store process IDs
PID_FILE=$(mktemp)
echo "Process ID file: $PID_FILE"

# recursively get child processes
get_child_pids() {
    local parent_pid=$1
    local child_pids

    child_pids=$(pgrep -P "$parent_pid")
    for pid in $child_pids; do
        echo "$pid" >>"$PID_FILE"
        get_child_pids "$pid"
    done
}

# update process list
update_process_list() {
    local main_pids=("$PID_AWSIM" "$PID_AUTOWARE" "$PID_ROSBAG")

    # clear the PID file
    : >"$PID_FILE"

    # record main process PIDs
    for pid in "${main_pids[@]}"; do
        if [[ -n $pid ]] && kill -0 "$pid" 2>/dev/null; then
            echo "$pid" >>"$PID_FILE"
            get_child_pids "$pid"
        fi
    done

    # get child processes of main processes
    for pattern in "ros2" "autoware" "web_server" "rviz"; do
        pgrep -f "$pattern" | while read -r pid; do
            # check if the PID is already in the file
            if ! grep -q "^$pid$" "$PID_FILE"; then
                echo "$pid" >>"$PID_FILE"
            fi
        done
    done
}

# shutdown function
graceful_shutdown() {
    local pid=$1
    local timeout=${2:-30} # timeout in seconds, default is 30 seconds

    if [[ -n $pid ]] && kill -0 "$pid" 2>/dev/null; then
        echo "Sending SIGTERM to PID $pid"
        kill "$pid"

        # wait for the process to terminate
        local count=0
        while kill -0 "$pid" 2>/dev/null && [ $count -lt $((timeout * 10)) ]; do
            sleep 0.1
            ((count++))
        done

        # if the process is still running after timeout, force kill
        if kill -0 "$pid" 2>/dev/null; then
            echo "Process $pid did not terminate gracefully after $timeout seconds, forcing kill"
            kill -9 "$pid"
            sleep 0.1
        fi
    fi
}

# Function to handle Ctrl+C and normal termination
cleanup() {
    echo "Termination signal received. Cleaning up..."

    # get the latest process list
    update_process_list

    # Stop recording rosbag
    echo "Stop rosbag"
    if [[ -n $PID_ROSBAG ]] && kill -0 "$PID_ROSBAG" 2>/dev/null; then
        graceful_shutdown "$PID_ROSBAG" 15
    fi

    # Ensure all data is written to disk and wait for rosbag to be finalized
    echo "Syncing filesystem to ensure rosbag is written..."
    sync
    sleep 5

    # shutdown ROS2 nodes
    echo "Shutting down ROS2 nodes gracefully..."
    ros2 node list 2>/dev/null | while read -r node; do
        echo "Shutting down node: $node"
        ros2 lifecycle set "$node" shutdown 2>/dev/null || true
        ros2 node kill "$node" 2>/dev/null || true
    done

    # Stop Autoware
    echo "Stop Autoware"
    if [[ -n $PID_AUTOWARE ]] && kill -0 "$PID_AUTOWARE" 2>/dev/null; then
        graceful_shutdown "$PID_AUTOWARE" 3
    fi

    # Stop AWSIM
    echo "Stop AWSIM"
    if [[ -n $PID_AWSIM ]] && kill -0 "$PID_AWSIM" 2>/dev/null; then
        graceful_shutdown "$PID_AWSIM" 3
    fi

    # Compress rosbag
    echo "Compress rosbag"
    if [ -f "rosbag2_autoware/metadata.yaml" ]; then
        # Postprocess result
        echo "Postprocess result"
        python3 /aichallenge/workspace/src/aichallenge_system/script/motion_analytics.py --input rosbag2_autoware --output . --save-details
        # Convert result after motion_analytics creates the details file
        echo "Convert result"
        python3 /aichallenge/workspace/src/aichallenge_system/script/result-converter.py 60 11 --input result-details-from-bag.json

        tar -czf rosbag2_autoware.tar.gz rosbag2_autoware
        rm -rf rosbag2_autoware
    else
        echo "Warning: rosbag2_autoware/metadata.yaml not found. Skipping postprocessing and compression."
    fi

    # check for remaining processes
    echo "Checking for remaining processes..."
    if [[ -f $PID_FILE ]]; then
        while read -r pid; do
            if kill -0 "$pid" 2>/dev/null; then
                echo "Attempting graceful shutdown of remaining PID $pid"
                graceful_shutdown "$pid" 3
            fi
        done <"$PID_FILE"
        rm "$PID_FILE"
    fi

    echo "Cleanup complete."
    # Stop ros2 daemon
    ros2 daemon stop
    exit 0
}

move_window() {
    local has_gpu
    has_gpu=$(command -v nvidia-smi >/dev/null && echo 1 || echo 0)

    while true; do
        local has_awsim has_rviz
        has_awsim=$(wmctrl -l | grep -q "AWSIM" && echo 1 || echo 0)
        has_rviz=$(wmctrl -l | grep -q "RViz" && echo 1 || echo 0)

        if [ "$has_rviz" -eq 1 ] && { [ "$has_awsim" -eq 1 ] || [ "$has_gpu" -eq 0 ]; }; then
            break
        fi
        sleep 1
    done
    echo "AWSIMとRVizのウィンドウが見つかりました"
    # Move windows
    wmctrl -a "RViz" && wmctrl -r "RViz" -e 0,0,0,1920,1043
    sleep 1
    wmctrl -a "AWSIM" && wmctrl -r "AWSIM" -e 0,0,0,900,1043
    sleep 2
}

# Trap Ctrl+C (SIGINT) and normal termination (EXIT)
trap cleanup SIGINT SIGTERM EXIT

# Move working directory
OUTPUT_DIRECTORY=$(date +%Y%m%d-%H%M%S)
cd /output || exit
mkdir "$OUTPUT_DIRECTORY"
ln -nfs "$OUTPUT_DIRECTORY" latest
cd "$OUTPUT_DIRECTORY" || exit

# shellcheck disable=SC1091
source /aichallenge/workspace/install/setup.bash
sudo ip link set multicast on lo
sudo sysctl -w net.core.rmem_max=2147483647 >/dev/null

# Start AWSIM with nohup
echo "Start AWSIM"
nohup /aichallenge/run_simulator.bash >/dev/null &
PID_AWSIM=$!
echo "AWSIM PID: $PID_AWSIM"
echo "$PID_AWSIM" >"$PID_FILE"
# recursively get child processes
get_child_pids "$PID_AWSIM"
sleep 3

# Start Autoware with nohup
echo "Start Autoware"
nohup /aichallenge/run_autoware.bash awsim >autoware.log 2>&1 &
PID_AUTOWARE=$!
echo "Autoware PID: $PID_AUTOWARE"
echo "$PID_AUTOWARE" >>"$PID_FILE"
# recursively get child processes
get_child_pids "$PID_AUTOWARE"
sleep 3

# run updater
(
    while true; do
        sleep 5

        # update if the main process is still running
        if [[ -n $PID_AWSIM ]] && kill -0 "$PID_AWSIM" 2>/dev/null; then
            update_process_list
        else
            # if the main process is not running, exit the loop
            break
        fi
    done
) &
PID_UPDATER=$!
echo "$PID_UPDATER" >>"$PID_FILE"

move_window
bash /aichallenge/publish.bash check
move_window
bash /aichallenge/publish.bash all
bash /aichallenge/publish.bash screen

# Start recording rosbag with nohup
echo "Start rosbag"
nohup /aichallenge/record_rosbag.bash >/dev/null 2>&1 &
PID_ROSBAG=$!
echo "ROS Bag PID: $PID_ROSBAG"
echo "$PID_ROSBAG" >>"$PID_FILE"
# recursively get child processes
get_child_pids "$PID_ROSBAG"

# Wait for AWSIM to finish (this is the main process we're waiting for)
wait "$PID_AWSIM"

# Stop recording rviz2
echo "Stop screen capture"
bash /aichallenge/publish.bash screen
sleep 3

# If AWSIM finished naturally, we'll proceed with the rest of the cleanup
cleanup
