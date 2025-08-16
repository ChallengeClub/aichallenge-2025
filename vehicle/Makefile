SHELL := /bin/bash
# 既にコンテナが立ち上がっている場合はログの表示を行います。
# autowareのみ起動・ログ表示
autoware:
	docker compose up -d autoware
	docker compose logs -f autoware

# racing kartの起動・ログ表示
driver:
	docker compose up -d driver
	docker compose logs -f driver

# zenohの起動・ログ表示
zenoh:
	docker compose up -d zenoh
	docker compose logs -f zenoh

# racing_kart_interfaceのbashを起動
driver-bash:
	docker compose run driver bash

# racing kartとzenohの起動・ログ表示
driver-zenoh:
	docker compose up -d driver zenoh
	docker compose logs -f driver zenoh

# aicコンテナにてros2 bag record -a
rosbag:
	docker compose up -d rosbag
	docker compose logs -f rosbag

# Autowareとracing kartとzenohの起動
run-full-system:
	docker compose up -d autoware driver zenoh
	docker compose logs -f autoware driver zenoh

# Download submission data by asking for credentials interactively
# Usage:
#   make download [SUBMISSION_ID=<id>]
download:
	@read -p "Enter Username: " USERNAME; \
	read -sp "Enter Password: " PASSWORD; \
	echo ""; \
	if [ -z "$$USERNAME" ] || [ -z "$$PASSWORD" ]; then \
		echo "\nError: USERNAME and PASSWORD must be provided."; \
		exit 1; \
	fi; \
	echo "Downloading submission data..."; \
	CMD="python3 ../download_latest_submission.py --username='$$USERNAME' --password='$$PASSWORD'"; \
	if [ -n "$(SUBMISSION_ID)" ]; then \
		CMD="$$CMD --submission-id='$(SUBMISSION_ID)'"; \
	fi; \
	OUTPUT=$$(eval $$CMD 2>&1); \
	echo "$$OUTPUT"; \
	GREPPED_LINE=$$(echo "$$OUTPUT" | grep "File saved to:"); \
	TARBALL_PATH=$$(echo "$$GREPPED_LINE" | awk '{print $$NF}' | tr -d '\r'); \
	if [ -n "$$TARBALL_PATH" ] && [ -f "$$TARBALL_PATH" ]; then \
		echo "----------------------------------------"; \
		echo "✅ Downloaded file found: $$TARBALL_PATH"; \
		SUBMIT_DIR_PATH="/home/$$USER/aichallenge-2025/aichallenge/workspace/src/aichallenge_submit"; \
		EXTRACT_DIR_PATH="/home/$$USER/aichallenge-2025/aichallenge/workspace/src"; \
		echo "🧹 Deleting existing directory: $$SUBMIT_DIR_PATH"; \
		rm -rf "$$SUBMIT_DIR_PATH"; \
		echo "📦 Extracting archive to: $$SUBMIT_DIR_PATH/"; \
		tar -xzf "$$TARBALL_PATH" -C "$$EXTRACT_DIR_PATH"; \
		rm  "$$TARBALL_PATH"; \
		echo "Extraction completed successfully."; \
		echo "----------------------------------------"; \
	else \
		echo "----------------------------------------"; \
		echo "⚠️ Extraction failed: Could not find a valid file to extract."; \
		echo "----------------------------------------"; \
	fi
	@echo "Process finished."

# autowareのbuildのみ
build:
	docker compose up -d aic-build
	docker compose logs -f aic-build

# ダウンロードからビルド・実行まで全て行う
all:download-only
	docker compose up -d aic-build driver zenoh autoware rosbag
	docker compose logs -f aic-build driver zenoh autoware rosbag
#それぞれのコンテナをstopする
stop-autoware:
	docker compose stop autoware
stop-zenoh:
	docker compose stop zenoh
stop-driver:
	docker compose stop driver
stop-rosbag:
	docker compose stop rosbag
# Stop all services
stop-all:
	docker compose down
