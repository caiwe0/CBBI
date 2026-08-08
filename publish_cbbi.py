import re
import json
import subprocess
import time
import sys
from datetime import datetime, timezone

def main():
    # 用 -u 强制无缓冲，确保输出能实时捕获
    proc = subprocess.Popen(
        [sys.executable, "-u", "main.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1
    )

    # 给足时间（拉数据+打印），适当加长到 120 秒更保险
    time.sleep(120)

    if proc.poll() is None:
        proc.terminate()
        try:
            proc.wait(timeout=15)
        except subprocess.TimeoutExpired:
            proc.kill()

    stdout, stderr = proc.communicate()

    # 把完整输出写一份到文件，方便排查
    with open("cbbi_debug.log", "w", encoding="utf-8") as f:
        f.write("=== STDOUT ===\n")
        f.write(stdout)
        f.write("\n=== STDERR ===\n")
        f.write(stderr)

    output = stdout + "\n" + stderr

    # 打印出来方便在 Action 日志里直接看
    print("===== CBBI RAW OUTPUT =====")
    print(output[-3000:])
    print("============================")

    # 更宽松的正则：允许全角/半角百分号、各种空格、可选小数
    # 匹配示例：
    #   29 % - Pi Cycle Top Indicator
    #   29% - Pi Cycle Top Indicator
    #   29％ - Pi Cycle Top Indicator
    pattern = r"(\d{1,3}(?:\.\d+)?)\s*[%％]\s*[-–—]\s*(.+?)\s*$"

    matches = re.findall(pattern, output, re.MULTILINE | re.IGNORECASE)

    if not matches:
        # 兜底：尝试匹配任何 "数字 百分号 文字" 的行
        pattern2 = r"(\d{1,3})\s*[%％]\s*(.+?)$"
        matches = re.findall(pattern2, output, re.MULTILINE)

    if not matches:
        raise SystemExit(
            "❌ 未解析到 CBBI 指标。\n"
            "请检查 cbbi_debug.log 里的原始输出，确认 main.py 是否真的打印了指标行。"
        )

    indicators = {}
    values = []

    for value, name in matches:
        v = float(value)
        n = re.sub(r"\s+", " ", name).strip()
        # 去重（防止同一指标打印两次）
        if n not in indicators:
            indicators[n] = v
            values.append(v)

    score = sum(values) / len(values)

    data = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "score": round(score, 2),
        "indicators": {k: float(v) for k, v in indicators.items()}
    }

    with open("cbbi.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print("✅ cbbi.json generated:")
    print(json.dumps(data, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
