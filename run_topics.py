"""Run the five assignment topics sequentially; stop at the first failed run."""
import re
import sys
from pathlib import Path

from research import main


def run_all():
    topics = re.findall(r"^\d+\. (.+)$", Path(__file__).with_name("topics.md").read_text(encoding="utf-8"), re.M)
    for index, topic in enumerate(topics, 1):
        print(f"[{index}/{len(topics)}] {topic}", flush=True)
        result = main(topic)
        if result:
            return result
    return 0


if __name__ == "__main__":
    sys.exit(run_all())
