import re
import json
import subprocess
from datetime import datetime, timezone

def main():
    result = subprocess.run(
        ["python", "main.py"],
        capture_output=True,
        text=True
    )

    output = result.stdout + "\n" + result.stderr

    # 匹配类似：29 % - Pi Cycle Top Indicator
    matches = re.findall(r"^\s*(\d+)\s*%\s*-\s*(.+?)\s*$", output, re.MULTILINE)

    if not matches:
        raise SystemExit("没有解析到 CBBI 指标百分比，请检查 main.py 输出格式")

    indicators = {}
    values = []

    for v, name in matches:
        v = int(v)
        name = name.strip()
        indicators[name] = v
        values.append(v)

    score = sum(values) / len(values)

    data = {
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "score": round(score, 2),
        "indicators": indicators
    }

    with open("cbbi.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print("生成 cbbi.json 成功:")
    print(json.dumps(data, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
