"""在受限工作区运行官方 linter，不更改 HOME。"""
import sys
from pathlib import Path
from genvm_linter.validate import artifacts
from genvm_linter import stubs
from genvm_linter.cli import cli

cache = Path('/tmp/issue-bounty-genvm')
artifacts.CACHE_DIR = cache
stubs.CACHE_DIR = cache / 'stubs'
if __name__ == '__main__':
    cli()
