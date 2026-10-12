#!/usr/bin/env bash
set -euo pipefail
# 使用独立 RC SDK 环境；密码和私钥不会作为 shell 参数传递。
cd "$(dirname "$0")/.."
exec .network-venv/bin/python scripts/deploy_bradbury.py "$@"
