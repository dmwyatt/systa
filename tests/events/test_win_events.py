from uuid import uuid4

import pytest

from systa.events.constants import win_events
from systa.events.store import callback_store


class TestCallbackStore:
    @classmethod
    def teardown_class(cls):
        callback_store.unregister_hooks()

    def test_enforces_range_set_item(self):
        bad_key = "no good"
        with pytest.raises(
            AssertionError, match="Can only set a tuple of ints of length 2."
        ):
            callback_store[bad_key] = "not going to work"

    def test_sets_to_list_of_one(self):
        fake_cb = "I R NOT A CALLBACK"
        callback_store[win_events.ALL_EVENTS_RANGE] = fake_cb
        assert callback_store[win_events.ALL_EVENTS_RANGE] == [fake_cb]

    def test_not_exists_item_defaults_to_list(self):
        assert callback_store[uuid4()] == []

    def test_iterates_event_ranges(self):
        callback_store[win_events.ALL_EVENTS_RANGE] = "NOT A CALLBACK"
        callback_store[win_events.ALL_AIA_EVENTS_RANGE] = "ALSO NOT A CALLBACK"

        for rng in callback_store:
            assert rng[0] in [
                win_events.ALL_AIA_EVENTS_RANGE,
                win_events.ALL_EVENTS_RANGE,
            ]
