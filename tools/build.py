"""Build an installable ZIP with only runtime assets (no Kodi needed)."""
import argparse
from pathlib import Path
import xml.etree.ElementTree as ET
import zipfile


def build(output):
    root = Path(__file__).resolve().parents[1]
    addon = ET.parse(root / 'addon.xml').getroot()
    output.mkdir(parents=True, exist_ok=True)
    target = output / '{}-{}.zip'.format(addon.attrib['id'], addon.attrib['version'])
    files = [root / p for p in ('addon.xml', 'service.py', 'icon.png', 'logo.png', 'README.md')]
    files += [p for p in (root / 'resources').rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix not in ('.pyc', '.pyo')]
    with zipfile.ZipFile(target, 'w', zipfile.ZIP_DEFLATED) as archive:
        for source in sorted(files):
            archive.write(source, addon.attrib['id'] + '/' + source.relative_to(root).as_posix())
    return target


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, default=Path('dist'))
    print(build(parser.parse_args().output))
