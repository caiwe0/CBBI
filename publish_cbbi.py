import re
import json
import subprocess
import time
from datetime import datetime, timezone


EXPECTED_INDICATORS = [
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


def normalize_name(name: str) -> str:
    """
    把输出里的指标名归一化，方便和预期列表比对。
    """
    name = name.strip()
    # 有些版本可能写成 Woobull Top Cap vs CVDD / Woobull Top Cap vs CVDD 等
    name = re.sub(r"\s+", " ", name)
    return name


def main():
    proc = subprocess.Popen(
        ["python", "-u", "main.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    )

    # 等足够时间让 main.py 拉数据并打印指标
    time.sleep(120)

    if proc.poll() is None:
        proc.terminate()
        try:
            proc.wait(timeout=15)
        except subprocess.TimeoutExpired:
            proc.kill()

    stdout, stderr = proc.communicate()

    output = stdout + "\n" + stderr

    # 调试原始输出
    with open("cbbi_debug.log", "w", encoding="utf-8") as f:
        f.write("=== STDOUT ===\n")
        f.write(stdout)
        f.write("\n=== STDERR ===\n")
        f.write(stderr)

    print("===== CBBI RAW OUTPUT TAIL =====")
    print(output[-3000:])
    print("================================")

    # 严格匹配：数字% - 已知指标名
    # 例子：29 % - Pi Cycle Top Indicator
    pattern = r"^\s*(\d{1,3}(?:\.\d+)?)\s*[%％]\s*[-–—]\s*(.+?)\s*$"

    found = {}

    for line in output.splitlines():
        m = re.match(pattern, line)
        if not m:
            continue

        value_str, name_raw = m.groups()
        name = normalize_name(name_raw)

        # 只接受预期指标名
        if name in EXPECTED_INDICATORS:
            value = float(value_str)
            # 如果同一指标出现多次，取最后一次或第一次都可以，这里覆盖为最后一次
            found[name] = value

    if len(found) < len(EXPECTED_INDICATORS):
        missing = [x for x in EXPECTED_INDICATORS if x not in found]

        raise SystemExit(
            f"❌ 只解析到 {len(found)}/{len(EXPECTED_INDICATORS)} 个指标。\n"
            f"缺失：{missing}\n"
            f"请检查 cbbi_debug.log 原始输出。"
        )

    values = [found[k] for k in EXPECTED_INDICATORS]
    score = sum(values) / len(values)

    indicators = {k: float(found[k]) for k in EXPECTED_INDICATORS}

    data = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "score": round(score, 2),
        "indicators": indicators,
    }

    with open("cbbi.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print("✅ cbbi.json generated:")
    print(json.dumps(data, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
