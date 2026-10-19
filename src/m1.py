"""M1 本地执行入口；生图由会话工具接续，不虚构独立 API。"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone

from pathlib import Path

from .config import load_config, project_path, sha256_file
from .outline import check_assets, load_outline


def current_run(out_root: Path, outline: dict) -> tuple[dict, Path, dict]:
    """只读取当前输入对应且对象未变更的运行版本，拒绝越界目录和旧产物。"""
    state = json.loads((out_root / "latest.json").read_text(encoding="utf-8"))
    run_dir = (out_root / state["run_dir"]).resolve()
    if not run_dir.is_relative_to((out_root / "runs").resolve()) or run_dir.name != state["run_id"]:
        raise ValueError("无效运行目录")
    manifest_path = run_dir / "manifest.json"
    if state["input_sha256"] != outline["_input_sha256"]:
        raise ValueError("输入已改变，请重新 build；不能使用旧版本")
    if sha256_file(manifest_path) != state["manifest_sha256"]:
        raise ValueError("manifest 已改变，请重新 build")
    if Path(state["pptx_file"]).name != state["pptx_file"]:
        raise ValueError("无效 PPT 路径")
    if sha256_file(run_dir / state["pptx_file"]) != state["pptx_sha256"]:
        raise ValueError("v1 已改变；本次尚无自动 diff，请同步输入再 build")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest["input_sha256"] != outline["_input_sha256"]:
        raise ValueError("manifest 与当前输入不一致")
    return state, run_dir, manifest


def _verified_artifact(base: Path, relative: str, digest: str) -> Path:
    """只读取指定证据目录内、内容哈希一致的现有文件。"""
    path = (base / relative).resolve()
    if not path.is_relative_to(base.resolve()) or not path.is_file() or sha256_file(path) != digest:
        raise ValueError(f"产物证据缺失或已改变: {Path(relative).name}")
    return path


def prepare_image(outline: dict, config: dict, out_root: Path, confirmed: bool) -> dict:
    """记录已取得的人类确认，核对证据后输出会话生图交接包。"""
    from .builder import verify_reopened, write_json
    if not confirmed:
        raise ValueError("须先取得用户对当前 v1 的确认，再传 --v1-confirmed")
    state, run_dir, manifest = current_run(out_root, outline)
    if state["state"] not in {"awaiting_v1_confirmation", "ready_for_image_generation", "image_generated", "awaiting_visual_acceptance", "accepted"}:
        raise ValueError("当前运行尚未通过 v1 检查")
    report_path = run_dir / "checks.json"
    if sha256_file(report_path) != state.get("checks_sha256"):
        raise ValueError("检测报告已改变，请重新 check")
    report = json.loads(report_path.read_text(encoding="utf-8"))
    if report.get("passed") is not True or report.get("issues") != [] or report.get("input_sha256") != state["input_sha256"] or report.get("pptx_sha256") != state["pptx_sha256"]:
        raise ValueError("检测报告未通过或不属于当前 v1")
    render = state["render"]
    for field, hash_field in (("pdf", "pdf_sha256"), ("reference_png", "reference_sha256")):
        path = (run_dir / render[field]).resolve()
        if not path.is_relative_to(run_dir.resolve()) or sha256_file(path) != render[hash_field]:
            raise ValueError("辅助导出已改变，请重新 check")
    if report["pdf_sha256"] != render["pdf_sha256"]:
        raise ValueError("检测报告对应的 PDF 与参考导出不一致")
    issues = check_assets(outline) + verify_reopened(run_dir / state["pptx_file"], manifest)
    if issues or any(font["sha256"] != manifest["font_records"][key]["sha256"] for key, font in config["fonts"].items()):
        raise ValueError("素材、字体或对象已改变，请重新 build/check")
    if state["state"] in {"image_generated", "awaiting_visual_acceptance", "accepted"}:
        try:
            handoff = _verified_artifact(out_root, state["image_input"], state["image_input_sha256"])
            package = json.loads(handoff.read_text(encoding="utf-8"))
            if any(package[key] != state[key] for key in ("run_id", "input_sha256", "pptx_sha256", "checks_sha256")):
                raise ValueError("生图交接与当前运行不一致")
            prompt_path = _verified_artifact(handoff.parent, "redraw-prompt.txt", package["prompt_sha256"])
            _verified_artifact(handoff.parent, "exact-text.json", package["exact_text_sha256"])
            final = state["final_image"]
            _verified_artifact(run_dir, final["file"], final["sha256"])
            review_path = _verified_artifact(run_dir, final["review_file"], final["review_sha256"])
            review = json.loads(review_path.read_text(encoding="utf-8"))
            if review["image_sha256"] != final["sha256"] or review["handoff_sha256"] != state["image_input_sha256"] or review["input_sha256"] != state["input_sha256"] or review["pptx_sha256"] != state["pptx_sha256"] or review["prompt_sha256"] != package["prompt_sha256"]:
                raise ValueError("最终图核对记录与输入不一致")
            submitted = _verified_artifact(run_dir, review["submitted_prompt_file"], review["submitted_prompt_sha256"])
            if submitted.read_text(encoding="utf-8") != prompt_path.read_text(encoding="utf-8").strip():
                raise ValueError("实际生图提示词与交接不一致")
            if state["state"] == "accepted" and (final.get("human_accepted") is not True or final.get("content_reviewed") is not True or review.get("content_review") != "passed" or review.get("human_visual_acceptance") != "passed" or review["human_acceptance"]["image_sha256"] != final["sha256"]):
                raise ValueError("缺少与当前图像绑定的验收记录")
        except (OSError, ValueError, KeyError, TypeError) as exc:
            state.update(state="failed", evidence_error=str(exc))
            state.get("final_image", {})["human_accepted"] = False
            write_json(out_root / "latest.json", state)
            raise ValueError("生图或验收证据无效，不能沿用旧状态；请恢复证据或重新检查后重绘") from exc
        return {"passed": True, "state": state["state"], "v1_confirmed": True, "texts": len(outline["slides"][0]["texts"]), "handoff": str(handoff), "prompt": str(prompt_path), "reused": True}
    exact = [{"id": text["id"], "role": text["role"], "text": text["text"]} for text in outline["slides"][0]["texts"]]
    prompt = (
        "Use case: productivity-visual; style-transfer / compositing.\n"
        "Asset type: single finished 16:9 presentation slide, opaque background.\n"
        "将参考图1的可编辑 PPT 页面重新设计并完整绘制为高级、协调的商业品牌年度汇报页。"
        "图1是已确认的内容、层级和阅读顺序参考，不要逐像素复制普通 PPT 的僵硬排版。"
        "图2为无字背景风格参考，图3为原创茶饮插画素材参考。\n"
        "保留暖白纸感、墨色、克制茶绿与茶叶元素；充分留白，精致中文无衬线字形。"
        "优化字体大小、字重、对齐、节奏及三组内容的图文关系。"
        "将生硬矩形数据框处理得更精致自然，可使用轻盈纸片质感与细腻笔触，数字醒目且内文清晰。"
        "茶饮、叶片、背景和自然投影应协调，避免像直接贴上去的素材；画面适合正式投影汇报。\n"
        "准确文字清单如下，每个 id 的文字均须出现，允许换行和空格变化，禁止改写或漏字；"
        "正文中近、超、年月、数字、单位、GO、标点和页脚来源必须保留。"
        "摘要与正文的重复是已确认设计，均须保留，不擅自去重。\n"
        + json.dumps(exact, ensure_ascii=False, indent=2)
        + "\n上面的 id、role、字段名、引号只是说明，不得印在画面上。"
        "不要添加任何额外文字、免责声明、制作说明、品牌 Logo 或水印。"
        "保持左侧三组内容与右侧茶饮的主关系，可微调几何；不要裁切内容。"
        "输出一张完整横向 16:9 幻灯片图片，目标 2560×1440；若尺寸不可锁定，优先保持完整 16:9 构图。\n"
    )
    package_dir = run_dir / "image-input"
    package_dir.mkdir(exist_ok=True)
    write_json(package_dir / "exact-text.json", {"texts": exact, "content_groups": outline["slides"][0].get("content_groups", {})})
    (package_dir / "redraw-prompt.txt").write_text(prompt, encoding="utf-8")
    package = {
        "schema_version": 1, "run_id": state["run_id"], "input_sha256": state["input_sha256"],
        "pptx_sha256": state["pptx_sha256"], "checks_sha256": state["checks_sha256"],
        "reference": {"role": "confirmed_v1_content_and_layout", "path_base": "run_dir", "path": render["reference_png"], "sha256": render["reference_sha256"]},
        "assets": [{"role": shape["role"], "path_base": "project_root", "path": shape["image_path"], "sha256": shape["image_sha256"]} for shape in manifest["slides"][0]["shapes"] if shape["type"] == "picture"],
        "prompt_sha256": sha256_file(package_dir / "redraw-prompt.txt"), "exact_text_sha256": sha256_file(package_dir / "exact-text.json"),
        "tool": "session image_gen", "model": "unknown", "output_target": "opaque PNG; native size; 16:9 relative error <=0.5%; no postprocessing",
    }
    write_json(package_dir / "handoff.json", package)
    state["v1_confirmed"] = True
    state.setdefault("v1_confirmation", {"input_sha256": state["input_sha256"], "pptx_sha256": state["pptx_sha256"], "recorded_at_utc": datetime.now(timezone.utc).isoformat(), "source": "explicit --v1-confirmed after human approval"})
    if state["state"] == "awaiting_v1_confirmation":
        state["state"] = "ready_for_image_generation"
    state.update(image_input=(package_dir / "handoff.json").relative_to(out_root).as_posix(), image_input_sha256=sha256_file(package_dir / "handoff.json"))
    write_json(out_root / "latest.json", state)
    return {"passed": True, "state": state["state"], "v1_confirmed": True, "texts": len(exact), "handoff": str(package_dir / "handoff.json"), "prompt": str(package_dir / "redraw-prompt.txt")}


def main() -> int:
    """校验输入；退出码 0 成功、2 数据/素材错误、1 环境/运行失败。"""
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    validate = subparsers.add_parser("validate", help="校验单页输入与独立素材")
    validate.add_argument("--input", required=True)
    validate.add_argument("--schema-only", action="store_true", help="仅检查结构和字体配置，不检查尚未生成的素材")
    build = subparsers.add_parser("build", help="构建 1 页可编辑 PPT 与最小 manifest")
    build.add_argument("--input", required=True)
    build.add_argument("--out", required=True)
    check = subparsers.add_parser("check", help="真实导出 PDF/PNG 并核对内容、字体与几何")
    check.add_argument("--input", required=True)
    check.add_argument("--out", required=True)
    check.add_argument("--soffice", help="LibreOffice 直接可执行文件路径")
    prepare = subparsers.add_parser("prepare-image", help="记录已有 v1 确认并准备会话生图输入包")
    prepare.add_argument("--input", required=True)
    prepare.add_argument("--out", required=True)
    prepare.add_argument("--v1-confirmed", action="store_true", help="仅在人类已确认当前 v1 后传入")
    args = parser.parse_args()
    try:
        outline = load_outline(args.input)
        config = load_config(outline)
        if args.command == "prepare-image":
            result = prepare_image(outline, config, project_path(args.out), args.v1_confirmed)
            print(json.dumps(result, ensure_ascii=False))
            return 0
        if args.command == "build":
            from .builder import build_slide
            result = build_slide(outline, config, project_path(args.out))
            print(json.dumps(result, ensure_ascii=False))
            return 0
        if args.command == "check":
            from .builder import write_json
            from .checks import check_v1
            from .render import render_reference
            out_root = project_path(args.out)
            state, run_dir, manifest = current_run(out_root, outline)
            state.update(state="checking", v1_confirmed=False)
            for key in ("checks_sha256", "v1_confirmation", "image_input", "image_input_sha256", "final_image"):
                state.pop(key, None)
            write_json(out_root / "latest.json", state)
            if args.soffice:
                config["soffice"] = args.soffice
            try:
                asset_issues = check_assets(outline)
                if asset_issues:
                    raise ValueError("; ".join(asset_issues))
                render = render_reference(run_dir / state["pptx_file"], config, run_dir)
                report = check_v1(run_dir / state["pptx_file"], run_dir / render["pdf"], manifest, config)
                write_json(run_dir / "checks.json", report)
                state.update(render=render, checks_sha256=sha256_file(run_dir / "checks.json"), state="awaiting_v1_confirmation" if report["passed"] else "failed")
                write_json(out_root / "latest.json", state)
                print(json.dumps({"passed": report["passed"], "state": state["state"], "issues": report["issues"], "slides": report["slides"], "shapes": report["shapes"], "pdf_fonts": report["pdf_fonts"], "reference": str(run_dir / render["reference_png"]), "report": str(run_dir / "checks.json")}, ensure_ascii=False))
                return 0 if report["passed"] else 2
            except (OSError, ValueError, RuntimeError):
                state.update(state="failed", v1_confirmed=False)
                write_json(out_root / "latest.json", state)
                raise
        issues = [] if args.schema_only else check_assets(outline)
        print(json.dumps({"command": args.command, "valid_schema": True, "schema_only": args.schema_only, "ready": not args.schema_only and not issues, "issues": issues, "input_sha256": outline["_input_sha256"]}, ensure_ascii=False))
        return 2 if issues else 0
    except (ValueError, KeyError, TypeError) as exc:
        print(json.dumps({"passed": False, "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2
    except (OSError, RuntimeError) as exc:
        print(json.dumps({"passed": False, "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
