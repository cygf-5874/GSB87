#!/usr/bin/env bash
# 固定验收入口：校验 review/REVIEW.md 的格式、可执行证据、对 8 条对外保证的覆盖，
# 并核对不可改文件的 SHA-256 基线与文件清单。**别改这个文件。**
# 用法：bash scripts/check.sh [-list] [--only <组名>]
set -uo pipefail

cd "$(dirname "$0")/.."

exec python3 check/check.py "$@"
