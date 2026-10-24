"""M1 可编辑对象、PDF 字符、字体和几何核对；不替代视觉验收。"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import re

import pymupdf

from .builder import normalized, verify_reopened
from .config import sha256_file


def _rect(box: list) -> pymupdf.Rect:
    x, y, w, h = box
    return pymupdf.Rect(x, y, x + w, y + h)


def _font_key(name: str) -> str:
    return re.sub(r"[^a-z0-9]", "", name.split("+")[-1].lower())


def audit_page(page, manifest: dict, tolerance: float = 1) -> dict:
    """保留 M1 的单页清单调用方式。"""
    return audit_slide(page, manifest["slides"][0], manifest["font_records"], tolerance)


def audit_slide(page, slide_record: dict, font_records: dict, tolerance: float = 1) -> dict:
    """按有效文字区分配实际字符，报告漏文、歧义、字体替换和几何问题。"""
    pymupdf.TOOLS.set_small_glyph_heights(True)
    issues = []
    shapes = slide_record["shapes"]
    texts = [shape for shape in shapes if shape["type"] == "text"]
    rectangles = [_rect(shape["effective_box_pt"]) for shape in texts]
    for i, rect in enumerate(rectangles):
        if not page.rect.contains(rect):
            issues.append({"code": "textbox_out_of_page", "shape": texts[i]["id"]})
        for j, other in enumerate(rectangles[i+1:], start=i+1):
            if (rect & other).get_area() > 0.01:
                issues.append({"code": "text_collision", "shapes": [texts[i]["id"], texts[j]["id"]]})
        for picture in shapes:
            if picture["type"] != "picture" or picture["role"] == "background":
                continue
            subject = _rect(picture.get("subject_safe_box_pt", picture["box_pt"]))
            if (rect & subject).get_area() > 0.01:
                issues.append({"code": "text_picture_collision", "shapes": [texts[i]["id"], picture["id"]]})
    assigned = [[] for _ in texts]
    observed = [set() for _ in texts]
    for block in page.get_text("rawdict")["blocks"]:
        for line in block.get("lines", []):
            for span in line["spans"]:
                for char in span["chars"]:
                    if not char["c"].strip():
                        continue
                    box = pymupdf.Rect(char["bbox"])
                    center = (box.tl + box.br) / 2
                    owners = [i for i, rect in enumerate(rectangles) if center in rect]
                    if len(owners) != 1:
                        issues.append({"code": "unassigned_or_ambiguous_character", "character": char["c"], "bbox": list(box)})
                        continue
                    owner = owners[0]
                    record = texts[owner]
                    assigned[owner].append(char["c"])
                    observed[owner].add(round(span["size"], 3))
                    if not (rectangles[owner] + (-tolerance, -tolerance, tolerance, tolerance)).contains(box):
                        issues.append({"code": "text_overflow", "shape": record["id"], "bbox": list(box)})
                    if not page.rect.contains(box):
                        issues.append({"code": "glyph_out_of_page", "shape": record["id"]})
                    if span["size"] < record["floor_pt"] - 0.1 or abs(span["size"] - record["font_size_pt"]) > 0.3:
                        issues.append({"code": "font_size_mismatch", "shape": record["id"], "observed": span["size"]})
                    font = font_records[record["font_key"]]
                    if _font_key(span["font"]) != _font_key(Path(font["path"]).stem):
                        issues.append({"code": "font_substitution", "shape": record["id"], "observed": span["font"]})
    results = []
    for record, actual, sizes in zip(texts, assigned, observed):
        text = "".join(actual)
        matched = normalized(text) == normalized(record["text"])
        if not matched:
            issues.append({"code": "text_mismatch", "shape": record["id"], "expected": record["text"], "observed": text})
        results.append({"id": record["id"], "text_matches": matched, "observed_text": text, "observed_sizes_pt": sorted(sizes)})
    unique = {repr(issue): issue for issue in issues}
    return {"issues": list(unique.values()), "texts": results, "pdf_fonts": [row[3] for row in page.get_fonts()]}


def check_v1(pptx_path: Path, pdf_path: Path, manifest: dict, config: dict) -> dict:
    """核对真实对象与 PDF，返回含证据哈希的结构化结果。"""
    issues = [{"code": item} for item in verify_reopened(pptx_path, manifest)]
    for key, font in config["fonts"].items():
        if manifest["font_records"][key]["sha256"] != font["sha256"]:
            issues.append({"code": "font_source_changed", "font": key})
    with pymupdf.open(pdf_path) as doc:
        if len(doc) != 1:
            return {"passed": False, "issues": issues + [{"code": "pdf_page_count"}]}
        page = doc[0]
        if abs(page.rect.width - config["canvas"]["width_pt"]) > 0.1 or abs(page.rect.height - config["canvas"]["height_pt"]) > 0.1:
            issues.append({"code": "pdf_canvas_mismatch"})
        audit = audit_page(page, manifest, config["geometry_tolerance_pt"])
        issues.extend(audit["issues"])
    return {
        "passed": not issues, "issues": issues, "slides": 1,
        "shapes": len(manifest["slides"][0]["shapes"]), "texts": audit["texts"], "pdf_fonts": audit["pdf_fonts"],
        "input_sha256": manifest["input_sha256"], "pptx_sha256": sha256_file(pptx_path), "pdf_sha256": sha256_file(pdf_path),
        "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        "visual_review": "pending", "v1_confirmation": "pending",
    }


def check_deck_v1(pptx_path: Path, pdf_path: Path, manifest: dict, config: dict) -> dict:
    """核对每一页及整套一致性；缺页也返回结构完整的失败报告。"""
    records = manifest["slides"]
    issues, pages = [], []
    for detail in verify_reopened(pptx_path, manifest):
        issue = {"code": "pptx_object_mismatch", "detail": detail}
        if detail.startswith("page="):
            index = int(detail.partition(":")[0][5:])
            issue.update(slide_index=index, slide_id=records[index-1]["slide_id"])
        issues.append(issue)
    for key, font in config["fonts"].items():
        if manifest["font_records"].get(key, {}).get("sha256") != font["sha256"]:
            issues.append({"code": "font_source_changed", "font": key})
    with pymupdf.open(pdf_path) as doc:
        if len(doc) != len(records):
            issues.append({"code": "pdf_page_count", "expected": len(records), "observed": len(doc)})
        for index, record in enumerate(records, 1):
            identity = {"slide_index": index, "slide_id": record["slide_id"]}
            page_issues = [item for item in issues if item.get("slide_index") == index]
            if index > len(doc):
                audit = {"texts": [], "pdf_fonts": []}
                page_issues.append({"code": "pdf_page_missing", **identity})
            else:
                page = doc[index-1]
                if abs(page.rect.width-config["canvas"]["width_pt"]) > .1 or abs(page.rect.height-config["canvas"]["height_pt"]) > .1:
                    page_issues.append({"code": "pdf_canvas_mismatch", **identity})
                audit = audit_slide(page, record, manifest["font_records"], config["geometry_tolerance_pt"])
                page_issues.extend({**item, **identity} for item in audit["issues"])
            issues.extend(item for item in page_issues if item not in issues)
            pages.append({**identity, "passed": not page_issues, "shapes": len(record["shapes"]),
                          "issues": page_issues, "texts": audit["texts"], "pdf_fonts": audit["pdf_fonts"]})
    return {"passed": not issues, "issues": issues, "slide_count": len(records), "slides": pages,
            "shapes": sum(len(page["shapes"]) for page in records),
            "input_sha256": manifest["input_sha256"], "pptx_sha256": sha256_file(pptx_path),
            "pdf_sha256": sha256_file(pdf_path), "checked_at_utc": datetime.now(timezone.utc).isoformat(),
            "visual_review": "pending", "v1_confirmation": "pending"}
