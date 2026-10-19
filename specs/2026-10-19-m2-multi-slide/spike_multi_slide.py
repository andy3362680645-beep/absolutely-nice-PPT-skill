"""M2 多页关键路径验证；夹具与证据只写本任务 output。"""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import uuid

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from PIL import Image, ImageDraw
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.util import Pt
import pymupdf

from src.config import load_config, sha256_file
from src.outline import check_assets, load_deck_outline, load_outline
from src.render import _session_fonts
from src.checks import audit_page
from src.text_fit import fit_textframe

M1_INPUT = ROOT / "specs/2026-10-18-m1-single-slide/m1-input.json"


def save_json(path, data):
    """保存本次验证证据。"""
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def probe(run):
    """不依赖未来 M2 实现，先真实验证两页及第二页错文。"""
    config = load_config(load_outline(M1_INPUT))
    Image.new("RGB", (1600, 900), "#FAF8F1").save(run / "background.png")
    icon = Image.new("RGBA", (200, 200))
    ImageDraw.Draw(icon).ellipse((10, 10, 190, 190), fill="#647547")
    icon.save(run / "illustration.png")
    prs = Presentation()
    prs.slide_width, prs.slide_height = Pt(960), Pt(540)
    slide_records = []
    for index in range(2):
        slide = prs.slides.add_slide(prs.slide_layouts[6])
        slide.shapes.add_picture(str(run / "background.png"), 0, 0, Pt(960), Pt(540))
        slide.shapes.add_picture(str(run / "illustration.png"), Pt(730), Pt(240), Pt(140), Pt(140))
        specs = [("title", f"多页技术验证 · 第 {index+1} 页", [40, 40, 860, 70], "bold", 36),
                 ("body", "第一页：验证独立文字与图片。" if index == 0 else "第二页：近 30 款、超 500 万份。", [40, 180, 620, 130], "regular", 24)]
        if index:
            specs.append(("extra", "此行为第二页独有。", [40, 350, 620, 50], "regular", 20))
        records = [{"id": "illustration", "type": "picture", "role": "illustration", "box_pt": [730, 240, 140, 140]}]
        for key, text, box, font_key, cap in specs:
            shape = slide.shapes.add_textbox(*(Pt(v) for v in box))
            shape.name = key
            tf = shape.text_frame
            tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
            font = config["fonts"][font_key]
            size = fit_textframe(shape, text, str(font["resolved_path"]), font["name"], cap_pt=cap, floor_pt=18, bold=font["bold"])
            assert size is not None
            for paragraph in tf.paragraphs:
                for item in paragraph.runs:
                    item.font.color.rgb = RGBColor.from_string("161A15")
            records.append({"id": key, "type": "text", "text": text, "effective_box_pt": box,
                            "font_key": font_key, "font_size_pt": size, "floor_pt": 18})
        slide_records.append({"slide_id": f"probe-{index+1}", "shapes": records})
    pptx = run / "probe.pptx"
    prs.save(pptx)
    reopened = Presentation(pptx)
    assert len(reopened.slides) == 2
    assert [len(s.shapes) for s in reopened.slides] == [4, 5]
    with _session_fonts(config), tempfile.TemporaryDirectory(prefix="m2-probe-") as profile:
        result = subprocess.run([config["soffice"], "-env:UserInstallation=" + Path(profile).as_uri(),
                                 "--headless", "--convert-to", "pdf", "--outdir", str(run), str(pptx)],
                                capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=45)
    assert result.returncode == 0, result.stdout + result.stderr
    fonts = {key: {k: v for k, v in value.items() if k != "resolved_path"} for key, value in config["fonts"].items()}
    audits, hashes = [], []
    with pymupdf.open(run / "probe.pdf") as doc:
        assert len(doc) == 2
        for index, page in enumerate(doc):
            assert abs(page.rect.width - 960) < .1 and abs(page.rect.height - 540) < .1
            audit = audit_page(page, {"slides": [slide_records[index]], "font_records": fonts})
            assert not audit["issues"], audit["issues"]
            audits.append({"slide_index": index+1, "slide_id": slide_records[index]["slide_id"], **audit})
            png = run / f"reference-{index+1:02d}.png"
            page.get_pixmap(matrix=pymupdf.Matrix(2560/960, 2560/960), alpha=False).save(png)
            hashes.append(sha256_file(png))
        wrong = copy.deepcopy(slide_records[1])
        wrong["shapes"][1]["text"] += "故意增加漏文"
        negative = audit_page(doc[1], {"slides": [wrong], "font_records": fonts})
        assert any(x["code"] == "text_mismatch" for x in negative["issues"])
        assert not audits[0]["issues"] and hashes[0] != hashes[1]
    evidence = {"passed": True, "case": "probe", "slides": 2, "shape_counts": [4, 5],
                "pages": audits, "reference_sha256": hashes,
                "second_page_negative": {"slide_index": 2, "slide_id": "probe-2", "deck_passed": False, "issues": negative["issues"]}}
    save_json(run / "result.json", evidence)
    return {"passed": True, "case": "probe", "slides": 2, "shape_counts": [4, 5], "positive_issues": 0, "second_page_negative_detected": True}


def fixture(run):
    """借用已有原创图片，只在隔离目录保存两页输入与来源夹具。"""
    data = json.loads(M1_INPUT.read_text(encoding="utf-8"))
    data.update(schema_version=2, deck_id="m2-multi-slide", title="M2 两页内部验证")
    second = copy.deepcopy(data["slides"][0])
    first = data["slides"][0]
    first.update(layout_type="cover", notes="第一页独立讲稿。", source_ids=[])
    first["texts"] = [t for t in first["texts"] if t["role"] != "source"]
    first["texts"][0]["text"] = "多页技术验证：第一页"
    second.update(slide_id="slide-02", layout_type="columns", notes="第二页独立讲稿。", source_ids=[data["sources"][0]["id"]])
    second["texts"][0]["text"] = "多页技术验证：第二页"
    data["slides"].append(second)
    provenance = run / "source-record.json"
    data["asset_source_record"] = provenance.relative_to(ROOT).as_posix()
    entries = []
    for picture in first["images"]:
        path = ROOT / picture["path"]
        with Image.open(path) as image:
            entries.append({"path": picture["path"], "sha256": sha256_file(path), "origin": "reused-M1-for-test",
                            "tool": "session image_gen", "model": "unknown", "prompt": "沿用M1已有原创素材；原记录 assets/m1-single-slide/source-record.json",
                            "size_px": list(image.size), "transparent_background": picture["require_alpha"]})
    save_json(provenance, {"schema_version": 1, "images": entries})
    path = run / "input.json"
    save_json(path, data)
    return path, load_deck_outline(path)


def schema_case(run):
    """验证页面身份、来源、第二页素材及换行哈希；不执行转换。"""
    path, data = fixture(run)
    assert not check_assets(data)
    raw = json.loads(path.read_text(encoding="utf-8"))
    negatives = {}
    mutations = {
        "duplicate_slide": lambda d: d["slides"][1].update(slide_id="slide-01"),
        "duplicate_shape": lambda d: d["slides"][1]["texts"][1].update(id="title"),
        "unknown_source": lambda d: d["slides"][1].update(source_ids=["missing"]),
        "out_of_bounds": lambda d: d["slides"][1]["texts"][0].update(box_pt=[900, 0, 200, 50]),
        "nan_box": lambda d: d["slides"][1]["texts"][0].update(box_pt=[float("nan"), 0, 200, 50]),
        "missing_alpha_requirement": lambda d: d["slides"][1]["images"][1].update(require_alpha=False),
    }
    for name, mutate in mutations.items():
        bad = copy.deepcopy(raw)
        mutate(bad)
        target = run / (name + ".json")
        save_json(target, bad)
        try:
            load_deck_outline(target)
        except ValueError as exc:
            assert "第 2 页" in str(exc), str(exc)
            negatives[name] = str(exc)
        else:
            raise AssertionError(name)
    bad = copy.deepcopy(raw)
    bad["slides"][1]["images"][1]["path"] = (run / "missing.png").relative_to(ROOT).as_posix()
    target = run / "missing-image.json"
    save_json(target, bad)
    issues = check_assets(load_deck_outline(target))
    assert any("missing_asset" in x and "page=2:slide-02" in x for x in issues), issues
    negatives["second_page_missing_image"] = issues
    bad = copy.deepcopy(raw)
    bad["slides"][1]["images"][1].update(path=bad["slides"][1]["images"][0]["path"])
    save_json(target, bad)
    issues = check_assets(load_deck_outline(target))
    assert any("alpha_missing" in x and "page=2:slide-02" in x for x in issues), issues
    negatives["second_page_opaque_image"] = issues
    lf_hash = data["_input_sha256"]
    path.write_bytes(path.read_bytes().replace(b"\r\n", b"\n").replace(b"\n", b"\r\n"))
    assert load_deck_outline(path)["_input_sha256"] == lf_hash
    for version in (1, 2):
        bad = copy.deepcopy(raw)
        bad["schema_version"] = version
        save_json(target, bad)
        try:
            load_outline(target)
        except ValueError:
            negatives[f"m1_rejects_multi_version_{version}"] = True
        else:
            raise AssertionError("M1 不应接受多页")
    save_json(run / "result.json", {"passed": True, "case": "schema", "negative_cases": negatives, "crlf_compatible": True})
    return {"passed": True, "case": "schema", "negative_cases": len(negatives), "crlf_compatible": True}


def main():
    """只提供已经实现的验证分支；失败以非零退出。"""
    parser = argparse.ArgumentParser(description=__doc__)
    cases = {"probe": probe, "schema": schema_case}
    parser.add_argument("--case", choices=list(cases), required=True)
    args = parser.parse_args()
    run = ROOT / "output/m2-multi-slide/spike" / (args.case + "-" + uuid.uuid4().hex[:10])
    run.mkdir(parents=True)
    result = cases[args.case](run)
    print(json.dumps({**result, "out": run.relative_to(ROOT).as_posix()}, ensure_ascii=False))


if __name__ == "__main__":
    main()
