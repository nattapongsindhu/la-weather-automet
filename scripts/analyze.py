"""
analyze.py
Reads temp, wind from env → classifies status, trend, anomaly, score
Writes results back to GITHUB_ENV
"""
import os, sys


def classify_status(temp: float) -> str:
    if temp > 30:
        return "HOT"
    elif temp > 20:
        return "WARM"
    elif temp < 5:
        return "COLD"
    return "OK"


def detect_trend(temp: float, csv_path: str = "temp.csv", threshold: float = 1.5) -> str:
    try:
        with open(csv_path) as f:
            lines = [l for l in f.read().strip().splitlines() if "," in l]
        data_lines = [l for l in lines if not l.startswith("timestamp")]
        if data_lines:
            last_temp = float(data_lines[-1].split(",")[1])
            diff = temp - last_temp
            if diff > threshold:
                return "Rising"
            elif diff < -threshold:
                return "Falling"
    except Exception:
        pass
    return "Stable"


def detect_anomaly(temp: float, csv_path: str = "temp.csv",
                   min_readings: int = 10, sd_threshold: float = 0.5,
                   sigma: float = 2.0) -> str:
    try:
        with open(csv_path) as f:
            lines = [l for l in f.read().strip().splitlines() if "," in l]
        data_lines = [l for l in lines if not l.startswith("timestamp")]
        recent = []
        for l in data_lines[-28:]:
            try:
                recent.append(float(l.split(",")[1]))
            except Exception:
                pass
        if len(recent) >= min_readings:
            avg = sum(recent) / len(recent)
            sd  = (sum((x - avg) ** 2 for x in recent) / len(recent)) ** 0.5
            if sd > sd_threshold and abs(temp - avg) > sigma * sd:
                return "ANOMALY"
    except Exception:
        pass
    return ""


def heat_index_score(temp: float, wind: float) -> int:
    return min(100, max(0, int(temp * 2 + wind * 0.5)))


def main():
    try:
        temp = float(os.environ["TEMP"])
        wind = float(os.environ["WIND"])
    except (KeyError, ValueError) as e:
        print(f"ERROR: missing env var — {e}", file=sys.stderr)
        sys.exit(1)

    status  = classify_status(temp)
    trend   = detect_trend(temp)
    anomaly = detect_anomaly(temp)
    score   = heat_index_score(temp, wind)

    print(f"status={status} trend={trend} anomaly='{anomaly}' score={score}")

    github_env = os.environ.get("GITHUB_ENV", "")
    if github_env:
        with open(github_env, "a") as f:
            f.write(f"STATUS={status}\n")
            f.write(f"TREND={trend}\n")
            f.write(f"SCORE={score}\n")
            f.write(f"ANOMALY={anomaly}\n")
    else:
        # local run — just print
        print(f"STATUS={status}\nTREND={trend}\nSCORE={score}\nANOMALY={anomaly}")


if __name__ == "__main__":
    main()
