"""Build an installable ZIP with only runtime assets (no Kodi needed)."""
import argparse
import shutil
from pathlib import Path
import xml.etree.ElementTree as ET
import zipfile


def runtime_files(root):
    files = [root / p for p in ('addon.xml', 'service.py', 'icon.png',
                                'LICENSE.txt', 'notice.txt', 'README.md')]
    files += [p for p in (root / 'resources').rglob('*')
              if p.is_file() and '__pycache__' not in p.parts
              and p.suffix not in ('.pyc', '.pyo')]
    return sorted(files)


def build(output, stage=None):
    root = Path(__file__).resolve().parents[1]
    addon = ET.parse(root / 'addon.xml').getroot()
    output.mkdir(parents=True, exist_ok=True)
    target = output / '{}-{}.zip'.format(addon.attrib['id'], addon.attrib['version'])
    files = runtime_files(root)
    if stage is not None:
        folder = stage / addon.attrib['id']
        # A new staging folder avoids retaining deleted files from an older build.
        folder.mkdir(parents=True, exist_ok=False)
        for source in files:
            destination = folder / source.relative_to(root)
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, destination)
            destination.chmod(0o644)
    with zipfile.ZipFile(target, 'w', zipfile.ZIP_DEFLATED) as archive:
        for source in files:
            info = zipfile.ZipInfo(addon.attrib['id'] + '/' + source.relative_to(root).as_posix())
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, source.read_bytes())
    return target


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, default=Path('dist'))
    parser.add_argument('--stage', type=Path, help='Create a new runtime directory for the official checker')
    args = parser.parse_args()
    print(build(args.output, args.stage))
