"""使用私有缓存；拒绝其他属主、符号链接和组/公开权限。"""
import os
import errno
import stat
import tempfile
from pathlib import Path


def _private_directory(path):
    path.mkdir(mode=0o700, parents=True, exist_ok=True)
    info = path.lstat()
    if (not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid()
            or stat.S_IMODE(info.st_mode) != 0o700):
        raise RuntimeError('Cache directory must be owned by this user with mode 0700')
    return path


def private_cache(name):
    configured = os.environ.get('ISSUE_BOUNTY_CACHE_DIR')
    if configured:
        root = _private_directory(Path(configured))
    else:
        try:
            root = _private_directory(Path.home() / '.cache' / 'issue-bounty')
        except OSError as exc:
            if exc.errno not in (errno.EACCES, errno.EROFS):
                raise
            # 只在 HOME 不可写时降级，不绕过属主/权限检查失败。
            root = _private_directory(Path(tempfile.mkdtemp(prefix='issue-bounty-cache-')))
    return _private_directory(root / name)
