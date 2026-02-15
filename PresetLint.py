from __future__ import annotations

import argparse
import copy
import json
import sys
from typing import Any

from Settings import Settings
from SettingsList import SettingInfos, validate_settings
from Utils import data_path

MAINTAINED_PRESETS = (
    "Triforce Blitz S4",
    "Triforce Blitz S4 Co-op",
)


def _load_presets() -> dict[str, dict[str, Any]]:
    with open(data_path("presets_default.json"), encoding="utf-8") as f:
        return json.load(f)


def _effective_preset(raw_preset: dict[str, Any]) -> dict[str, Any]:
    settings = Settings(copy.deepcopy(raw_preset), strict=False)
    settings.remove_disabled()
    return settings.to_json()


def _diff_raw_vs_effective(raw_preset: dict[str, Any], effective_preset: dict[str, Any]) -> tuple[dict[str, tuple[Any, Any]], list[str]]:
    changed: dict[str, tuple[Any, Any]] = {}
    removed: list[str] = []
    for key, raw_value in raw_preset.items():
        info = SettingInfos.setting_infos.get(key)
        if info is None or not info.shared:
            continue
        if key not in effective_preset:
            removed.append(key)
        else:
            effective_value = effective_preset[key]
            if raw_value != effective_value:
                changed[key] = (raw_value, effective_value)
    return changed, removed


def lint_presets(presets_to_check: list[str]) -> int:
    all_presets = _load_presets()
    exit_code = 0

    for preset_name in presets_to_check:
        raw_preset = all_presets.get(preset_name)
        if raw_preset is None:
            print(f"[ERROR] Missing preset: {preset_name}", file=sys.stderr)
            exit_code = 1
            continue

        try:
            validate_settings(raw_preset, check_conflicts=False)
        except Exception as ex:
            print(f"[ERROR] {preset_name}: validation failed with check_conflicts=False: {ex}", file=sys.stderr)
            exit_code = 1
            continue

        effective_preset = _effective_preset(raw_preset)
        changed, removed = _diff_raw_vs_effective(raw_preset, effective_preset)

        print(f"== {preset_name} ==")
        if not changed and not removed:
            print("No raw/effective differences.")
            continue
        if changed:
            print("Changed settings (raw -> effective):")
            for key in sorted(changed):
                raw_value, effective_value = changed[key]
                print(f"  {key}: {raw_value!r} -> {effective_value!r}")
        if removed:
            print("Removed settings (disabled after dependency resolution):")
            for key in sorted(removed):
                print(f"  {key}")

    return exit_code


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate presets and report raw-vs-effective setting differences after remove_disabled()."
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Validate all presets for schema (check_conflicts=False). Raw/effective diffs are still reported only for selected presets.",
    )
    parser.add_argument(
        "--preset",
        action="append",
        dest="presets",
        help="Preset name to report. Can be provided multiple times. Defaults to maintained Triforce Blitz presets.",
    )
    args = parser.parse_args()

    all_presets = _load_presets()
    if args.all:
        for preset_name, preset in all_presets.items():
            try:
                validate_settings(preset, check_conflicts=False)
            except Exception as ex:
                print(f"[ERROR] {preset_name}: validation failed with check_conflicts=False: {ex}", file=sys.stderr)
                return 1

    presets_to_check = args.presets if args.presets else list(MAINTAINED_PRESETS)
    return lint_presets(presets_to_check)


if __name__ == "__main__":
    raise SystemExit(main())
