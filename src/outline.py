"""M1 单页 JSON 输入与素材校验；保留原始文案和输入哈希。"""

from __future__ import annotations

import json
import hashlib
import math
from pathlib import Path
import re

from PIL import Image

from .config import ROOT, project_path, sha256_file


def _number(value) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _valid_box(box, width: float, height: float) -> bool:
    if not isinstance(box, list) or len(box) != 4 or not all(_number(v) for v in box):
        return False
    x, y, w, h = box
    return x >= 0 and y >= 0 and w > 0 and h > 0 and x + w <= width and y + h <= height


def load_outline(input_path: str | Path) -> dict:
    """保留 M1 schema 1 单页读取契约。"""
    return _load_outline(input_path, 1)


def load_deck_outline(input_path: str | Path) -> dict:
    """读取 schema 2 多页输入；不要求未生成素材已存在。"""
    return _load_outline(input_path, 2)


def _load_outline(input_path: str | Path, version: int) -> dict:
    """共用字段与逐页校验，版本入口保持隔离。"""
    path = project_path(input_path)
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(data, dict) or type(data.get("schema_version")) is not int or data["schema_version"] != version:
        raise ValueError(f"仅支持 schema_version={version}")
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
    if not isinstance(slides, list) or not slides or any(not isinstance(slide, dict) for slide in slides):
        raise ValueError("slides 必须为非空页面列表")
    if version == 1 and len(slides) != 1:
        raise ValueError("M1 必须且只能包含 1 页")
    sources = data.get("sources")
    if not isinstance(sources, list) or (version == 1 and not sources):
        raise ValueError("缺少资料来源")
    for source in sources:
        if not isinstance(source, dict) or not all(isinstance(source.get(key), str) and source[key].strip() for key in ("publisher", "date", "url")):
            raise ValueError("来源必须包含发布机构、日期与 URL")
        if not source["url"].startswith(("https://", "http://")):
            raise ValueError("来源 URL 必须为 HTTP(S) 链接")
    source_ids = set()
    if version == 2:
        record = data.get("asset_source_record")
        if not isinstance(record, str) or not record.strip() or Path(record).is_absolute() or not project_path(record).is_relative_to(ROOT):
            raise ValueError("asset_source_record 必须为项目内相对路径")
        for source in sources:
            key = source.get("id")
            if not isinstance(key, str) or not key.strip() or key in source_ids:
                raise ValueError("资料来源 id 必须非空且唯一")
            source_ids.add(key)
    page_ids = set()
    for index, slide in enumerate(slides, 1):
        try:
            _validate_slide(slide, fonts, margin, width, height)
            if version == 1:
                if not any(text["role"] == "source" for text in slide["texts"]):
                    raise ValueError("缺少资料来源或页脚")
            else:
                if slide["slide_id"] in page_ids:
                    raise ValueError("重复 slide_id")
                page_ids.add(slide["slide_id"])
                if slide.get("layout_type") not in {"cover", "columns", "image-text", "data", "closing"}:
                    raise ValueError("layout_type 无效")
                if not isinstance(slide.get("notes"), str):
                    raise ValueError("notes 必须为字符串")
                refs = slide.get("source_ids")
                if not isinstance(refs, list) or any(not isinstance(key, str) or key not in source_ids for key in refs) or len(set(refs)) != len(refs):
                    raise ValueError("source_ids 无效、重复或资料不存在")
                if refs and not any(text["role"] == "source" for text in slide["texts"]):
                    raise ValueError("引用资料的页面缺少来源文本")
                if sum(text["role"] == "title" for text in slide["texts"]) != 1:
                    raise ValueError("每页必须恰有一个标题")
        except ValueError as exc:
            if version == 1:
                raise
            raise ValueError(f"第 {index} 页 [{slide.get('slide_id', '?')}]: {exc}") from exc
    data["_input_path"] = path
    data["_input_sha256"] = hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()
    return data


def _validate_slide(slide, fonts, margin, width, height):
    """对单页的全部形状与准确文案执行既有校验。"""
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
        text_margin = text.get("margin_pt", margin)
        if not _number(text_margin) or text_margin < 0 or min(text["box_pt"][2:]) <= text_margin * 2:
            raise ValueError(f"文字有效区域为空: {text['id']}")
        if not isinstance(text.get("color"), str) or not re.fullmatch(r"[0-9A-Fa-f]{6}", text["color"]):
            raise ValueError(f"文字颜色无效: {text['id']}")
        if "fill_color" in text and (not isinstance(text["fill_color"], str) or not re.fullmatch(r"[0-9A-Fa-f]{6}", text["fill_color"])):
            raise ValueError(f"文字底色无效: {text['id']}")
        if not isinstance(text.get("align", "left"), str) or text.get("align", "left") not in {"left", "center", "right"}:
            raise ValueError(f"文字对齐无效: {text['id']}")
    groups = slide.get("content_groups", {})
    if not isinstance(groups, dict):
        raise ValueError("content_groups 必须为对象")
    text_by_id = {text["id"]: text for text in texts}
    grouped_ids = set()
    for group_id, group in groups.items():
        if not isinstance(group_id, str) or not group_id or not isinstance(group, dict) or not isinstance(group.get("text"), str) or not group["text"].strip():
            raise ValueError("完整句逻辑组无效")
        members = group.get("shape_ids")
        if not isinstance(members, list) or not members or any(not isinstance(key, str) or key not in text_by_id or key in grouped_ids for key in members) or len(set(members)) != len(members):
            raise ValueError(f"逻辑组成员无效: {group_id}")
        combined = "".join(text_by_id[key]["text"] for key in members)
        if re.sub(r"\s+", "", combined) != re.sub(r"\s+", "", group["text"]):
            raise ValueError(f"逻辑组与完整确认句不一致: {group_id}")
        grouped_ids.update(members)
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


def check_assets(outline: dict) -> list[str]:
    """检查真实图片存在性、宽高比和 alpha；返回所有可定位问题。"""
    issues = []
    for index, slide in enumerate(outline["slides"], 1):
        first_issue = len(issues)
        for picture in slide["images"]:
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
        if outline.get("schema_version") == 2:
            for position in range(first_issue, len(issues)):
                issues[position] += f":page={index}:{slide['slide_id']}"
    if outline.get("schema_version") == 2:
        return issues + check_asset_sources(outline)
    return issues



def check_asset_sources(outline: dict) -> list[str]:
    """核对每张实际图片对应的来源条目和哈希，不代替授权/审美判断。"""
    issues = []
    try:
        path = project_path(outline["asset_source_record"])
        record = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(record, dict) or record.get("schema_version") != 1 or not isinstance(record.get("images"), list):
            return ["asset_source_record_invalid"]
        entries = {}
        for entry in record["images"]:
            if not isinstance(entry, dict) or not isinstance(entry.get("path"), str):
                return ["asset_source_entry_invalid"]
            key = project_path(entry["path"])
            if key in entries:
                return ["asset_source_entry_duplicate:" + entry["path"]]
            if any(not isinstance(entry.get(field), str) or not entry[field].strip()
                   for field in ("sha256", "origin", "tool", "model", "prompt")):
                return ["asset_source_metadata_invalid:" + entry["path"]]
            entries[key] = entry
        for index, slide in enumerate(outline["slides"], 1):
            for picture in slide["images"]:
                key = project_path(picture["path"])
                label = f"{index}:{slide['slide_id']}:{picture['id']}"
                entry = entries.get(key)
                if not entry:
                    issues.append("asset_source_missing:" + label)
                elif not key.is_file() or sha256_file(key) != entry["sha256"]:
                    issues.append("asset_source_hash:" + label)
                else:
                    with Image.open(key) as image:
                        if entry.get("size_px") != list(image.size) or entry.get("transparent_background") is not picture["require_alpha"]:
                            issues.append("asset_source_image_metadata:" + label)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        issues.append("asset_source_record_unreadable:" + str(exc))
    return issues
