"""Update or lint data/presets-default.json

Usage:
  update-presets.py [options]
  update-presets.py list-non-default <preset>
  update-presets.py diff <left> <right>
  update-presets.py (-h | --help)

Options:
  -h, --help         show this help message and exit
  --from=<rev>       update presets to match the given git commit
  --hook             run noninteractively for git pre-commit hook purposes
  --preset=<preset>  only update the named preset
"""

import sys

import json
import platform
import subprocess

import docopt # PyPI: docopt

import SettingsList

if hasattr(SettingsList, 'si_dict'):
    SETTINGS_DICT = SettingsList.si_dict
else:
    SETTINGS_DICT = SettingsList.SettingInfos.setting_infos

def complete_presets(new_presets, interactive, *, preset=None, source=None):
    with open('data/presets_default.json', encoding='utf-8') as f:
        current = json.load(f)
    names = set(current)
    if source is not None:
        names |= set(source)
    for preset_name in sorted(names, key=lambda name: (list(current).index(name) if name in current else len(current), name)):
        if source is None or preset_name not in source or (preset is not None and preset_name != preset):
            old_preset = current[preset_name]
        else:
            old_preset = source[preset_name]
        if preset is not None and preset_name != preset:
            new_presets[preset_name] = old_preset
            continue
        if preset_name not in new_presets:
            new_presets[preset_name] = {}
        SettingsList.validate_settings(new_presets[preset_name], check_conflicts=False)
        for setting_name, setting in SETTINGS_DICT.items():
            if setting.shared and setting_name not in new_presets[preset_name]:
                if setting_name in old_preset:
                    try:
                        new_presets[preset_name][setting_name] = old_preset[setting_name]
                        SettingsList.validate_settings(new_presets[preset_name], check_conflicts=False)
                    except TypeError:
                        if interactive:
                            while True:
                                try:
                                    new_presets[preset_name][setting_name] = json.loads(input(f'{preset_name}[{setting_name}] (previously {json.dumps(old_preset[setting_name])}): ').strip())
                                except json.JSONDecodeError:
                                    continue
                                else:
                                    break
                            SettingsList.validate_settings(new_presets[preset_name], check_conflicts=False)
                        else:
                            raise
                else:
                    if interactive:
                        while True:
                            try:
                                new_presets[preset_name][setting_name] = json.loads(input(f'{preset_name}[{setting_name}]: ').strip())
                            except json.JSONDecodeError:
                                continue
                            else:
                                break
                    else:
                        raise ValueError(f'Missing setting {setting_name!r} in preset {preset_name!r}')

if __name__ == '__main__':
    arguments = docopt.docopt(__doc__)
    new_presets = {}
    if arguments['list-non-default']:
        with open('data/presets_default.json', encoding='utf-8') as f:
            preset = json.load(f)[arguments['<preset>']]
        non_default = {name: value for name, value in preset.items() if value != SETTINGS_DICT[name].default}
        print(json.dumps(non_default, indent=4))
    elif arguments['diff']:
        if arguments['<left>'] == 'default':
            left = {setting_name: setting.default for setting_name, setting in SETTINGS_DICT.items() if setting.shared}
        else:
            with open('data/presets_default.json', encoding='utf-8') as f:
                left = json.load(f)[arguments['<left>']]
        if arguments['<right>'] == 'default':
            right = {setting_name: setting.default for setting_name, setting in SETTINGS_DICT.items() if setting.shared}
        else:
            with open('data/presets_default.json', encoding='utf-8') as f:
                right = json.load(f)[arguments['<right>']]
        with open('left.json', 'w', encoding='utf-8') as left_f:
            json.dump(left, left_f, indent=4)
        with open('right.json', 'w', encoding='utf-8') as right_f:
            json.dump(right, right_f, indent=4)
        diff = ['wsl', 'diff'] if platform.system() == 'Windows' else ['diff']
        sys.exit(subprocess.run([*diff, left_f.name, right_f.name]).returncode)
    elif arguments['--hook']:
        complete_presets(new_presets, False)
        with open('data/presets_default.json', encoding='utf-8') as f:
            if f.read() != json.dumps(new_presets, indent=4) + '\n':
                raise ValueError('presets not formatted correctly, run .\\update-presets.py to fix')
    else:
        if arguments['--from']:
            source = json.loads(subprocess.run(['git', 'show', f'{arguments["--from"]}:data/presets_default.json'], encoding='utf-8', stdout=subprocess.PIPE, check=True).stdout)
        else:
            source = None
        complete_presets(new_presets, True, preset=arguments['--preset'], source=source)
        with open('data/presets_default.json', 'w', encoding='utf-8', newline='\n') as f:
            json.dump(new_presets, f, indent=4)
            print(file=f)
