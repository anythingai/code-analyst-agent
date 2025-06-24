from __future__ import annotations

import os

# Allow stubbed external service behaviour during unit tests
os.environ.setdefault("ALLOW_STUB", "1") 