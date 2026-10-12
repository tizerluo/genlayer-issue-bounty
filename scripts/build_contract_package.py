"""Build a reproducible stored ZIP runner containing the exact readable source."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import zipfile
import zlib

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'contracts/issue_bounty_escrow.py'
OUTPUT = ROOT / 'artifacts/issue_bounty_escrow.zip'
RUNNER = 'py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6'
PAYLOAD_PATH = '/issue_bounty_source.zlib'


def package_entries(source: bytes) -> dict[str, bytes]:
    """GenVM ZIP entries are stored; Python decompresses the inner payload."""
    source_hash = hashlib.sha256(source).hexdigest()
    loader = f'''# {{ "Depends": "{RUNNER}" }}
import hashlib as _source_hashing
import zlib as _source_compression

def _load_readable_source():
    with open({PAYLOAD_PATH!r}, 'rb') as payload:
        source = _source_compression.decompress(payload.read())
    if len(source) != {len(source)} or _source_hashing.sha256(source).hexdigest() != {source_hash!r}:
        raise RuntimeError('Contract source integrity check failed')
    exec(compile(source, '/contract.py', 'exec'), globals())

_load_readable_source()
'''
    runner = {'Seq': [
        {'MapFile': {'file': 'source.zlib', 'to': PAYLOAD_PATH}},
        {'Depends': RUNNER},
    ]}
    return {
        'runner.json': json.dumps(runner, separators=(',', ':')).encode(),
        'file': loader.encode(),
        'source.zlib': zlib.compress(source, level=9),
    }


def build_package(source_path: Path = SOURCE) -> bytes:
    """Return deployment bytes without RPC calls or key access."""
    source = source_path.read_bytes()
    source.decode('utf-8')
    output = io.BytesIO()
    with zipfile.ZipFile(output, 'w', compression=zipfile.ZIP_STORED) as archive:
        for name, contents in package_entries(source).items():
            entry = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            entry.compress_type = zipfile.ZIP_STORED
            entry.create_system = 3
            entry.external_attr = 0o100644 << 16
            archive.writestr(entry, contents)
    return output.getvalue()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=SOURCE)
    parser.add_argument('--output', type=Path, default=OUTPUT)
    args = parser.parse_args()
    args.source = args.source.resolve()
    args.output = args.output.resolve()
    source = args.source.read_bytes()
    package = build_package(args.source)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(package)
    def label(path):
        try:
            return str(path.relative_to(ROOT))
        except ValueError:
            return str(path)

    manifest = {
        'source': label(args.source),
        'source_bytes': len(source), 'source_sha256': hashlib.sha256(source).hexdigest(),
        'package': label(args.output),
        'package_bytes': len(package), 'package_sha256': hashlib.sha256(package).hexdigest(),
        'runner': RUNNER, 'zip_compression': 'stored', 'payload_compression': 'zlib',
        'transactions_sent': 0,
    }
    args.output.with_suffix('.package.json').write_text(json.dumps(manifest, indent=2)+'\n')
    print(json.dumps(manifest, indent=2))


if __name__ == '__main__':
    main()
