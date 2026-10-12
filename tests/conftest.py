"""仅把官方 SDK 下载缓存移到可写目录。"""
from pathlib import Path
from gltest.direct import sdk_loader
import pytest

sdk_loader.CACHE_DIR = Path('/tmp/issue-bounty-genvm')

@pytest.fixture
def replay_validator(direct_vm, monkeypatch):
    """0.29.2 缺少 Sandbox 实现；仅在测试中执行相同函数，不伪造投票。"""
    def replay(**kwargs):
        from genlayer import gl
        def sandbox(fn, *, allow_write_ops=False):
            try:
                return gl.vm.Return(fn())
            except gl.vm.UserError as exc:
                return exc
            except Exception as exc:
                return gl.vm.VMError(str(exc))
        monkeypatch.setattr(gl.vm, 'spawn_sandbox', sandbox)
        previous = direct_vm._in_nondet
        direct_vm._in_nondet = True
        try:
            return direct_vm.run_validator(**kwargs)
        finally:
            direct_vm._in_nondet = previous
    return replay
