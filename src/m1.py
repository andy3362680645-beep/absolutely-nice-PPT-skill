"""M1 本地执行入口；生图由会话工具接续，不虚构独立 API。"""

from __future__ import annotations

import argparse
import json
import sys

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
    args = parser.parse_args()
    try:
        outline = load_outline(args.input)
        config = load_config(outline)
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
            state.pop("checks_sha256", None)
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
