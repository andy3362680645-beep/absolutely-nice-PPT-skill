"""M1 LibreOffice 辅助导出；最终展示图仍由会话生图工具生成。"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import subprocess
import tempfile
import uuid

import pymupdf

from .config import sha256_file


def render_reference(pptx_path: Path, config: dict, run_dir: Path) -> dict:
    """在独立子目录中导出 PDF 和参考 PNG，拒绝陈旧或无效输出。"""
    soffice = Path(config["soffice"])
    if not soffice.is_file() or soffice.suffix.lower() not in {".exe", ".com"}:
        raise ValueError("需配置 LibreOffice 直接可执行文件（soffice.com/exe），不使用会改名的包装脚本")
    export_dir = run_dir / ("render-" + uuid.uuid4().hex[:8])
    export_dir.mkdir()
    with tempfile.TemporaryDirectory(prefix="m1-lo-") as profile:
        try:
            result = subprocess.run(
                [str(soffice), "-env:UserInstallation=" + Path(profile).as_uri(), "--headless", "--convert-to", "pdf", "--outdir", str(export_dir), str(pptx_path)],
                capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=config["render_timeout_s"],
            )
        except subprocess.TimeoutExpired as exc:
            raise RuntimeError("LibreOffice 转换超时，未将旧 PDF 作为结果") from exc
    pdf_path = export_dir / (pptx_path.stem + ".pdf")
    if result.returncode != 0 or not pdf_path.is_file():
        raise RuntimeError(f"LibreOffice 转换失败（{result.returncode}）: {(result.stdout + result.stderr)[-800:]}")
    with pymupdf.open(pdf_path) as doc:
        if len(doc) != 1:
            raise RuntimeError("辅助 PDF 必须为 1 页")
        page = doc[0]
        if abs(page.rect.width - config["canvas"]["width_pt"]) > 0.1 or abs(page.rect.height - config["canvas"]["height_pt"]) > 0.1:
            raise RuntimeError("辅助 PDF 页尺寸与画布不一致")
        png_path = export_dir / "reference.png"
        scale = config["canvas"]["reference_width_px"] / page.rect.width
        page.get_pixmap(matrix=pymupdf.Matrix(scale, scale), alpha=False).save(png_path)
    return {
        "pdf": pdf_path.relative_to(run_dir).as_posix(), "reference_png": png_path.relative_to(run_dir).as_posix(),
        "pdf_sha256": sha256_file(pdf_path), "reference_sha256": sha256_file(png_path),
        "rendered_at_utc": datetime.now(timezone.utc).isoformat(), "lo_exit_code": result.returncode,
    }
