"""M1 中文适配最小验证；先 probe-old，再验证修复后的边界与混排。"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from PIL import ImageFont
from src import text_fit


def main() -> None:
    """输出可复核 JSON；旧边界探测使用子进程防止挂住当前进程。"""
    parser = argparse.ArgumentParser()
    parser.add_argument("--probe-old", action="store_true")
    parser.add_argument("--worker-narrow", action="store_true")
    args = parser.parse_args()
    font_path = ROOT / "fonts/SourceHanSansSC-Regular.otf"
    font = ImageFont.truetype(str(font_path), 24)
    if args.worker_narrow:
        text_fit.cjk_wrap("茶", font, 0.1)
        return
    if args.probe_old:
        try:
            result = subprocess.run(
                [sys.executable, __file__, "--worker-narrow"],
                capture_output=True, text=True, timeout=2,
            )
        except subprocess.TimeoutExpired:
            print(json.dumps({"old_narrow_box": "timeout_reproduced", "timeout_s": 2}))
            return
        raise AssertionError(f"旧循环未复现，exit={result.returncode}: {result.stderr}")

    cases = [
        ("chinese", "用户共创，让灵感成为日常。", 180),
        ("mixed", "喜茶 GO 2025 年，超 100 万份。", 180),
        ("explicit_newline", "喜贴回归\n百万共创", 180),
        ("long_western", "https://example.com/" + "a" * 100, 100),
        ("punctuation", "共创（灵感）与日常，带来温暖。", 100),
        ("punctuation_boundary", "一二三四。", 96),
    ]
    results = []
    for label, content, width in cases:
        lines = text_fit.cjk_wrap(content, font, width)
        assert "".join("".join(lines).split()) == "".join(content.split()), label
        assert all(text_fit.text_width_px(font, line) <= width + 0.01 for line in lines), label
        if label == "punctuation_boundary":
            assert all(not line or line[0] not in text_fit.NO_LINE_START for line in lines), lines
        results.append({"case": label, "lines": len(lines), "passed": True})
    for width in (0, -1, 0.1):
        try:
            text_fit.cjk_wrap("茶", font, width)
        except ValueError:
            results.append({"case": f"invalid_width_{width}", "passed": True})
        else:
            raise AssertionError(f"不可容纳单字的宽度未失败: {width}")
    assert text_fit.best_font_size("茶", str(font_path), 15, 30, 24, 10) is not None
    assert text_fit.best_font_size("茶" * 200, str(font_path), 20, 10) is None
    assert text_fit.best_font_size("茶", str(font_path), 0, 20) is None
    assert text_fit.best_font_size("茶", str(font_path), 20, 0) is None
    print(json.dumps({"passed": True, "wrap_cases": results, "size_cases": 4}, ensure_ascii=False))


if __name__ == "__main__":
    main()
