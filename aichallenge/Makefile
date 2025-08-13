# make file inspired by https://roborovsky-racers.github.io/RoborovskyNote/
sim:
	@sudo ip link set multicast on lo
	@sudo sysctl -w net.core.rmem_max=2147483647 >/dev/null
	@echo "Start AWSIM"
	@/aichallenge/simulator/AWSIM/AWSIM.x86_64 --timeout 86400.0 &

aw:
	@echo "Start Auwoware"
	@bash run_autoware.bash awsim

init:
	@./publish_initialpose.py

start:
	@echo "Start control"
	ros2 topic pub -t 10 /control/control_mode_request_topic std_msgs/msg/Bool '{data: true}' >/dev/null &

reset:
	@echo "Reset simulation"
	@ros2 topic pub --once /aichallenge/awsim/reset std_msgs/msg/Empty {} >/dev/null &
	@./publish_initialpose.py

all: sim aw
	@echo ""
