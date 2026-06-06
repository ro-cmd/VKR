# -*- coding: utf-8 -*-
"""Archaeological Mapping Toolkit — Desktop App (PySide6)."""
import json, os, subprocess, sys, threading, traceback
from pathlib import Path

if getattr(sys, "frozen", False):
    ROOT = Path(sys.executable).parent
else:
    ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# matplotlib Agg FIRST — before any Qt backend gets loaded
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.figure import Figure

try:
    from PySide6.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QStackedWidget, QPushButton, QLabel, QLineEdit, QTextEdit,
        QFileDialog, QMessageBox, QFrame, QScrollArea, QCheckBox,
        QComboBox, QSlider, QProgressBar, QSizePolicy,
        QGraphicsOpacityEffect,
    )
    from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QTimer, QSize, Signal, QObject
    from PySide6.QtGui import QFont, QPixmap, QShortcut, QKeySequence
except ImportError as e:
    print(f"PySide6 not found: {e}")
    print("Install: pip install PySide6")
    input("Press Enter to exit...")
    sys.exit(1)

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg

CONFIG_FILE = ROOT / "app_config.json"
RECENT_FILE = ROOT / "recent_files.json"

STYLE = """
* { font-family: "Segoe UI", sans-serif; }
QMainWindow { background: #f5f5f7; }
QFrame#card {
    background: #ffffff;
    border: 1px solid #d8d8dc;
    border-radius: 12px;
}
QFrame#topbar { background: #eae7f0; border: none; border-bottom: 1px solid #d0cdd8; }
QFrame#statusbar { background: #eae7f0; border: none; border-top: 1px solid #d0cdd8; }

QPushButton#nav {
    background: transparent; color: #666; border: none;
    padding: 8px 18px; font-size: 13px; font-weight: 500;
    border-radius: 6px;
}
QPushButton#nav:hover { background: #ddd8e6; color: #333; }
QPushButton#nav:checked { background: #6b5b95; color: #fff; font-weight: 600; }

QPushButton#action {
    background: #6b5b95; color: #fff; border: none;
    padding: 9px 22px; font-size: 13px; font-weight: 600;
    border-radius: 8px;
}
QPushButton#action:hover { background: #7d6ba8; }
QPushButton#action:pressed { background: #5a4a84; }
QPushButton#action:disabled { background: #bbb; color: #888; }

QPushButton#small {
    background: #e8e6f0; color: #333; border: none;
    padding: 7px 14px; font-size: 12px; border-radius: 6px;
}
QPushButton#small:hover { background: #d8d5e3; }

QLineEdit, QComboBox {
    background: #fff; color: #111; border: 1px solid #ccc;
    border-radius: 6px; padding: 7px 10px; font-size: 13px;
}
QLineEdit:focus, QComboBox:focus { border-color: #6b5b95; }

QTextEdit {
    background: #fff; color: #111; border: 1px solid #ccc;
    border-radius: 6px; padding: 6px; font-size: 12px;
}
QLabel { color: #222; font-size: 13px; }
QLabel#heading { font-size: 17px; font-weight: 700; color: #1a1a2e; }
QLabel#sub { color: #777; font-size: 12px; }
QLabel#placeholder {
    color: #999; font-size: 13px; background: #fafafa;
    border: 1px dashed #ccc; border-radius: 8px;
}
QCheckBox { color: #222; font-size: 13px; spacing: 6px; }
QProgressBar {
    border: none; background: #e0dde8; border-radius: 4px; height: 6px;
}
QProgressBar::chunk { background: #6b5b95; border-radius: 4px; }
QSlider::groove:horizontal { height: 5px; background: #ddd; border-radius: 2px; }
QSlider::handle:horizontal {
    width: 16px; height: 16px; margin: -6px 0;
    background: #6b5b95; border-radius: 8px;
}
QComboBox QAbstractItemView {
    background: #fff; color: #111; padding: 4px;
}
QScrollArea { border: none; background: transparent; }
"""

STYLE_DARK = """
* { font-family: "Segoe UI", sans-serif; }
QMainWindow { background: #1a1a2e; }
QFrame#card {
    background: #2d2d3d;
    border: 1px solid #444;
    border-radius: 12px;
}
QFrame#topbar { background: #252540; border: none; border-bottom: 1px solid #444; }
QFrame#statusbar { background: #252540; border: none; border-top: 1px solid #444; }

QPushButton#nav {
    background: transparent; color: #a0a0b0; border: none;
    padding: 8px 18px; font-size: 13px; font-weight: 500;
    border-radius: 6px;
}
QPushButton#nav:hover { background: #3d3d50; color: #e8e6f0; }
QPushButton#nav:checked { background: #6b5b95; color: #fff; font-weight: 600; }

QPushButton#action {
    background: #6b5b95; color: #fff; border: none;
    padding: 9px 22px; font-size: 13px; font-weight: 600;
    border-radius: 8px;
}
QPushButton#action:hover { background: #7d6ba8; }
QPushButton#action:pressed { background: #5a4a84; }
QPushButton#action:disabled { background: #444; color: #888; }

QPushButton#small {
    background: #3d3d50; color: #e8e6f0; border: none;
    padding: 7px 14px; font-size: 12px; border-radius: 6px;
}
QPushButton#small:hover { background: #4d4d60; }

QLineEdit, QComboBox {
    background: #252540; color: #e8e6f0; border: 1px solid #444;
    border-radius: 6px; padding: 7px 10px; font-size: 13px;
}
QLineEdit:focus, QComboBox:focus { border-color: #6b5b95; }
QComboBox QAbstractItemView {
    background: #2d2d3d; color: #e8e6f0; selection-background-color: #6b5b95;
    selection-color: #fff; padding: 4px; font-size: 13px;
}
QComboBox::drop-down {
    border: none; background: #3d3d50; border-radius: 4px;
}
QComboBox QAbstractItemView::item {
    color: #e8e6f0; min-height: 24px; padding: 2px 8px;
}
QComboBox QAbstractItemView::item:selected {
    background: #6b5b95; color: #fff;
}
QComboBox QAbstractItemView::item:hover {
    background: #3d3d50; color: #fff;
}

QTextEdit {
    background: #252540; color: #e8e6f0; border: 1px solid #444;
    border-radius: 6px; padding: 6px; font-size: 12px;
}
QLabel { color: #e8e6f0; font-size: 13px; }
QLabel#heading { font-size: 17px; font-weight: 700; color: #fff; }
QLabel#sub { color: #a0a0b0; font-size: 12px; }
QLabel#placeholder {
    color: #888; font-size: 13px; background: #252540;
    border: 1px dashed #555; border-radius: 8px;
}
QCheckBox { color: #e8e6f0; font-size: 13px; spacing: 6px; }
QProgressBar {
    border: none; background: #3d3d50; border-radius: 4px; height: 6px;
}
QProgressBar::chunk { background: #6b5b95; border-radius: 4px; }
QSlider::groove:horizontal { height: 5px; background: #444; border-radius: 2px; }
QSlider::handle:horizontal {
    width: 16px; height: 16px; margin: -6px 0;
    background: #6b5b95; border-radius: 8px;
}
QScrollArea { border: none; background: transparent; }
"""


# ── helpers ──────────────────────────────────────────────────────────────

def load_recent():
    try:
        if RECENT_FILE.exists():
            return json.loads(RECENT_FILE.read_text("utf-8"))
    except Exception:
        pass
    return []

def save_recent(path):
    r = [p for p in load_recent() if p != path]
    r.insert(0, path)
    try:
        RECENT_FILE.write_text(json.dumps(r[:10], ensure_ascii=False), "utf-8")
    except Exception:
        pass

def load_config():
    try:
        if CONFIG_FILE.exists():
            return json.loads(CONFIG_FILE.read_text("utf-8"))
    except Exception:
        pass
    return {}

def save_config(cfg):
    try:
        CONFIG_FILE.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), "utf-8")
    except Exception:
        pass

DEFAULTS = {
    "source_crs": "EPSG:3857", "target_crs": "EPSG:3857",
    "quality_profile": "standard",
    "max_z_sigma": 3.5, "max_planar_jump": 10.0, "min_point_spacing": 0.2,
    "connect_codes": "BASE,STAIN_01,STAIN_11,STAIN_12,STAIN_02,STAIN_21,STAIN_22",
    "center_keywords": "центр,center", "title": "Archaeological Survey",
    "output_dir": str(ROOT / "output"),
    "write_summary": True, "write_quality": True,
    "plots_enabled": True, "interactive_3d": True, "basemap": False,
    "auto_levels": False,
}


def run_pipeline(config_dict, stop_check=None):
    """Heavy work — runs in background thread. Returns (ok, msg, outdir, plan2d, data_dict)."""
    def stopped():
        return stop_check and stop_check()
    try:
        from archaeo.config import AppConfig
        from archaeo.crs import transform_gdf
        from pathlib import Path
        from archaeo.exporting import (
            export_lines,
            export_planes,
            export_points,
            export_plan_2d_map,
            export_plan_2d_map_leaflet,
            write_excel_reports,
            write_load_report,
            write_summary,
        )
        from archaeo.io import load_surveys
        from archaeo.plots import plot_3d, plot_3d_interactive, plot_plan, plot_vertical_sections
        from archaeo.stats import generate_pdf_report
        from archaeo.processing import build_lines, build_planes, expand_excavation_stages, find_center_point
        from archaeo.quality import (
            QualityConfig,
            build_quality_issues,
            build_quality_report,
            quality_issues_to_dataframe,
            write_quality_issues_report,
            write_quality_report,
        )

        d = config_dict
        cfg = AppConfig(
            input_path=d["input_path"], encoding=d.get("encoding"),
            source_crs=d.get("source_crs") or "EPSG:3857",
            target_crs=d.get("target_crs") or d.get("source_crs") or "EPSG:3857",
            output_dir=d["output_dir"],
            export_formats=d.get("export_formats") or ["gpkg", "geojson"],
            connect_codes=d.get("connect_codes") or ["BASE"],
            annotate_prefixes=d.get("annotate_prefixes") or ["FIND_"],
            plot_title=d.get("title") or "Archaeological Survey",
            plots_enabled=d.get("plots_enabled", True),
            basemap=d.get("basemap", False), basemap_provider="OpenStreetMap.Mapnik",
            show_plots=False, interactive_3d=d.get("interactive_3d", True),
            write_summary=d.get("write_summary", True), write_quality=d.get("write_quality", True),
            center_point_id=d.get("center_point_id"), center_code=d.get("center_code"),
            center_description_keywords=d.get("center_description_keywords") or ["центр", "center"],
            max_z_sigma=float(d.get("max_z_sigma") or 3.5),
            max_planar_jump=float(d.get("max_planar_jump") or 5.0),
            min_point_spacing=float(d.get("min_point_spacing") or 0.2),
        )
        paths = [p.strip() for p in cfg.input_path.split(",") if p.strip()]
        if not paths:
            return False, "Укажите входной файл.", "", "", None

        print("[1/7] Loading data...", flush=True)
        data = load_surveys(paths, source_crs=cfg.source_crs, encoding=cfg.encoding)
        print(f"  Loaded {len(data.df)} rows, columns: {list(data.df.columns)}", flush=True)
        if stopped(): return False, "Остановлено.", "", "", None

        print("[2/7] Transforming CRS...", flush=True)
        data.gdf, data.crs = transform_gdf(data.gdf, cfg.target_crs)
        data.gdf = expand_excavation_stages(data.gdf)
        data.df["E"] = data.gdf.geometry.x
        data.df["N"] = data.gdf.geometry.y
        data.df["Code"] = data.gdf["Code"].values
        data.df["PointID"] = data.gdf["PointID"].values
        if stopped(): return False, "Остановлено.", "", "", None

        if d.get("auto_levels"):
            from archaeo.processing import auto_levels_by_elevation
            print("[2.5/7] Auto-levels by elevation...", flush=True)
            data.gdf = auto_levels_by_elevation(data.gdf, gap_percentile=85.0)
            data.df["Code"] = data.gdf["Code"].values
            cfg.connect_codes = sorted(data.gdf["Code"].unique().tolist())
        if stopped(): return False, "Остановлено.", "", "", None

        print("[3/7] Building geometry...", flush=True)
        center = find_center_point(data.gdf, cfg.center_point_id, cfg.center_code, cfg.center_description_keywords)
        lines = build_lines(data.gdf, cfg.connect_codes, center_row=center, close_loop=True)
        planes = build_planes(data.gdf, cfg.connect_codes, center_row=center)
        if stopped(): return False, "Остановлено.", "", "", None

        print("[4/7] Exporting...", flush=True)
        export_points(data.gdf, cfg.output_dir, cfg.export_formats, crs=data.crs)
        export_lines(lines, cfg.output_dir, cfg.export_formats)
        export_planes(planes, cfg.output_dir, cfg.export_formats)
        write_load_report(
            data.load_report,
            cfg.output_dir,
            relativize_base=Path(cfg.output_dir).parent,
        )
        if cfg.write_summary:
            write_summary(data.df, cfg.output_dir)
        quality_report_obj = None
        if cfg.write_quality:
            qc = QualityConfig(cfg.max_z_sigma, cfg.max_planar_jump, cfg.min_point_spacing)
            quality_report_obj = build_quality_report(data.df, cfg.connect_codes, qc)
            write_quality_report(quality_report_obj, cfg.output_dir)
            issues = build_quality_issues(data.df, cfg.connect_codes, qc)
            write_quality_issues_report(issues, cfg.output_dir)
            if cfg.write_summary:
                from dataclasses import asdict
                issues_df = quality_issues_to_dataframe(issues)
                write_excel_reports(
                    data.df,
                    asdict(quality_report_obj),
                    issues_df if not issues_df.empty else None,
                    cfg.output_dir,
                )
        if stopped(): return False, "Остановлено.", "", "", None

        plan2d = ""
        if cfg.plots_enabled:
            print("[5/7] Plot 2D...", flush=True)
            plan2d = os.path.join(cfg.output_dir, "plan_2d.png")
            plot_plan(data.gdf, lines, planes, center, plan2d, cfg.plot_title, cfg.annotate_prefixes, cfg.basemap, cfg.basemap_provider, False)
            if stopped(): return False, "Остановлено.", "", "", None
            print("[6/7] Plot 3D static...", flush=True)
            plot_3d(data.gdf, lines, planes, center, os.path.join(cfg.output_dir, "plan_3d.png"), f"{cfg.plot_title} (3D)", False)
            if stopped(): return False, "Остановлено.", "", "", None
            if cfg.interactive_3d:
                print("[7/7] Plot 3D interactive HTML...", flush=True)
                plot_3d_interactive(data.gdf, lines, planes, center, os.path.join(cfg.output_dir, "plan_3d_interactive.html"), f"{cfg.plot_title} (3D)")
            plot_vertical_sections(data.gdf, center, os.path.join(cfg.output_dir, "sections_2d.png"), cfg.plot_title)
            export_plan_2d_map(data.gdf, lines, cfg.output_dir, title=cfg.plot_title)
            export_plan_2d_map_leaflet(data.gdf, lines, planes, cfg.output_dir, title=cfg.plot_title)
        try:
            from dataclasses import asdict
            qd = asdict(quality_report_obj) if quality_report_obj else None
            generate_pdf_report(data.gdf, planes, cfg.output_dir, title=cfg.plot_title, plan_2d_path=plan2d, quality_report=qd)
        except Exception:
            pass
        print("[DONE]", flush=True)
        plt.close("all")

        ci = ""
        if center is not None:
            try:
                ci = f", центр: {center['PointID']}"
            except Exception:
                ci = ", центр: найден"
        msg = f"Готово! Точек: {len(data.df)}, файлов: {len(data.source_files)}, CRS: {data.crs}{ci}."
        dd = {
            "gdf": data.gdf, "lines_gdf": lines, "planes_gdf": planes,
            "center_row": center,
            "codes": sorted(data.gdf["Code"].unique().tolist()),
            "z_min": float(data.gdf["Z"].min()), "z_max": float(data.gdf["Z"].max()),
        }
        return True, msg, cfg.output_dir, plan2d, dd
    except Exception:
        return False, traceback.format_exc(), "", "", None


def load_preview(path):
    try:
        from archaeo.io import read_tabular_with_fallbacks, normalize_columns
        df = read_tabular_with_fallbacks(path, None)
        return normalize_columns(df).head(80), None
    except Exception as e:
        return None, str(e)


def load_codes_from_file(path):
    """Extract unique Code values from file for connect_codes. Returns list of strings or None on error."""
    try:
        from archaeo.io import read_tabular_with_fallbacks, normalize_columns, validate_columns
        df = read_tabular_with_fallbacks(path, None)
        df = normalize_columns(df)
        validate_columns(df)
        codes = sorted(df["Code"].dropna().astype(str).unique().tolist())
        return codes if codes else None
    except Exception:
        return None


# ── 3D figure builder ────────────────────────────────────────────────────

def _code_color(codes, code):
    pal = plt.get_cmap("tab10").colors
    return pal[codes.index(code) % len(pal)] if code in codes else pal[0]

def _filter_data(dd, code_filter):
    """Filter gdf/lines/planes by code. 'Все' = no filter."""
    gdf = dd["gdf"]; lines = dd["lines_gdf"]; planes = dd["planes_gdf"]
    if code_filter and code_filter != "Все":
        gdf = gdf[gdf["Code"] == code_filter]
        lines = lines[lines["Code"] == code_filter] if lines is not None and len(lines) else None
        planes = planes[planes["Code"] == code_filter] if planes is not None and len(planes) else None
    return gdf, lines, planes


def _ordered_subset(gdf, code, center_row):
    """Get points for code in polygon/line order (angle from centroid)."""
    from archaeo.processing import _order_by_angle, _remove_center
    sub = gdf[gdf["Code"] == code].copy()
    sub = _remove_center(sub, center_row)
    return _order_by_angle(sub)


def _data_bounds_2d(gdf, lines, planes, center, code_filter):
    """Collect all x,y from data for axis limits."""
    xs, ys = [], []
    if not gdf.empty:
        xs.extend(gdf.geometry.x); ys.extend(gdf.geometry.y)
    if lines is not None and len(lines):
        for _, r in lines.iterrows():
            x, y = r.geometry.xy
            xs.extend(x); ys.extend(y)
    if planes is not None and len(planes):
        for _, r in planes.iterrows():
            x, y = r.geometry.exterior.xy
            xs.extend(x); ys.extend(y)
    if center is not None and (not code_filter or code_filter == "Все"):
        xs.append(center.geometry.x); ys.append(center.geometry.y)
    return xs, ys


def build_2d_figure(dd, code_filter="Все", title=""):
    gdf, lines, planes = _filter_data(dd, code_filter)
    center = dd["center_row"]; codes = dd["codes"]

    fig = Figure(figsize=(8, 6), dpi=120)
    ax = fig.add_subplot(111)
    for code in gdf["Code"].unique():
        sub = gdf[gdf["Code"] == code]
        ax.scatter(sub.geometry.x, sub.geometry.y, c=_code_color(codes, code), label=code, s=50, alpha=0.9)
    if lines is not None and len(lines):
        for _, r in lines.iterrows():
            xs, ys = r.geometry.xy
            ax.plot(xs, ys, "-", lw=2, alpha=0.7, color=_code_color(codes, r["Code"]))
    if planes is not None and len(planes):
        for _, r in planes.iterrows():
            xs, ys = r.geometry.exterior.xy
            ax.fill(xs, ys, color=_code_color(codes, r["Code"]), alpha=0.15)
    if center is not None and (code_filter == "Все" or not code_filter):
        ax.scatter([center.geometry.x], [center.geometry.y], c="#111", s=130, marker="*", label="CENTER", zorder=5)
    xs, ys = _data_bounds_2d(gdf, lines, planes, center, code_filter)
    if xs and ys:
        xmin, xmax = min(xs), max(xs)
        ymin, ymax = min(ys), max(ys)
        margin = 0.03
        xr = max(xmax - xmin, 0.001) * margin
        yr = max(ymax - ymin, 0.001) * margin
        ax.set_xlim(xmin - xr, xmax + xr)
        ax.set_ylim(ymin - yr, ymax + yr)
    suffix = f" | {code_filter}" if code_filter and code_filter != "Все" else ""
    ax.set_title((title or "2D") + suffix)
    ax.set_xlabel("Easting"); ax.set_ylabel("Northing")
    ax.grid(True, alpha=0.25)
    ax.legend(loc="best", fontsize=7)
    ax.set_aspect("equal", adjustable="box")
    fig.tight_layout()
    return fig


def build_3d_figure(dd, code_filter="Все", z_layer=None, title=""):
    gdf_f, lines_f, planes_f = _filter_data(dd, code_filter)
    center = dd["center_row"]; codes = dd["codes"]
    zmin, zmax = dd["z_min"], dd["z_max"]

    if z_layer is not None and z_layer >= 0:
        band = max((zmax - zmin) / 10, 0.001)
        gdf_f = gdf_f[(gdf_f["Z"] >= zmin + z_layer * band) & (gdf_f["Z"] < zmin + (z_layer + 1) * band)]
        lines_f, planes_f = None, None
    gdf, lines, planes = gdf_f, lines_f, planes_f

    fig = Figure(figsize=(6, 5), dpi=100)
    ax = fig.add_subplot(111, projection="3d")
    for code in gdf["Code"].unique():
        sub = gdf[gdf["Code"] == code]
        ax.scatter(sub.geometry.x, sub.geometry.y, sub["Z"], c=_code_color(codes, code), label=code, s=45, alpha=0.9)
    if lines is not None and len(lines):
        for _, r in lines.iterrows():
            sub = _ordered_subset(dd["gdf"], r["Code"], center)
            if len(sub) >= 2:
                xs, ys = sub.geometry.x.values, sub.geometry.y.values
                zs = sub["Z"].values
                ax.plot(xs, ys, zs, "-", lw=2, alpha=0.7, color=_code_color(codes, r["Code"]))
    if planes is not None and len(planes):
        for _, r in planes.iterrows():
            sub = _ordered_subset(dd["gdf"], r["Code"], center)
            if len(sub) >= 3:
                xs, ys = sub.geometry.x.values, sub.geometry.y.values
                zs = sub["Z"].values
                try:
                    ax.plot_trisurf(xs, ys, zs, color=_code_color(codes, r["Code"]), alpha=0.2)
                except Exception:
                    ax.plot(xs, ys, zs, "-", color=_code_color(codes, r["Code"]), alpha=0.4)
    if center is not None and (code_filter == "Все" or not code_filter):
        ax.scatter([center.geometry.x], [center.geometry.y], [center["Z"]], c="#111", s=120, marker="*", label="CENTER")
    xs_all, ys_all, zs_all = [], [], []
    if not gdf.empty:
        xs_all.extend(gdf.geometry.x); ys_all.extend(gdf.geometry.y); zs_all.extend(gdf["Z"])
    if lines is not None and len(lines):
        for _, r in lines.iterrows():
            sub = _ordered_subset(dd["gdf"], r["Code"], center)
            if len(sub) >= 2:
                xs_all.extend(sub.geometry.x); ys_all.extend(sub.geometry.y); zs_all.extend(sub["Z"])
    if planes is not None and len(planes):
        for _, r in planes.iterrows():
            sub = _ordered_subset(dd["gdf"], r["Code"], center)
            if len(sub) >= 3:
                xs_all.extend(sub.geometry.x); ys_all.extend(sub.geometry.y); zs_all.extend(sub["Z"])
    if center is not None and (not code_filter or code_filter == "Все"):
        xs_all.append(center.geometry.x); ys_all.append(center.geometry.y); zs_all.append(center["Z"])
    if xs_all and ys_all and zs_all:
        margin = 0.03
        xr = max(max(xs_all) - min(xs_all), 0.001) * margin
        yr = max(max(ys_all) - min(ys_all), 0.001) * margin
        zr = max(max(zs_all) - min(zs_all), 0.001) * margin
        ax.set_xlim(min(xs_all) - xr, max(xs_all) + xr)
        ax.set_ylim(min(ys_all) - yr, max(ys_all) + yr)
        ax.set_zlim(min(zs_all) - zr, max(zs_all) + zr)
    ax.set_xlabel("Easting"); ax.set_ylabel("Northing"); ax.set_zlabel("Z")
    suffix = f" | {code_filter}" if code_filter and code_filter != "Все" else ""
    ax.set_title((title or "3D") + suffix)
    ax.legend(loc="upper left", fontsize=7)
    fig.tight_layout()
    return fig, ax


# ── Qt widgets ───────────────────────────────────────────────────────────

class AnimatedStack(QStackedWidget):
    def setCurrentIndexAnimated(self, idx, ms=250):
        if idx == self.currentIndex():
            return
        for i in range(self.count()):
            w = self.widget(i)
            if w and w.graphicsEffect():
                w.setGraphicsEffect(None)
        self.setCurrentIndex(idx)


class MplCanvas(FigureCanvasQTAgg):
    def __init__(self, fig):
        super().__init__(fig)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMinimumHeight(320)


class _PipelineSignals(QObject):
    finished = Signal(bool, str, str, str, object)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        try:
            from archaeo.version import __version__
            self.setWindowTitle(f"Archaeo Map v{__version__} — Archaeological Mapping Toolkit")
        except Exception:
            self.setWindowTitle("Archaeo Map — Archaeological Mapping Toolkit")
        self.setMinimumSize(900, 680)
        self.resize(1040, 780)
        self.setStyleSheet(STYLE)

        self.output_dir = ""
        self.data_dict = None
        self._canvas = None
        self._fig3d = None
        self._ax3d = None
        self._azim = 0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._rotate)
        self._signals = _PipelineSignals()
        self._signals.finished.connect(self._done)
        self._worker = None
        self._stop_flag = False
        self.cfg = {**DEFAULTS, **load_config()}
        self._dark_theme = self.cfg.get("dark_theme", False)

        cw = QWidget()
        self.setCentralWidget(cw)
        root = QVBoxLayout(cw)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── top bar ──
        bar = QFrame(objectName="topbar")
        bar.setFixedHeight(52)
        hb = QHBoxLayout(bar)
        hb.setContentsMargins(16, 0, 16, 0)
        hb.setSpacing(6)
        self._tabs = []
        for i, name in enumerate(["Данные", "Настройки", "Результаты", "3D"]):
            b = QPushButton(name, objectName="nav", checkable=True, checked=(i == 0))
            b.clicked.connect(lambda _, idx=i: self._go(idx))
            self._tabs.append(b)
            hb.addWidget(b)
        hb.addStretch()
        self.btn_run = QPushButton("Запустить", objectName="action")
        self.btn_run.clicked.connect(self._on_run)
        hb.addWidget(self.btn_run)
        self.btn_stop = QPushButton("Остановить", objectName="small", enabled=False)
        self.btn_stop.setStyleSheet("QPushButton { background: #d44; color: #fff; } QPushButton:hover { background: #e55; }")
        self.btn_stop.clicked.connect(self._on_stop)
        hb.addWidget(self.btn_stop)
        self.btn_dir = QPushButton("Открыть папку", objectName="small", enabled=False)
        self.btn_dir.clicked.connect(self._open_dir)
        hb.addWidget(self.btn_dir)
        self.btn_theme = QPushButton("🌙", objectName="small")
        self.btn_theme.setToolTip("Тёмная / светлая тема")
        self.btn_theme.clicked.connect(self._toggle_theme)
        hb.addWidget(self.btn_theme)
        root.addWidget(bar)

        # ── progress ──
        self.progress = QProgressBar(visible=False)
        self.progress.setRange(0, 0)
        self.progress.setFixedHeight(6)
        root.addWidget(self.progress)

        # ── stack ──
        self.stack = AnimatedStack()
        self._build_pages()
        root.addWidget(self.stack, 1)

        # ── status ──
        sb = QFrame(objectName="statusbar")
        sb.setFixedHeight(30)
        sbl = QHBoxLayout(sb)
        sbl.setContentsMargins(16, 0, 16, 0)
        self.status = QLabel("Готов", objectName="sub")
        sbl.addWidget(self.status)
        root.addWidget(sb)

        self._apply_cfg()
        self._apply_theme()
        self._setup_shortcuts()

    def _setup_shortcuts(self):
        """Горячие клавиши."""
        QShortcut(QKeySequence("Ctrl+O"), self, self._browse)
        QShortcut(QKeySequence("Ctrl+R"), self, self._on_run)
        QShortcut(QKeySequence("Ctrl+1"), self, lambda: self._go(0))
        QShortcut(QKeySequence("Ctrl+2"), self, lambda: self._go(1))
        QShortcut(QKeySequence("Ctrl+3"), self, lambda: self._go(2))
        QShortcut(QKeySequence("Ctrl+4"), self, lambda: self._go(3))
        QShortcut(QKeySequence("Escape"), self, self._on_stop)

    # ── pages ──

    def _build_pages(self):
        self.stack.addWidget(self._page_data())
        self.stack.addWidget(self._page_settings())
        self.stack.addWidget(self._page_results())
        self.stack.addWidget(self._page_3d())

    def _card(self):
        f = QFrame(objectName="card")
        lay = QVBoxLayout(f)
        lay.setContentsMargins(20, 18, 20, 18)
        lay.setSpacing(10)
        return f, lay

    def _page_data(self):
        page = QWidget()
        pl = QVBoxLayout(page)
        pl.setContentsMargins(24, 20, 24, 20)

        c, cl = self._card()
        cl.addWidget(QLabel("Загрузка данных", objectName="heading"))
        cl.addWidget(QLabel("Формат: CSV или Excel с колонками PointID, N, E, Z, Code, Description.", objectName="sub"))

        row = QHBoxLayout()
        self.f_path = QLineEdit(placeholderText="Путь к файлу...")
        row.addWidget(self.f_path, 1)
        b1 = QPushButton("Обзор", objectName="small")
        b1.clicked.connect(self._browse)
        row.addWidget(b1)
        b2 = QPushButton("Превью", objectName="small")
        b2.clicked.connect(self._preview)
        row.addWidget(b2)
        cl.addLayout(row)

        cl.addWidget(QLabel("Недавние файлы:", objectName="sub"))
        self._recent_box = QWidget()
        self._recent_lay = QHBoxLayout(self._recent_box)
        self._recent_lay.setContentsMargins(0, 0, 0, 0)
        self._recent_lay.setSpacing(4)
        cl.addWidget(self._recent_box)
        self._fill_recent()

        self.preview = QTextEdit(readOnly=True)
        self.preview.setFont(QFont("Consolas", 10))
        self.preview.setMinimumHeight(100)
        self.preview.setMaximumHeight(220)
        self.preview.setPlaceholderText("Нажмите Превью для просмотра данных...")
        cl.addWidget(self.preview)

        pl.addWidget(c)
        pl.addStretch()
        return page

    def _page_settings(self):
        page = QWidget()
        pl = QVBoxLayout(page)
        pl.setContentsMargins(24, 20, 24, 20)

        c, cl = self._card()
        cl.addWidget(QLabel("Параметры обработки", objectName="heading"))

        def row(label, widget):
            h = QHBoxLayout()
            lb = QLabel(label)
            lb.setFixedWidth(180)
            h.addWidget(lb)
            h.addWidget(widget, 1)
            cl.addLayout(h)

        self.s_crs = QLineEdit(placeholderText="EPSG:3857")
        self.s_crs_t = QLineEdit(placeholderText="EPSG:3857")
        self.s_codes = QLineEdit(placeholderText="BASE,STAIN_01,STAIN_11,STAIN_12,...")
        self.s_kw = QLineEdit(placeholderText="центр,center")
        self.s_title = QLineEdit(placeholderText="Archaeological Survey")
        self.s_out = QLineEdit(placeholderText=str(ROOT / "output"))
        row("CRS исходный:", self.s_crs)
        row("CRS целевой:", self.s_crs_t)
        row("Коды для линий:", self.s_codes)
        row("Ключевые слова центра:", self.s_kw)
        row("Заголовок:", self.s_title)

        out_row = QHBoxLayout()
        out_row.addWidget(self.s_out, 1)
        b = QPushButton("Обзор", objectName="small")
        b.clicked.connect(lambda: self.s_out.setText(QFileDialog.getExistingDirectory(self, "Папка", str(ROOT)) or self.s_out.text()))
        out_row.addWidget(b)
        h = QHBoxLayout()
        lb = QLabel("Папка результатов:")
        lb.setFixedWidth(180)
        h.addWidget(lb)
        h.addLayout(out_row, 1)
        cl.addLayout(h)

        self.s_quality_profile = QComboBox()
        self.s_quality_profile.addItems(["strict", "standard", "mild"])
        self.s_quality_profile.setToolTip("strict: жёстко | standard: стандарт | mild: мягко")
        row("Профиль качества:", self.s_quality_profile)
        self.cb_auto_levels = QCheckBox("Авто-уровни по высоте (BASE → EXC → STAIN)")
        self.cb_auto_levels.setToolTip("Разбить точки по Z: верх=BASE, средние=STAIN_01,STAIN_02,…, низ=STAIN")
        self.cb_sum = QCheckBox("Сводка summary.csv")
        self.cb_qual = QCheckBox("Отчёт качества")
        self.cb_plot = QCheckBox("2D / 3D планы")
        self.cb_3d = QCheckBox("Интерактивная 3D HTML")
        self.cb_map = QCheckBox("Подложка карты")
        cl.addWidget(self.cb_auto_levels)
        for cb in [self.cb_sum, self.cb_qual, self.cb_plot, self.cb_3d, self.cb_map]:
            cl.addWidget(cb)

        pl.addWidget(c)
        pl.addStretch()
        return page

    def _page_results(self):
        page = QWidget()
        pl = QVBoxLayout(page)
        pl.setContentsMargins(24, 20, 24, 20)

        c, cl = self._card()
        cl.addWidget(QLabel("Результаты обработки", objectName="heading"))
        self.log = QTextEdit(readOnly=True)
        self.log.setFont(QFont("Consolas", 10))
        self.log.setMinimumHeight(80)
        self.log.setMaximumHeight(120)
        self.log.setPlaceholderText("Лог обработки...")
        cl.addWidget(self.log)

        filt = QHBoxLayout()
        filt.addWidget(QLabel("Раскоп / код:"))
        self.combo_2d = QComboBox()
        self.combo_2d.addItem("Все")
        self.combo_2d.setMinimumWidth(160)
        self.combo_2d.currentTextChanged.connect(self._rebuild_2d)
        filt.addWidget(self.combo_2d)
        filt.addStretch()
        cl.addLayout(filt)

        self._2d_box = QVBoxLayout()
        self._2d_ph = QLabel("План 2D появится после обработки", objectName="placeholder", alignment=Qt.AlignmentFlag.AlignCenter)
        self._2d_ph.setMinimumHeight(300)
        self._2d_box.addWidget(self._2d_ph)
        cl.addLayout(self._2d_box)

        self._canvas_2d = None
        self._fig_2d = None

        pl.addWidget(c, 1)
        return page

    def _page_3d(self):
        page = QWidget()
        pl = QVBoxLayout(page)
        pl.setContentsMargins(24, 20, 24, 20)

        c, cl = self._card()
        cl.addWidget(QLabel("3D визуализация", objectName="heading"))
        cl.addWidget(QLabel("Фильтр по коду раскопа и высоте Z. Автоматическое вращение.", objectName="sub"))

        ctrl = QHBoxLayout()
        ctrl.addWidget(QLabel("Раскоп / код:"))
        self.combo_3d = QComboBox()
        self.combo_3d.addItem("Все")
        self.combo_3d.setMinimumWidth(160)
        self.combo_3d.currentTextChanged.connect(self._on_3d_code)
        ctrl.addWidget(self.combo_3d)
        ctrl.addSpacing(12)
        ctrl.addWidget(QLabel("Z-слой:"))
        self.zslider = QSlider(Qt.Orientation.Horizontal)
        self.zslider.setRange(-1, 9)
        self.zslider.setValue(-1)
        self.zslider.setToolTip("-1 = все слои")
        self.zslider.valueChanged.connect(self._on_3d_z)
        ctrl.addWidget(self.zslider)
        self.z_label = QLabel("все")
        self.z_label.setFixedWidth(30)
        ctrl.addWidget(self.z_label)
        ctrl.addSpacing(12)
        self.cb_rot = QCheckBox("Вращение", checked=True)
        self.cb_rot.stateChanged.connect(self._toggle_rot)
        ctrl.addWidget(self.cb_rot)
        cl.addLayout(ctrl)

        self._3d_box = QVBoxLayout()
        self._3d_ph = QLabel("Запустите обработку — 3D появится здесь", objectName="placeholder", alignment=Qt.AlignmentFlag.AlignCenter)
        self._3d_ph.setMinimumHeight(340)
        self._3d_box.addWidget(self._3d_ph)
        cl.addLayout(self._3d_box)

        pl.addWidget(c, 1)
        return page

    # ── actions ──

    def _go(self, idx):
        for i, b in enumerate(self._tabs):
            b.setChecked(i == idx)
        self.stack.setCurrentIndexAnimated(idx)
        if idx == 2 and self.data_dict and self._canvas_2d is None:
            self._rebuild_2d("Все")
        if idx == 3 and self.data_dict and self._canvas is None:
            self._rebuild_3d()

    def _browse(self):
        p, _ = QFileDialog.getOpenFileName(self, "Файл", str(ROOT), "CSV/Excel (*.csv *.xlsx *.xls);;All (*)")
        if p:
            self.f_path.setText(p)
            save_recent(p)
            self._fill_recent()
            self._apply_codes_from_file(p)
            self.status.setText(f"Выбран: {os.path.basename(p)}")

    def _fill_recent(self):
        while self._recent_lay.count():
            w = self._recent_lay.takeAt(0).widget()
            if w:
                w.deleteLater()
        for p in load_recent()[:5]:
            if os.path.isfile(p):
                b = QPushButton(os.path.basename(p), objectName="small")
                b.setToolTip(p)
                b.clicked.connect(lambda _, fp=p: (self.f_path.setText(fp), self._apply_codes_from_file(fp), self.status.setText(f"Открыт: {os.path.basename(fp)}")))
                self._recent_lay.addWidget(b)
        self._recent_lay.addStretch()

    def _apply_codes_from_file(self, path):
        """Load unique Code values from file and set in settings."""
        if not path or not os.path.isfile(path):
            return
        codes = load_codes_from_file(path)
        if codes:
            txt = ",".join(codes)
            self.s_codes.setText(txt)
            self.cfg["connect_codes"] = codes
            save_config(self.cfg)

    def _preview(self):
        p = self.f_path.text().strip()
        if not p or not os.path.isfile(p):
            QMessageBox.warning(self, "Внимание", "Выберите файл.")
            return
        df, err = load_preview(p)
        if err:
            self.preview.setPlainText(f"Ошибка: {err}")
            return
        self._apply_codes_from_file(p)
        cols = list(df.columns)
        hdr = " | ".join(f"{c:>10}" for c in cols)
        sep = "-" * len(hdr)
        rows = [" | ".join(str(r[c])[:10].rjust(10) for c in cols) for _, r in df.head(40).iterrows()]
        self.preview.setPlainText(hdr + "\n" + sep + "\n" + "\n".join(rows))
        self.status.setText(f"Превью: {len(df)} строк")

    def _open_dir(self):
        if self.output_dir and os.path.isdir(self.output_dir):
            os.startfile(self.output_dir) if sys.platform == "win32" else subprocess.run(["xdg-open", self.output_dir])

    def _toggle_theme(self):
        self._dark_theme = not self._dark_theme
        self._apply_theme()
        self.cfg["dark_theme"] = self._dark_theme
        save_config(self.cfg)

    def _apply_theme(self):
        self.setStyleSheet(STYLE_DARK if self._dark_theme else STYLE)
        if hasattr(self, "btn_theme"):
            self.btn_theme.setText("☀️" if self._dark_theme else "🌙")
        if self._dark_theme:
            from PySide6.QtGui import QPalette, QColor
            pal = QApplication.palette()
            pal.setColor(pal.ColorRole.Window, QColor(45, 45, 61))
            pal.setColor(pal.ColorRole.WindowText, QColor(232, 230, 240))
            pal.setColor(pal.ColorRole.Base, QColor(37, 37, 64))
            pal.setColor(pal.ColorRole.Text, QColor(232, 230, 240))
            pal.setColor(pal.ColorRole.Highlight, QColor(107, 91, 149))
            pal.setColor(pal.ColorRole.HighlightedText, QColor(255, 255, 255))
            pal.setColor(pal.ColorRole.ButtonText, QColor(232, 230, 240))
            QApplication.setPalette(pal)
        else:
            from PySide6.QtGui import QPalette
            QApplication.setPalette(QPalette())

    def _get_cfg(self):
        codes = [s.strip() for s in self.s_codes.text().split(",") if s.strip()] or DEFAULTS["connect_codes"].split(",")
        profile = self.s_quality_profile.currentText() if hasattr(self, "s_quality_profile") else "standard"
        try:
            from archaeo.quality import get_quality_profile
            qp = get_quality_profile(profile)
            mzs, mpj, mps = qp.max_z_sigma, qp.max_planar_jump, qp.min_point_spacing
        except Exception:
            mzs, mpj, mps = 3.5, 10.0, 0.2
        kw = [s.strip() for s in self.s_kw.text().split(",") if s.strip()] or ["центр", "center"]
        return {
            "input_path": self.f_path.text().strip(),
            "encoding": None,
            "output_dir": self.s_out.text().strip() or str(ROOT / "output"),
            "source_crs": self.s_crs.text().strip() or "EPSG:3857",
            "target_crs": self.s_crs_t.text().strip() or "EPSG:3857",
            "connect_codes": codes, "center_description_keywords": kw,
            "title": self.s_title.text().strip() or "Archaeological Survey",
            "export_formats": ["gpkg", "geojson"], "annotate_prefixes": ["FIND_"],
            "write_summary": self.cb_sum.isChecked(), "write_quality": self.cb_qual.isChecked(),
            "plots_enabled": self.cb_plot.isChecked(), "interactive_3d": self.cb_3d.isChecked(),
            "basemap": self.cb_map.isChecked(),
            "auto_levels": self.cb_auto_levels.isChecked(),
            "quality_profile": profile,
            "max_z_sigma": mzs, "max_planar_jump": mpj, "min_point_spacing": mps,
        }

    def _apply_cfg(self):
        c = self.cfg
        self.s_crs.setText(c.get("source_crs", ""))
        self.s_crs_t.setText(c.get("target_crs", ""))
        codes = c.get("connect_codes", "")
        self.s_codes.setText(",".join(codes) if isinstance(codes, list) else codes)
        self.s_kw.setText(c.get("center_keywords", "центр,center"))
        self.s_title.setText(c.get("title", ""))
        self.s_out.setText(c.get("output_dir", str(ROOT / "output")))
        self.cb_auto_levels.setChecked(c.get("auto_levels", False))
        if hasattr(self, "s_quality_profile"):
            idx = self.s_quality_profile.findText(c.get("quality_profile", "standard"))
            if idx >= 0:
                self.s_quality_profile.setCurrentIndex(idx)
        self.cb_sum.setChecked(c.get("write_summary", True))
        self.cb_qual.setChecked(c.get("write_quality", True))
        self.cb_plot.setChecked(c.get("plots_enabled", True))
        self.cb_3d.setChecked(c.get("interactive_3d", True))
        self.cb_map.setChecked(c.get("basemap", False))

    def _clear_results(self):
        """Clear previous results, combos, and canvases."""
        self.data_dict = None
        self.output_dir = ""
        for combo in [self.combo_2d, self.combo_3d]:
            combo.blockSignals(True)
            combo.clear()
            combo.addItem("Все")
            combo.blockSignals(False)
        if self._2d_ph.parent() is None:
            self._2d_box.addWidget(self._2d_ph)
        if self._canvas_2d:
            self._canvas_2d.setParent(None)
            self._canvas_2d.deleteLater()
            self._canvas_2d = None
        if self._fig_2d:
            plt.close(self._fig_2d)
            self._fig_2d = None
        if self._3d_ph.parent() is None:
            self._3d_box.addWidget(self._3d_ph)
        if self._canvas:
            self._canvas.setParent(None)
            self._canvas.deleteLater()
            self._canvas = None
        if self._fig3d:
            plt.close(self._fig3d)
            self._fig3d = None
        self._ax3d = None
        self.btn_dir.setEnabled(False)
        self.log.setPlainText("")
        self.status.setText("Готов")

    def _on_run(self):
        cfg = self._get_cfg()
        if not cfg["input_path"]:
            QMessageBox.warning(self, "Внимание", "Выберите входной файл.")
            return
        if not os.path.isfile(cfg["input_path"]):
            QMessageBox.critical(self, "Ошибка", f"Файл не найден:\n{cfg['input_path']}")
            return
        os.makedirs(cfg["output_dir"], exist_ok=True)

        self._clear_results()
        self.progress.setVisible(True)
        self.btn_run.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.btn_dir.setEnabled(False)
        self._stop_flag = False
        self._go(2)
        self.log.setPlainText("Обработка...")
        self.status.setText("Обработка...")

        def work():
            ok, msg, outdir, plan2d, dd = run_pipeline(cfg, stop_check=lambda: self._stop_flag)
            self._signals.finished.emit(ok, msg, outdir, plan2d, dd)
        self._worker = threading.Thread(target=work, daemon=True)
        self._worker.start()

    def _on_stop(self):
        self._stop_flag = True
        self.btn_stop.setEnabled(False)
        self.status.setText("Останавливаем...")
        self.log.setPlainText(self.log.toPlainText() + "\nОстановка...")
        self._clear_results()

    def _done(self, ok, msg, outdir, plan2d, dd):
        self.progress.setVisible(False)
        self.btn_run.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.output_dir = outdir
        self.data_dict = dd
        self.log.setPlainText(msg)
        self.status.setText("Готово!" if ok else "Ошибка")
        self.btn_dir.setEnabled(bool(ok and outdir))

        if ok:
            if dd:
                codes = dd["codes"]
                for combo in [self.combo_2d, self.combo_3d]:
                    combo.blockSignals(True)
                    combo.clear()
                    combo.addItem("Все")
                    combo.addItems(codes)
                    combo.blockSignals(False)
                self._canvas_2d = None
                self._canvas = None
                self._go(2)
                self._rebuild_2d("Все")
            QMessageBox.information(self, "Готово", msg)
            if dd:
                self.status.setText(f"Готово! Раскопы: {', '.join(dd['codes'])}")
        else:
            QMessageBox.critical(self, "Ошибка", msg[:800])

    # ── 2D ──

    def _rebuild_2d(self, code_filter=None):
        if not self.data_dict:
            return
        if code_filter is None:
            code_filter = self.combo_2d.currentText()
        try:
            fig = build_2d_figure(self.data_dict, code_filter, self.s_title.text() or "2D")
            if self._2d_ph.parent():
                self._2d_ph.setParent(None)
            if self._canvas_2d:
                self._canvas_2d.setParent(None)
                self._canvas_2d.deleteLater()
            if self._fig_2d:
                plt.close(self._fig_2d)
            self._fig_2d = fig
            self._canvas_2d = MplCanvas(fig)
            self._2d_box.addWidget(self._canvas_2d)
        except Exception as e:
            self.status.setText(f"2D: {e}")

    # ── 3D ──

    def _on_3d_code(self, v):
        self._rebuild_3d()

    def _on_3d_z(self, v):
        self.z_label.setText("все" if v < 0 else str(v))
        self._rebuild_3d()

    def _toggle_rot(self, state):
        if state:
            self._timer.start(40)
        else:
            self._timer.stop()

    def _rotate(self):
        if self._ax3d and self._canvas:
            self._azim = (self._azim + 0.8) % 360
            self._ax3d.view_init(elev=25, azim=self._azim)
            self._canvas.draw_idle()

    def _rebuild_3d(self):
        if not self.data_dict:
            return
        code_filter = self.combo_3d.currentText()
        z_layer = self.zslider.value()
        z_arg = z_layer if z_layer >= 0 else None
        try:
            fig, ax = build_3d_figure(self.data_dict, code_filter, z_arg, self.s_title.text() or "3D")
            if self._3d_ph.parent():
                self._3d_ph.setParent(None)
            if self._canvas:
                self._canvas.setParent(None)
                self._canvas.deleteLater()
            if self._fig3d:
                plt.close(self._fig3d)
            self._fig3d, self._ax3d = fig, ax
            self._canvas = MplCanvas(fig)
            self._3d_box.addWidget(self._canvas)
            if self.cb_rot.isChecked():
                self._timer.start(40)
        except Exception as e:
            self.status.setText(f"3D: {e}")


# ── main ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setFont(QFont("Segoe UI", 10))
    w = MainWindow()
    w.show()
    sys.exit(app.exec())
