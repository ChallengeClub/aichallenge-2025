# autowareのみ起動
run-autoware-only:
	@if ! docker compose ps autoware | grep -q "Up"; then \
		echo "Starting autoware container..."; \
		docker compose up -d autoware; \
	else \
		echo "Autoware container already running"; \
	fi
	@echo "Starting all services without build..."
	docker compose exec -T autoware bash -c "bash run_autoware.bash awsim" &

# racing kartとzenohの起動 
run-driver-zenoh:
	docker compose up -d driver zenoh

# autowareのbuildのみ
build-only:
	@if ! docker compose ps autoware | grep -q "Up"; then \
		echo "Starting autoware container..."; \
		docker compose up -d autoware; \
	else \
		echo "Autoware container already running"; \
	fi
	@echo "Building workspace (this may take time and might fail with OOM)..."
	@echo "If this fails, use the pre-built version with 'make setup'"
	docker compose exec -T autoware bash -c "source /opt/ros/humble/setup.bash && source /autoware/install/setup.bash && timeout 1800 bash build_autoware.bash" || echo "Build failed or timed out"

# 上記全部やっちゃう
all: build-only run-driver-zenoh run-autoware-only
	@echo "All services started, showing logs..."
	docker compose logs -f autoware driver zenoh

# Stop all services
stop-all:
	docker compose down
