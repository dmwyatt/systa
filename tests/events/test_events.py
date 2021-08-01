from pytest_mock import MockerFixture

from systa.events.events import IdleCheck


def test_idle_check(mocker: MockerFixture):
    mocked_idle_time_getter = mocker.patch("systa.events.events.get_idle_time")
    mocked_idle_time_getter.return_value = 11
    ic = IdleCheck(10)
    assert ic.check()


# test data taken from model in docs/idle_time_model.xlsx
test_data = [
    (0, -1, False),
    (1, 0.88, False),
    (2, 1.88, False),
    (3, 2.88, False),
    (4, 3.88, False),
    (5, 4.88, False),
    (6, 5.88, True),
    (7, 6.88, True),
    (8, 7.88, False),
    (9, 8.88, False),
    (10, 9.88, False),
    (11, 0.68, False),
    (12, 1.68, False),
    (13, 2.68, False),
    (14, 3.68, False),
    (15, 4.68, False),
    (16, 5.68, True),
    (17, 6.68, True),
    (18, 7.68, False),
    (19, 8.68, False),
    (20, 9.68, False),
    (21, 0.61, False),
    (22, 1.61, False),
    (23, 2.61, False),
    (24, 3.61, False),
    (25, 4.61, False),
    (26, 5.61, True),
    (27, 6.61, True),
    (28, 7.61, False),
]


def test_idle_check_matches_model(mocker: MockerFixture):
    mocked_idle_time_getter = mocker.patch("systa.events.events.get_idle_time")
    mocked_time = mocker.patch("systa.events.events.time.time")

    ic = IdleCheck(5, 2)

    for at_time, user_input_at, expected in test_data:
        mocked_idle_time_getter.return_value = user_input_at
        mocked_time.return_value = at_time
        assert ic.check() is expected, f"({at_time, user_input_at, expected})"
