import re
import json
import subprocess
import time
from datetime import datetime, timezone

EXPECTED = [
    "Pi Cycle Top Indicator",
    "RUPL/NUPL Chart",
    "RHODL Ratio",
    "Puell Multiple",
    "2 Year Moving Average",
    "Bitcoin Trolololo Trend Line",
    "MVRV Z-Score",
    "Reserve Risk",
    "Woobull Top Cap vs CVDD",
]

def main():
    proc = subprocess.Popen(
        ["python", "-u", "main.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    )

    # 本地网络一般更快，120 秒足够
    time.sleep(120)

    if proc.poll() is None:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()

    stdout, _ = proc.communicate()

    found = {}
    pattern = re.compile(
        r"^\s*(\d{1,3})\s*%\s*[-–—]\s*(.+?)\s*$",
        re.MULTILINE,
    )

    for line in stdout.splitlines():
        if "[" in line and "it]" in line:
            continue
        m = pattern.match(line)
        if not m:
            continue

        name = m.group(2).strip()
        for exp in EXPECTED:
            if exp.lower() in name.lower():
                found[exp] = float(m.group(1))
                break

    if len(found) != len(EXPECTED):
        missing = [x for x in EXPECTED if x not in found]
        raise RuntimeError(
            f"只解析到 {len(found)} 个指标，缺失：{missing}"
        )

    values = list(found.values())
    score = sum(values) / len(values)

    data = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "score": round(score, 2),
        "indicators": {k: float(v) for k, v in found.items()},
    }

    with open("cbbi.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"✅ CBBI score = {score:.2f}")
    print(json.dumps(data, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
