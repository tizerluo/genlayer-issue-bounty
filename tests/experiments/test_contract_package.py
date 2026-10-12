"""Verify that deployment bytes restore exactly the reviewed readable source."""
import io
import zipfile
import zlib

import pytest

from scripts.build_contract_package import SOURCE, OUTPUT, PAYLOAD_PATH, build_package, verify_package


def test_stored_package_restores_reviewed_source():
    package = build_package()
    verify_package(package)
    verify_package(OUTPUT.read_bytes())
    with zipfile.ZipFile(io.BytesIO(package)) as archive:
        assert all(entry.compress_type == zipfile.ZIP_STORED for entry in archive.infolist())
        assert archive.testzip() is None
        assert zlib.decompress(archive.read('source.zlib')) == SOURCE.read_bytes()
    assert len(package) < len(SOURCE.read_bytes())


def test_semantic_verification_accepts_alternative_zlib_bytes():
    with zipfile.ZipFile(OUTPUT) as archive:
        entries = {name: archive.read(name) for name in archive.namelist()}
    entries['source.zlib'] = zlib.compress(SOURCE.read_bytes(), level=1)
    alternative = io.BytesIO()
    with zipfile.ZipFile(alternative, 'w', compression=zipfile.ZIP_STORED) as archive:
        for name, data in entries.items():
            archive.writestr(name, data)
    assert alternative.getvalue() != OUTPUT.read_bytes()
    verify_package(alternative.getvalue())


@pytest.mark.parametrize('entry,contents', [('file', b'pass'), ('runner.json', b'{}'),
                                         ('source.zlib', zlib.compress(b'pass'))])
def test_semantic_verification_rejects_substitution(entry, contents):
    altered = io.BytesIO()
    with zipfile.ZipFile(OUTPUT) as original, zipfile.ZipFile(altered, 'w') as archive:
        for name in original.namelist():
            archive.writestr(name, contents if name == entry else original.read(name))
    with pytest.raises(RuntimeError, match='mismatch'):
        verify_package(altered.getvalue())


def test_semantic_verification_rejects_compressed_zip_entries():
    altered = io.BytesIO()
    with zipfile.ZipFile(OUTPUT) as original, zipfile.ZipFile(altered, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
        for name in original.namelist():
            archive.writestr(name, original.read(name))
    with pytest.raises(RuntimeError, match='stored ZIP'):
        verify_package(altered.getvalue())


def test_loader_rejects_substituted_source_before_execution(tmp_path):
    with zipfile.ZipFile(OUTPUT) as archive:
        loader = archive.read('file').decode()
    payload_path = tmp_path / 'source.zlib'
    payload_path.write_bytes(zlib.compress(b"raise AssertionError('Substituted source executed')"))
    loader = loader.replace(repr(PAYLOAD_PATH), repr(str(payload_path)))
    with pytest.raises(RuntimeError, match='Contract source integrity check failed'):
        exec(compile(loader, '<packaged loader>', 'exec'), {})
