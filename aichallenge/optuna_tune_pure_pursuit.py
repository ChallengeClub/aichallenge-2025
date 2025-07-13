import optuna
import subprocess
import json
import os
import pandas as pd
from datetime import datetime

N_TRIALS = 20  # 試行回数（必要に応じて変更）

def objective(trial):
    lookahead_gain = trial.suggest_float("lookahead_gain", 0.05, 0.5)
    lookahead_min = trial.suggest_float("lookahead_min", 0.5, 5.0)
    speed_gain = trial.suggest_float("speed_gain", 0.1, 2.0)

    # 現在のパラメータを出力
    print(f"Trying: lookahead_gain={lookahead_gain:.3f}, lookahead_min={lookahead_min:.3f}, speed_gain={speed_gain:.3f}")

    result = subprocess.run(
        ["python3", "evaluate_wrapper.py", str(lookahead_gain), str(lookahead_min), str(speed_gain)],
        capture_output=True,
        text=True
    )

    try:
        score = float(result.stdout.strip())
        print(f"→ Score: {score:.3f}")
        return score
    except Exception as e:
        print("Failed to parse score:", e)
        return float("inf")


def main():
    print(f"🔧 Starting Optuna optimization: {N_TRIALS} trials")
    study = optuna.create_study(direction="minimize")
    study.optimize(objective, n_trials=N_TRIALS)

    print("\n✅ Best parameters found:")
    print(study.best_params)

    # ログ保存
    log_dir = "optuna_logs"
    os.makedirs(log_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    df = study.trials_dataframe()
    csv_path = os.path.join(log_dir, f"tuning_result_{timestamp}.csv")
    df.to_csv(csv_path, index=False)
    print(f"📄 Trial log saved to: {csv_path}")


if __name__ == "__main__":
    main()
