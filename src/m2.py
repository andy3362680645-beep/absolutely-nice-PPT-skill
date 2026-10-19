"""M2 多页可编辑 PPT：校验、构建、实际逐页检查。"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from zipfile import BadZipFile

from .builder import build_deck, verify_reopened, write_json
from .checks import check_deck_v1
from .config import ROOT, load_config, project_path, sha256_file
from .outline import check_assets, load_deck_outline
from .render import render_deck_reference


def _output_root(value: str) -> Path:
    """本轮仅写 M2 产物树，避免覆盖 M1 或源码。"""
    path = project_path(value)
    if not path.is_relative_to((ROOT / "output/m2-multi-slide").resolve()):
        raise ValueError("M2 --out 须位于 output/m2-multi-slide 内")
    return path


def _artifact(base: Path, relative: str, digest: str) -> Path:
    """核对运行目录内的真实文件，不以存在性或旧状态代替证据。"""
    path = (base / relative).resolve()
    if not path.is_relative_to(base.resolve()) or not path.is_file() or sha256_file(path) != digest:
        raise ValueError(f"证据缺失或改变: {relative}")
    return path


def current_run(root: Path, outline: dict, config: dict) -> tuple[dict, Path, dict]:
    """读取同一执行源、PPT、清单、素材及字体对应的安全运行。"""
    state = json.loads((root / "latest.json").read_text(encoding="utf-8"))
    run = (root / state["run_dir"]).resolve()
    if not run.is_relative_to((root / "runs").resolve()) or run.name != state["run_id"]:
        raise ValueError("无效运行目录")
    if state["input_sha256"] != outline["_input_sha256"]:
        raise ValueError("输入已改变，请重新 build")
    if Path(state["pptx_file"]).name != state["pptx_file"]:
        raise ValueError("无效 PPT 文件名")
    _artifact(run, state["pptx_file"], state["pptx_sha256"])
    manifest_path = _artifact(run, "manifest.json", state["manifest_sha256"])
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest["schema_version"] != 2 or any(manifest[key] != expected for key, expected in (
        ("run_id", state["run_id"]), ("input_sha256", outline["_input_sha256"]),
        ("pptx_file", state["pptx_file"]), ("deck_id", outline["deck_id"]))):
        raise ValueError("清单不属于当前 M2 运行")
    if manifest["asset_source_record"] != outline["asset_source_record"] or sha256_file(project_path(outline["asset_source_record"])) != manifest["asset_source_sha256"]:
        raise ValueError("素材来源记录已改变，请重新 build")
    issues = check_assets(outline) + verify_reopened(run / state["pptx_file"], manifest)
    if set(config["fonts"]) != set(manifest["font_records"]) or any(
        font["sha256"] != manifest["font_records"].get(key, {}).get("sha256") for key, font in config["fonts"].items()
    ):
        issues.append("字体已改变")
    if issues:
        raise ValueError("请重新核对素材/对象并 build: " + "; ".join(issues))
    return state, run, manifest


def _previous_check(state: dict, run: Path) -> None:
    """重新检查之前拒绝混用已损坏的旧报告和参考图。"""
    if "checks_sha256" not in state and "render" not in state:
        return
    report = json.loads(_artifact(run, "checks.json", state["checks_sha256"]).read_text(encoding="utf-8"))
    render = state["render"]
    _artifact(run, render["pdf"], render["pdf_sha256"])
    if report["pptx_sha256"] != state["pptx_sha256"] or report["input_sha256"] != state["input_sha256"] or report["pdf_sha256"] != render["pdf_sha256"] or report["references"] != render["pages"]:
        raise ValueError("旧检查与当前运行不一致，请重新 build")
    for page in render["pages"]:
        _artifact(run, page["reference_png"], page["reference_sha256"])


def _clear_confirmation(state: dict) -> None:
    """取消旧人类确认引用，不删除历史证据。"""
    state["v1_confirmed"] = False
    for key in ("v1_confirmation", "v1_review", "v1_review_sha256", "final_image", "image_input", "image_input_sha256"):
        state.pop(key, None)


def _fail_existing(root: Path | None, error: str) -> None:
    """只将指定 M2 根目录中的最新状态标为失败。"""
    if root is None or not (root / "latest.json").is_file():
        return
    try:
        state = json.loads((root / "latest.json").read_text(encoding="utf-8"))
        _clear_confirmation(state)
        state.update(state="failed", error=error)
        write_json(root / "latest.json", state)
    except (OSError, ValueError, TypeError):
        # 无法解析的状态不是可复用证据；主调用仍返回原始失败。
        return


def check(outline: dict, config: dict, root: Path) -> dict:
    """每次实际重新导出，逐页检查并保存与参考图绑定的报告。"""
    state, run, manifest = current_run(root, outline, config)
    _previous_check(state, run)
    _clear_confirmation(state)
    for key in ("checks_sha256", "render", "error"):
        state.pop(key, None)
    state["state"] = "checking"
    write_json(root / "latest.json", state)
    render = render_deck_reference(run / state["pptx_file"], config, run, manifest["slides"])
    report = check_deck_v1(run / state["pptx_file"], run / render["pdf"], manifest, config)
    report.update(references=render["pages"], manifest_sha256=state["manifest_sha256"],
                  asset_source_sha256=manifest["asset_source_sha256"])
    write_json(run / "checks.json", report)
    state.update(render=render, checks_sha256=sha256_file(run / "checks.json"),
                 state="awaiting_v1_confirmation" if report["passed"] else "failed")
    write_json(root / "latest.json", state)
    return {"passed": report["passed"], "state": state["state"], "slides": report["slide_count"],
            "pages": [{"slide_index": page["slide_index"], "slide_id": page["slide_id"],
                       "passed": page["passed"], "issues": page["issues"]} for page in report["slides"]],
            "issues": report["issues"], "report": str(run / "checks.json"),
            "references": [str(run / page["reference_png"]) for page in render["pages"]],
            "summary": f"共 {len(report['slides'])} 页，{sum(page['passed'] for page in report['slides'])} 页逐页检查通过；" + ("等待查看画面并确认可编辑版。" if report["passed"] else "整套未通过，请查看对应页问题。")}


def main() -> int:
    """0 通过、2 输入/内容/证据失败、1 环境/执行失败。"""
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("validate", "build", "check"):
        command = commands.add_parser(name)
        command.add_argument("--input", required=True)
        if name == "validate":
            command.add_argument("--schema-only", action="store_true")
        else:
            command.add_argument("--out", required=True)
        if name == "check":
            command.add_argument("--soffice")
    args = parser.parse_args()
    root = None
    try:
        if args.command != "validate":
            root = _output_root(args.out)
        outline = load_deck_outline(args.input)
        config = load_config(outline)
        if args.command == "validate":
            issues = [] if args.schema_only else check_assets(outline)
            result = {"passed": not issues, "valid_schema": True, "schema_only": args.schema_only,
                      "ready": not args.schema_only and not issues, "slides": len(outline["slides"]),
                      "issues": issues, "input_sha256": outline["_input_sha256"]}
        elif args.command == "build":
            result = build_deck(outline, config, root)
        else:
            if args.soffice:
                config["soffice"] = args.soffice
            result = check(outline, config, root)
        print(json.dumps(result, ensure_ascii=False))
        return 0 if result["passed"] else 2
    except (ValueError, KeyError, TypeError, BadZipFile) as exc:
        _fail_existing(root, str(exc))
        print(json.dumps({"passed": False, "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2
    except (OSError, RuntimeError) as exc:
        _fail_existing(root, str(exc))
        print(json.dumps({"passed": False, "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
