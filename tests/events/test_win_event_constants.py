import pytest

from systa.events.constants import win_events, win_obj_ids


class TestWinEvents:
    event_names = [attr for attr in dir(win_events) if win_events._is_event_attr(attr)]
    event_items = [
        (event_name, getattr(win_events, event_name)) for event_name in event_names
    ]

    def test_is_windows_internal_title_on_non_internal_title(self):
        assert win_events.is_windows_internal_title("Microsoft Word") is False

    def test_is_windows_internal_title_on_internal_title(self):
        assert win_events.is_windows_internal_title("OLEChannelWnd")

    def test_is_windows_internal_title_on_wildcard_internal_title(self):
        assert win_events.is_windows_internal_title("System Clock, 4:11 PM")

    def test_values_contains_event_values(self):
        assert set(getattr(win_events, attr) for attr in self.event_names) == set(
            win_events.values()
        )

    def test_keys_contains_event_names(self):
        assert set(self.event_names) == set(win_events.keys())

    @pytest.mark.parametrize("test_input,expected", event_items)
    def test_get_gets_by_event_name(self, test_input, expected):
        assert win_events.get(test_input) == expected

    @pytest.mark.parametrize("expected,test_input", event_items)
    def test_get_gets_by_event_value(self, expected, test_input):
        assert win_events.get(test_input) == expected

    def test_items_gets_name_value_pairs(self):
        assert sorted(list(win_events.items())) == sorted(self.event_items)

    def test_is_valid_range_checks_invalid_range_item_length(self):
        assert (
            win_events.is_valid_range(
                (
                    win_events.EVENT_SYSTEM_MOVESIZEEND,
                    win_events.EVENT_SYSTEM_MOVESIZESTART,
                    win_events.EVENT_OBJECT_CLOAKED,
                )
            )
            is False
        )

    def test_is_valid_range_checks_items_in_correct_order(self):
        assert (
            win_events.is_valid_range(
                (
                    win_events.EVENT_SYSTEM_MOVESIZEEND,
                    win_events.EVENT_SYSTEM_MOVESIZESTART,
                )
            )
            is False
        )

    def test_is_valid_range_checks_items_are_valid_values(self):
        assert (
            win_events.is_valid_range(
                (win_events.EVENT_SYSTEM_MOVESIZESTART, 9999999999)
            )
        ) is False

    def test_can_iter_event_names(self):
        assert sorted(list(win_events)) == sorted(self.event_names)

    @pytest.mark.parametrize("test_input,expected", event_items)
    def test_getitem_gets_by_event_name(self, test_input, expected):
        assert win_events[test_input] == expected

    @pytest.mark.parametrize("expected,test_input", event_items)
    def test_getitem_gets_by_event_value(self, expected, test_input):
        assert win_events[test_input] == expected

    @pytest.mark.parametrize("test_input", [x[1] for x in event_items])
    def test_contains_values(self, test_input):
        assert test_input in win_events


class TestObjIds:
    object_names = [
        attr for attr in dir(win_obj_ids) if win_obj_ids._is_object_id(attr)
    ]
    object_items = [
        (obj_name, getattr(win_obj_ids, obj_name)) for obj_name in object_names
    ]

    def test_values_is_obj_values(self):
        assert sorted(
            getattr(win_obj_ids, obj_name) for obj_name in self.object_names
        ) == sorted(win_obj_ids.values())

    def test_keys_is_obj_names(self):
        assert sorted(self.object_names) == sorted(win_obj_ids.keys())

    @pytest.mark.parametrize("test_input,expected", object_items)
    def test_get_gets_by_obj_name(self, test_input, expected):
        assert win_obj_ids.get(test_input) == expected

    @pytest.mark.parametrize("expected,test_input", object_items)
    def test_get_gets_by_obj_value(self, expected, test_input):
        assert win_obj_ids.get(test_input) == expected

    def test_can_iter_obj_names(self):
        assert sorted(list(win_obj_ids)) == sorted(self.object_names)

    @pytest.mark.parametrize("test_input,expected", object_items)
    def test_getitem_gets_by_obj_name(self, test_input, expected):
        assert win_obj_ids[test_input] == expected

    @pytest.mark.parametrize("expected,test_input", object_items)
    def test_getitem_gets_by_obj_value(self, expected, test_input):
        assert win_obj_ids[test_input] == expected

    @pytest.mark.parametrize("test_input", [x[1] for x in object_items])
    def test_contains_values(self, test_input):
        assert test_input in win_obj_ids
