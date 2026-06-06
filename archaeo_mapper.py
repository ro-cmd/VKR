import argparse
import os
from pathlib import Path
from typing import List, Optional

from archaeo.config import AppConfig, load_config
from archaeo.crs import transform_gdf
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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Archaeological mapping from total station CSV data.",
    )
    parser.add_argument("--config", default=None, help="Path to config.ini.")
    parser.add_argument("--input", default=None, help="Path(s) to input tables, comma-separated.")
    parser.add_argument("--encoding", default=None, help="CSV encoding override.")
    parser.add_argument("--source-crs", default=None, help="CRS for input coordinates.")
    parser.add_argument("--target-crs", default=None, help="CRS for output coordinates.")
    parser.add_argument("--crs", default=None, help="Set source and target CRS together.")
    parser.add_argument("--output-dir", default=None, help="Output directory.")
    parser.add_argument(
        "--export",
        default=None,
        help="Comma-separated export formats: gpkg, geojson, shp.",
    )
    parser.add_argument(
        "--connect-codes",
        default=None,
        help="Comma-separated codes to connect into lines.",
    )
    parser.add_argument(
        "--annotate-prefixes",
        default=None,
        help="Comma-separated code prefixes to annotate.",
    )
    parser.add_argument("--title", default=None, help="Plot title.")
    parser.add_argument(
        "--plots",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Enable or disable plot generation.",
    )
    parser.add_argument(
        "--basemap",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Enable or disable basemap.",
    )
    parser.add_argument(
        "--basemap-provider",
        default=None,
        help="Basemap provider, e.g. OpenStreetMap.Mapnik.",
    )
    parser.add_argument(
        "--show",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Show plots interactively.",
    )
    parser.add_argument(
        "--interactive-3d",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Write interactive 3D HTML with rotation.",
    )
    parser.add_argument(
        "--summary",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Write summary.csv.",
    )
    parser.add_argument(
        "--quality",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Write quality.json.",
    )
    parser.add_argument("--center-point-id", default=None, help="PointID of excavation center.")
    parser.add_argument("--center-code", default=None, help="Code used for excavation center.")
    parser.add_argument(
        "--center-description-keywords",
        default=None,
        help="Comma-separated keywords to auto-detect center in Description.",
    )
    parser.add_argument("--max-z-sigma", type=float, default=None, help="Z outlier sigma threshold.")
    parser.add_argument("--max-planar-jump", type=float, default=None, help="Max allowed planar jump.")
    parser.add_argument("--min-point-spacing", type=float, default=None, help="Min point spacing.")
    return parser.parse_args()


def _parse_list(value: Optional[str]) -> Optional[List[str]]:
    if value is None:
        return None
    return [item.strip() for item in value.split(",") if item.strip()]


def _default_config() -> AppConfig:
    return AppConfig(
        input_path="",
        encoding=None,
        source_crs="EPSG:3857",
        target_crs="EPSG:3857",
        output_dir="output",
        export_formats=["gpkg", "geojson"],
        connect_codes=["BASE", "STAIN_01", "STAIN_11", "STAIN_12", "STAIN_02", "STAIN_21", "STAIN_22"],
        annotate_prefixes=["FIND_"],
        plot_title="Archaeological Survey",
        plots_enabled=True,
        basemap=False,
        basemap_provider="OpenStreetMap.Mapnik",
        show_plots=False,
        interactive_3d=True,
        write_summary=True,
        write_quality=True,
        center_point_id=None,
        center_code=None,
        center_description_keywords=["центр", "center"],
        max_z_sigma=3.5,
        max_planar_jump=5.0,
        min_point_spacing=0.2,
    )


def _apply_overrides(cfg: AppConfig, args: argparse.Namespace) -> AppConfig:
    if args.input:
        cfg.input_path = args.input
    if args.encoding is not None:
        cfg.encoding = args.encoding
    if args.crs:
        cfg.source_crs = args.crs
        cfg.target_crs = args.crs
    if args.source_crs:
        cfg.source_crs = args.source_crs
    if args.target_crs:
        cfg.target_crs = args.target_crs
    if args.output_dir:
        cfg.output_dir = args.output_dir
    if args.export is not None:
        cfg.export_formats = _parse_list(args.export) or []
    if args.connect_codes is not None:
        cfg.connect_codes = _parse_list(args.connect_codes) or []
    if args.annotate_prefixes is not None:
        cfg.annotate_prefixes = _parse_list(args.annotate_prefixes) or []
    if args.title is not None:
        cfg.plot_title = args.title
    if args.plots is not None:
        cfg.plots_enabled = args.plots
    if args.basemap is not None:
        cfg.basemap = args.basemap
    if args.basemap_provider is not None:
        cfg.basemap_provider = args.basemap_provider
    if args.show is not None:
        cfg.show_plots = args.show
    if args.interactive_3d is not None:
        cfg.interactive_3d = args.interactive_3d
    if args.summary is not None:
        cfg.write_summary = args.summary
    if args.quality is not None:
        cfg.write_quality = args.quality
    if args.center_point_id is not None:
        cfg.center_point_id = args.center_point_id
    if args.center_code is not None:
        cfg.center_code = args.center_code
    if args.center_description_keywords is not None:
        cfg.center_description_keywords = _parse_list(args.center_description_keywords) or []
    if args.max_z_sigma is not None:
        cfg.max_z_sigma = args.max_z_sigma
    if args.max_planar_jump is not None:
        cfg.max_planar_jump = args.max_planar_jump
    if args.min_point_spacing is not None:
        cfg.min_point_spacing = args.min_point_spacing
    return cfg


def main() -> int:
    args = parse_args()
    cfg = load_config(args.config) if args.config else _default_config()
    cfg = _apply_overrides(cfg, args)

    if not cfg.input_path:
        raise SystemExit("Input CSV path is required. Use --input or config.ini.")

    input_paths = _parse_list(cfg.input_path) or [cfg.input_path]
    data = load_surveys(input_paths, source_crs=cfg.source_crs, encoding=cfg.encoding)
    data.gdf, data.crs = transform_gdf(data.gdf, cfg.target_crs)
    data.gdf = expand_excavation_stages(data.gdf)
    data.df["E"] = data.gdf.geometry.x
    data.df["N"] = data.gdf.geometry.y
    data.df["Code"] = data.gdf["Code"].values
    data.df["PointID"] = data.gdf["PointID"].values

    center_row = find_center_point(
        data.gdf,
        center_point_id=cfg.center_point_id,
        center_code=cfg.center_code,
        description_keywords=cfg.center_description_keywords,
    )
    lines_gdf = build_lines(data.gdf, cfg.connect_codes, center_row=center_row, close_loop=True)
    planes_gdf = build_planes(data.gdf, cfg.connect_codes, center_row=center_row)
    export_points(data.gdf, cfg.output_dir, cfg.export_formats, crs=data.crs)
    export_lines(lines_gdf, cfg.output_dir, cfg.export_formats)
    export_planes(planes_gdf, cfg.output_dir, cfg.export_formats)
    load_report_path = write_load_report(
        data.load_report,
        cfg.output_dir,
        relativize_base=Path(cfg.output_dir).parent,
    )

    summary_path = None
    quality_report_obj = None
    issues = None
    if cfg.write_summary:
        summary_path = write_summary(data.df, cfg.output_dir)

    if cfg.write_quality:
        qc_cfg = QualityConfig(
            max_z_sigma=cfg.max_z_sigma,
            max_planar_jump=cfg.max_planar_jump,
            min_point_spacing=cfg.min_point_spacing,
        )
        quality_report_obj = build_quality_report(data.df, cfg.connect_codes, qc_cfg)
        write_quality_report(quality_report_obj, cfg.output_dir)
        issues = build_quality_issues(data.df, cfg.connect_codes, qc_cfg)
        write_quality_issues_report(issues, cfg.output_dir)

    if cfg.write_summary and cfg.write_quality and quality_report_obj is not None and issues is not None:
        from dataclasses import asdict
        issues_df = quality_issues_to_dataframe(issues)
        write_excel_reports(
            data.df,
            asdict(quality_report_obj),
            issues_df if not issues_df.empty else None,
            cfg.output_dir,
        )

    if cfg.plots_enabled:
        plan_path = os.path.join(cfg.output_dir, "plan_2d.png")
        plot_plan(
            data.gdf,
            lines_gdf,
            planes_gdf,
            center_row,
            plan_path,
            cfg.plot_title,
            cfg.annotate_prefixes,
            cfg.basemap,
            cfg.basemap_provider,
            cfg.show_plots,
        )
        plot_3d(
            data.gdf,
            lines_gdf,
            planes_gdf,
            center_row,
            os.path.join(cfg.output_dir, "plan_3d.png"),
            f"{cfg.plot_title} (3D)",
            cfg.show_plots,
        )
        if cfg.interactive_3d:
            plot_3d_interactive(
                data.gdf,
                lines_gdf,
                planes_gdf,
                center_row,
                os.path.join(cfg.output_dir, "plan_3d_interactive.html"),
                f"{cfg.plot_title} (3D Interactive)",
            )
        plot_vertical_sections(
            data.gdf,
            center_row,
            os.path.join(cfg.output_dir, "sections_2d.png"),
            cfg.plot_title,
        )
        export_plan_2d_map(
            data.gdf,
            lines_gdf,
            cfg.output_dir,
            title=cfg.plot_title,
        )
        export_plan_2d_map_leaflet(
            data.gdf,
            lines_gdf,
            planes_gdf,
            cfg.output_dir,
            title=cfg.plot_title,
        )

    plan_2d_path = os.path.join(cfg.output_dir, "plan_2d.png") if cfg.plots_enabled and os.path.isfile(os.path.join(cfg.output_dir, "plan_2d.png")) else None
    try:
        from dataclasses import asdict
        qd = asdict(quality_report_obj) if quality_report_obj else None
        generate_pdf_report(data.gdf, planes_gdf, cfg.output_dir, title=cfg.plot_title, plan_2d_path=plan_2d_path, quality_report=qd)
    except Exception:
        pass

    print("Done.")
    print(f"Rows: {len(data.df)}")
    print(f"Input tables: {len(data.source_files)}")
    print(f"Load report: {load_report_path}")
    if summary_path:
        print(f"Summary: {summary_path}")
    if center_row is not None:
        print(f"Center point: PointID={center_row['PointID']}, Code={center_row['Code']}")
    print(f"CRS: {data.crs}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
