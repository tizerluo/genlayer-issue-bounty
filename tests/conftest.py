"""仅把官方 SDK 下载缓存移到可写目录。"""
from gltest.direct import sdk_loader
import pytest
from scripts.cache_paths import private_cache

# 0.29.2 的清理逻辑用路径子串识别 SDK，因此保留 gltest-direct。
sdk_loader.CACHE_DIR = private_cache('gltest-direct')

@pytest.fixture
def direct_deploy(direct_deploy):
    """使用与 Depends 探针一致的官方版本，不依赖共享缓存或 latest。"""
    def deploy(*args, **kwargs):
        kwargs.setdefault('sdk_version', 'v0.2.12')
        return direct_deploy(*args, **kwargs)
    return deploy

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
