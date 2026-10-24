"""M1 LibreOffice 辅助导出；最终展示图仍由会话生图工具生成。"""

from __future__ import annotations

from datetime import datetime, timezone
from contextlib import contextmanager
import os
from pathlib import Path
import subprocess
import tempfile
import uuid

import pymupdf

from .config import sha256_file


@contextmanager
def _session_fonts(config: dict):
    """Windows 会话中临时加载已配置字体；仅释放本次增加的引用。"""
    if os.name != "nt":
        yield []
        return
    import ctypes
    gdi = ctypes.WinDLL("gdi32", use_last_error=True)
    for function in (gdi.AddFontResourceExW, gdi.RemoveFontResourceExW):
        function.argtypes = [ctypes.c_wchar_p, ctypes.c_uint, ctypes.c_void_p]
        function.restype = ctypes.c_int
    loaded = []
    try:
        for path in dict.fromkeys(str(font["resolved_path"]) for font in config["fonts"].values()):
            count = gdi.AddFontResourceExW(path, 0, None)
            if count == 0:
                raise RuntimeError(f"当前会话无法加载字体: {Path(path).name}")
            loaded.append((path, count))
        yield [{"file": Path(path).name, "resources": count} for path, count in loaded]
    finally:
        for path, _ in reversed(loaded):
            gdi.RemoveFontResourceExW(path, 0, None)


def _export_pdf(pptx_path, config, run_dir):
    """一次独立 LO 转换；不复用旧目录中的输出。"""
    soffice = Path(config["soffice"])
    if not soffice.is_file() or soffice.suffix.lower() not in {".exe", ".com"}:
        raise ValueError("需配置 LibreOffice 直接可执行文件（soffice.com/exe），不使用会改名的包装脚本")
    export_dir = run_dir / ("render-" + uuid.uuid4().hex[:8])
    export_dir.mkdir()
    with _session_fonts(config) as font_loads, tempfile.TemporaryDirectory(prefix="m1-lo-") as profile:
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
    return pdf_path, font_loads, result.returncode


def render_reference(pptx_path: Path, config: dict, run_dir: Path) -> dict:
    """保持 M1 一页 reference.png 与旧结果字段。"""
    pdf_path, font_loads, exit_code = _export_pdf(pptx_path, config, run_dir)
    export_dir = pdf_path.parent
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
        "rendered_at_utc": datetime.now(timezone.utc).isoformat(), "lo_exit_code": exit_code,
        "session_font_loads": font_loads,
    }



def render_deck_reference(pptx_path: Path, config: dict, run_dir: Path, slide_records: list[dict]) -> dict:
    """整套转 PDF 后按清单逐页导出，记录独立路径与真实尺寸。"""
    if not slide_records:
        raise ValueError("页面清单不能为空")
    pdf_path, font_loads, exit_code = _export_pdf(pptx_path, config, run_dir)
    pages = []
    with pymupdf.open(pdf_path) as doc:
        if len(doc) != len(slide_records):
            raise RuntimeError(f"辅助 PDF 页数错误: 预期 {len(slide_records)}，实际 {len(doc)}")
        for index, (page, record) in enumerate(zip(doc, slide_records), 1):
            if abs(page.rect.width - config["canvas"]["width_pt"]) > .1 or abs(page.rect.height - config["canvas"]["height_pt"]) > .1:
                raise RuntimeError(f"第 {index} 页 [{record['slide_id']}] PDF 尺寸不一致")
            png = pdf_path.parent / f"reference-{index:02d}.png"
            scale = config["canvas"]["reference_width_px"] / page.rect.width
            pix = page.get_pixmap(matrix=pymupdf.Matrix(scale, scale), alpha=False)
            pix.save(png)
            pages.append({"slide_index": index, "slide_id": record["slide_id"],
                          "reference_png": png.relative_to(run_dir).as_posix(),
                          "reference_sha256": sha256_file(png), "size_px": [pix.width, pix.height]})
    return {"pdf": pdf_path.relative_to(run_dir).as_posix(), "pdf_sha256": sha256_file(pdf_path),
            "pages": pages, "rendered_at_utc": datetime.now(timezone.utc).isoformat(),
            "lo_exit_code": exit_code, "session_font_loads": font_loads}
