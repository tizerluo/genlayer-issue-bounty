"""在受限工作区运行官方 linter，不更改 HOME。"""
from cache_paths import private_cache
from genvm_linter.validate import artifacts
from genvm_linter import stubs
from genvm_linter.cli import cli

cache = private_cache('genvm')
artifacts.CACHE_DIR = cache
stubs.CACHE_DIR = private_cache('genvm-stubs')
if __name__ == '__main__':
    cli()
