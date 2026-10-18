"""M1 单页 JSON 输入与素材校验；保留原始文案和输入哈希。"""

from __future__ import annotations

import json
import math
from pathlib import Path
import re

from PIL import Image

from .config import project_path, sha256_file


def _number(value) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _valid_box(box, width: float, height: float) -> bool:
    if not isinstance(box, list) or len(box) != 4 or not all(_number(v) for v in box):
        return False
    x, y, w, h = box
    return x >= 0 and y >= 0 and w > 0 and h > 0 and x + w <= width and y + h <= height


def load_outline(input_path: str | Path) -> dict:
    """读取并验证 schema v1 单页结构；素材存在性由 check_assets 单独检查。"""
    path = project_path(input_path)
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(data, dict) or type(data.get("schema_version")) is not int or data["schema_version"] != 1:
        raise ValueError("仅支持 schema_version=1")
    if not isinstance(data.get("title"), str) or not data["title"].strip():
        raise ValueError("缺少有效演示标题")
    if not isinstance(data.get("deck_id"), str) or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", data["deck_id"]):
        raise ValueError("deck_id 必须为英文小写连字符标识")
    canvas = data.get("canvas", {})
    if not isinstance(canvas, dict):
        raise ValueError("canvas 必须为对象")
    width, height = canvas.get("width_pt"), canvas.get("height_pt")
    if not all(_number(v) and v > 0 for v in (width, height)) or abs(width / height - 16 / 9) > 1e-6:
        raise ValueError("M1 画布必须为有效的 16:9")
    reference_width = canvas.get("reference_width_px")
    if not isinstance(reference_width, int) or not 640 <= reference_width <= 4096:
        raise ValueError("参考图宽度必须为 640～4096 的整数")
    style = data.get("style", {})
    if not isinstance(style, dict):
        raise ValueError("style 必须为对象")
    fonts = style.get("fonts")
    if not isinstance(fonts, dict) or not fonts:
        raise ValueError("缺少字体配置")
    for key, font in fonts.items():
        if not isinstance(font, dict) or not all(isinstance(font.get(f), str) and font[f] for f in ("path", "name")):
            raise ValueError(f"字体配置无效: {key}")
        if not isinstance(font.get("bold"), bool):
            raise ValueError(f"字体字重无效: {key}")
    margin = style.get("text_margin_pt", 2)
    if not _number(margin) or margin < 0:
        raise ValueError("文字边距无效")
    slides = data.get("slides")
    if not isinstance(slides, list) or len(slides) != 1 or not isinstance(slides[0], dict):
        raise ValueError("M1 必须且只能包含 1 页")
    slide = slides[0]
    if not isinstance(slide.get("slide_id"), str) or not slide["slide_id"]:
        raise ValueError("缺少 slide_id")
    texts, images = slide.get("texts"), slide.get("images")
    if not isinstance(texts, list) or not texts or not isinstance(images, list):
        raise ValueError("texts 必须非空，images 必须为列表")
    identifiers = set()
    for shape in texts + images:
        if not isinstance(shape, dict) or not isinstance(shape.get("id"), str) or not shape["id"] or shape["id"] in identifiers:
            raise ValueError("形状 id 必须非空且唯一")
        identifiers.add(shape["id"])
        if not _valid_box(shape.get("box_pt"), width, height):
            raise ValueError(f"形状越界或尺寸无效: {shape['id']}")
    for text in texts:
        if not isinstance(text.get("text"), str) or not text["text"].strip():
            raise ValueError(f"文字不能为空: {text['id']}")
        if text.get("role") not in {"title", "subtitle", "heading", "body", "source"}:
            raise ValueError(f"不支持的文字层角色: {text['id']}")
        if text.get("font_key") not in fonts:
            raise ValueError(f"未知字体: {text['id']}")
        cap, floor = text.get("cap_pt"), text.get("floor_pt")
        if not all(isinstance(v, int) and not isinstance(v, bool) for v in (cap, floor)) or not 10 <= floor <= cap <= 120:
            raise ValueError(f"字号范围无效: {text['id']}")
        if min(text["box_pt"][2:]) <= margin * 2:
            raise ValueError(f"文字有效区域为空: {text['id']}")
        if not isinstance(text.get("color"), str) or not re.fullmatch(r"[0-9A-Fa-f]{6}", text["color"]):
            raise ValueError(f"文字颜色无效: {text['id']}")
    for picture in images:
        if picture.get("role") not in {"background", "illustration"} or not isinstance(picture.get("path"), str) or not picture["path"]:
            raise ValueError(f"图片配置无效: {picture['id']}")
        if not isinstance(picture.get("require_alpha"), bool):
            raise ValueError(f"图片透明要求无效: {picture['id']}")
        if picture["role"] == "illustration" and not picture["require_alpha"]:
            raise ValueError(f"独立插画必须要求真实透明通道: {picture['id']}")
        safe = picture.get("subject_safe_box_pt")
        if safe is not None:
            if not _valid_box(safe, width, height):
                raise ValueError(f"主体安全区无效: {picture['id']}")
            x, y, w, h = picture["box_pt"]
            sx, sy, sw, sh = safe
            if sx < x or sy < y or sx + sw > x + w or sy + sh > y + h:
                raise ValueError(f"主体安全区超出图片框: {picture['id']}")
    if sum(picture["role"] == "background" for picture in images) != 1:
        raise ValueError("必须有一张独立背景")
    sources = data.get("sources")
    if not isinstance(sources, list) or not sources or not any(text["role"] == "source" for text in texts):
        raise ValueError("缺少资料来源或页脚")
    for source in sources:
        if not isinstance(source, dict) or not all(isinstance(source.get(key), str) and source[key].strip() for key in ("publisher", "date", "url")):
            raise ValueError("来源必须包含发布机构、日期与 URL")
        if not source["url"].startswith(("https://", "http://")):
            raise ValueError("来源 URL 必须为 HTTP(S) 链接")
    data["_input_path"] = path
    data["_input_sha256"] = sha256_file(path)
    return data


def check_assets(outline: dict) -> list[str]:
    """检查真实图片存在性、宽高比和 alpha；返回所有可定位问题。"""
    issues = []
    for picture in outline["slides"][0]["images"]:
        path = project_path(picture["path"])
        if not path.is_file():
            issues.append(f"missing_asset:{picture['id']}:{picture['path']}")
            continue
        try:
            with Image.open(path) as image:
                image.load()
                if picture["role"] == "background" and abs((image.width / image.height) / (16 / 9) - 1) > 0.005:
                    issues.append(f"background_aspect_ratio:{picture['id']}")
                if picture["require_alpha"]:
                    if "A" not in image.getbands():
                        issues.append(f"alpha_missing:{picture['id']}")
                    else:
                        low, high = image.getchannel("A").getextrema()
                        if low >= 255 or high == 0:
                            issues.append(f"alpha_not_cutout:{picture['id']}")
        except OSError:
            issues.append(f"unreadable_asset:{picture['id']}")
    return issues
