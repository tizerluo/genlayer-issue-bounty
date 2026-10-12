"""Verify that deployment bytes restore exactly the reviewed readable source."""
import io
import zipfile
import zlib

import pytest

from scripts.build_contract_package import SOURCE, OUTPUT, PAYLOAD_PATH, build_package


def test_reproducible_stored_package_restores_reviewed_source():
    package = build_package()
    assert package == OUTPUT.read_bytes() == build_package()
    with zipfile.ZipFile(io.BytesIO(package)) as archive:
        assert all(entry.compress_type == zipfile.ZIP_STORED for entry in archive.infolist())
        assert archive.testzip() is None
        assert zlib.decompress(archive.read('source.zlib')) == SOURCE.read_bytes()
    assert len(package) < len(SOURCE.read_bytes())


def test_loader_rejects_substituted_source_before_execution(tmp_path):
    with zipfile.ZipFile(OUTPUT) as archive:
        loader = archive.read('file').decode()
    payload_path = tmp_path / 'source.zlib'
    payload_path.write_bytes(zlib.compress(b"raise AssertionError('Substituted source executed')"))
    loader = loader.replace(repr(PAYLOAD_PATH), repr(str(payload_path)))
    with pytest.raises(RuntimeError, match='Contract source integrity check failed'):
        exec(compile(loader, '<packaged loader>', 'exec'), {})
