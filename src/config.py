"""M1 项目路径、字体与运行参数；不依赖本机个人路径。"""

from __future__ import annotations

import hashlib
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def sha256_file(path: Path) -> str:
    """返回文件内容 SHA256，用于输入、字体和素材关联。"""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def project_path(value: str | Path) -> Path:
    """绝对路径保持不变，相对路径按项目根目录解析。"""
    path = Path(value)
    return path.resolve() if path.is_absolute() else (ROOT / path).resolve()


def load_config(outline: dict, overrides: dict | None = None) -> dict:
    """从已校验输入生成运行配置，缺失字体必须明确失败。"""
    overrides = overrides or {}
    fonts = {}
    for key, value in outline["style"]["fonts"].items():
        path = project_path(overrides.get(f"font_{key}", value["path"]))
        if not path.is_file():
            raise ValueError(f"字体文件不存在: {value['path']}")
        fonts[key] = {**value, "resolved_path": path, "sha256": sha256_file(path)}
    default_lo = Path(os.environ.get("ProgramFiles", "C:/Program Files")) / "LibreOffice/program/soffice.com"
    return {
        "fonts": fonts,
        "canvas": outline["canvas"],
        "margin_pt": outline["style"].get("text_margin_pt", 2),
        "soffice": str(overrides.get("soffice") or os.environ.get("M1_SOFFICE") or default_lo),
        "render_timeout_s": 45,
        "geometry_tolerance_pt": 1,
    }
