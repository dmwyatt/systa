import pytest

from systa.windows import current_windows


def test_getitem():
    with pytest.raises(
            KeyError, match="No window matching title: '🍔'"
    ):
        current_windows["🍔"]

