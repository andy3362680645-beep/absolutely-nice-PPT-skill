"""M1 本地执行入口；生图由会话工具接续，不虚构独立 API。"""

from __future__ import annotations

import argparse
import json
import sys

from .config import load_config
from .outline import check_assets, load_outline


def main() -> int:
    """校验输入；退出码 0 成功、2 数据/素材错误、1 环境/运行失败。"""
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    validate = subparsers.add_parser("validate", help="校验单页输入与独立素材")
    validate.add_argument("--input", required=True)
    validate.add_argument("--schema-only", action="store_true", help="仅检查结构和字体配置，不检查尚未生成的素材")
    args = parser.parse_args()
    try:
        outline = load_outline(args.input)
        load_config(outline)
        issues = [] if args.schema_only else check_assets(outline)
        print(json.dumps({"command": args.command, "valid_schema": True, "schema_only": args.schema_only, "ready": not args.schema_only and not issues, "issues": issues, "input_sha256": outline["_input_sha256"]}, ensure_ascii=False))
        return 2 if issues else 0
    except (ValueError, KeyError, TypeError) as exc:
        print(json.dumps({"passed": False, "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2
    except OSError as exc:
        print(json.dumps({"passed": False, "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
