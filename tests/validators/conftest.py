import sys
from pathlib import Path
from unittest.mock import patch

import pytest

VALIDATOR_DIR = Path(__file__).resolve().parents[2] / ".claude" / "skills" / "lincoln-workflow" / "validators"
sys.path.insert(0, str(VALIDATOR_DIR))

import validate


def run_validator(root: Path, check_name: str, *args):
    """Run a validator exit check with PROJECT_ROOT temporarily patched to root."""
    check_fn = validate.EXIT_CHECKS[check_name]
    with patch.object(validate, "PROJECT_ROOT", root):
        with pytest.raises(SystemExit) as exc_info:
            check_fn(*args)
    return exc_info.value.code
