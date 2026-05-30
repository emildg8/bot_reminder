#!/usr/bin/env python3
"""Записывает git sha текущего деплоя в data/deploy_sha.txt."""

from bot.services.deploy_meta import record_deploy_sha_from_git


def main() -> None:
    sha = record_deploy_sha_from_git()
    if sha:
        print(f"Deploy sha: {sha[:7]}")
    else:
        print("Not a git repo — deploy sha not recorded")


if __name__ == "__main__":
    main()
