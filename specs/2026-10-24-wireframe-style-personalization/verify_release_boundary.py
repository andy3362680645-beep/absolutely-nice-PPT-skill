"""在临时副本验证个人目录排除及违规包拒绝；不读取真实偏好。"""
from pathlib import Path
import argparse
import json
import shutil
import sys
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src import release


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--folder', type=Path)
    parser.add_argument('--zip', type=Path)
    args = parser.parse_args()
    results = []
    original_root = release.ROOT
    with tempfile.TemporaryDirectory(prefix='ppt-preferences-boundary-') as scratch:
        scratch = Path(scratch)
        fake = scratch / 'source'
        public = fake / '.ai/templates/user-preferences.md'
        public.parent.mkdir(parents=True)
        public.write_text('# Empty public template\n', encoding='utf-8')
        private_paths = ['.local/ppt-agent/preferences.md', '.ai/.local/preferences.md']
        for relative in private_paths:
            p = fake / relative
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text('synthetic-private-marker', encoding='utf-8')
        try:
            release.ROOT = fake
            collected = {p.relative_to(fake).as_posix() for p in release._source_files()}
            assert '.ai/templates/user-preferences.md' in collected
            assert not collected.intersection(private_paths)
            assert all(not release._allowed(p) for p in private_paths)
            results.append('private-source-excluded-public-template-retained')
        finally:
            release.ROOT = original_root

        if bool(args.folder) != bool(args.zip):
            raise ValueError('folder与zip须同时提供')
        if args.folder:
            release.verify_release(args.folder, args.zip)
            for index, relative in enumerate(private_paths):
                copied = scratch / f'copy-{index}' / 'ppt-agent'
                shutil.copytree(args.folder, copied)
                p = copied / relative
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text('synthetic-private-marker', encoding='utf-8')
                manifest_file = copied / 'release-manifest.json'
                manifest = json.loads(manifest_file.read_text(encoding='utf-8'))
                manifest['files'].append({'path': relative, 'size': p.stat().st_size,
                                          'sha256': release.sha(p)})
                release.write_json(manifest_file, manifest)
                archive_path = copied.parent / 'tampered.zip'
                with zipfile.ZipFile(archive_path, 'x') as archive:
                    for item in copied.rglob('*'):
                        if item.is_file():
                            archive.write(item, 'ppt-agent/' + item.relative_to(copied).as_posix())
                try:
                    release.verify_release(copied, archive_path)
                except ValueError as exc:
                    assert str(exc) == '不允许的发布文件：' + relative, str(exc)
                    results.append('tampered-package-rejected:' + relative)
                else:
                    raise AssertionError('违规个人目录未被拒绝')
    print(json.dumps({'passed': True, 'checks': results,
                      'scope': '临时合成目录和发行副本；未读取或改写真实个人档案'}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
