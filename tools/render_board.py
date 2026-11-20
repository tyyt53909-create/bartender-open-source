#!/usr/bin/env python3
"""Compatibility entry point for the shared document compiler."""
from render_docs import main
if __name__ == "__main__":
    raise SystemExit(main(only={'docs/coordination-board.md'}))
