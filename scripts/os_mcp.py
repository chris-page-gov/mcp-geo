#!/usr/bin/env python3
"""Legacy adapter module now delegating to `server.stdio_adapter`.

Allows console script and direct invocation to remain stable after refactor.
"""
from server.stdio_adapter import main  # re-export

if __name__ == "__main__":  # pragma: no cover
    main()
