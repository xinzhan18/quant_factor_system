"""Tests for research.domain.sample_policy."""

from datetime import date

import pytest

from research.domain.sample_policy import SamplePolicy, SupportWindow, ValidationWindow


class TestValidationWindow:
    def test_basic_construction(self):
        w = ValidationWindow(
            window_id="seg_a",
            start=date(2019, 1, 1),
            end=date(2021, 12, 31),
            label="First half",
        )
        assert w.window_id == "seg_a"
        assert w.days == (date(2021, 12, 31) - date(2019, 1, 1)).days

    def test_invalid_range_raises(self):
        with pytest.raises(ValueError, match="before end"):
            ValidationWindow(
                window_id="bad",
                start=date(2022, 1, 1),
                end=date(2021, 12, 31),
            )

    def test_same_start_end_raises(self):
        with pytest.raises(ValueError, match="before end"):
            ValidationWindow(
                window_id="bad",
                start=date(2022, 1, 1),
                end=date(2022, 1, 1),
            )

    def test_frozen(self):
        w = ValidationWindow(
            window_id="seg_a",
            start=date(2019, 1, 1),
            end=date(2021, 12, 31),
        )
        with pytest.raises(AttributeError):
            w.window_id = "changed"


class TestSupportWindow:
    def test_basic_construction(self):
        w = SupportWindow(
            window_id="support_1",
            start=date(2022, 1, 1),
            end=date(2023, 6, 30),
            weight=0.5,
        )
        assert w.weight == 0.5
        assert w.days > 0

    def test_invalid_range_raises(self):
        with pytest.raises(ValueError, match="before end"):
            SupportWindow(
                window_id="bad",
                start=date(2023, 6, 30),
                end=date(2022, 1, 1),
            )


class TestSamplePolicy:
    def test_default_policy(self):
        policy = SamplePolicy.default()
        assert policy.validation_window_id == "std_2024"
        assert policy.train_start == date(2015, 1, 1)
        assert policy.train_end == date(2023, 12, 31)
        assert policy.validation_start == date(2024, 1, 1)
        assert policy.validation_end == date(2024, 12, 31)
        assert policy.holdout_used is False

    def test_validation_after_train(self):
        with pytest.raises(ValueError, match="after train"):
            SamplePolicy(
                validation_window_id="bad",
                data_start=date(2015, 1, 1),
                active_train_range=(date(2015, 1, 1), date(2024, 6, 30)),
                active_validation_range=(date(2024, 1, 1), date(2024, 12, 31)),
            )

    def test_train_range_ordering(self):
        with pytest.raises(ValueError, match="Train range"):
            SamplePolicy(
                validation_window_id="bad",
                data_start=date(2015, 1, 1),
                active_train_range=(date(2023, 12, 31), date(2015, 1, 1)),
                active_validation_range=(date(2024, 1, 1), date(2024, 12, 31)),
            )

    def test_validation_range_ordering(self):
        with pytest.raises(ValueError, match="Validation range"):
            SamplePolicy(
                validation_window_id="bad",
                data_start=date(2015, 1, 1),
                active_train_range=(date(2015, 1, 1), date(2023, 12, 31)),
                active_validation_range=(date(2024, 12, 31), date(2024, 1, 1)),
            )

    def test_holdout_after_validation(self):
        with pytest.raises(ValueError, match="Holdout start"):
            SamplePolicy(
                validation_window_id="bad",
                data_start=date(2015, 1, 1),
                active_train_range=(date(2015, 1, 1), date(2023, 12, 31)),
                active_validation_range=(date(2024, 1, 1), date(2024, 12, 31)),
                holdout_pool_range=(date(2024, 6, 1), date(2025, 12, 31)),
            )

    def test_with_support_windows(self):
        sw = SupportWindow(
            window_id="support_2023",
            start=date(2023, 1, 1),
            end=date(2023, 12, 31),
        )
        policy = SamplePolicy(
            validation_window_id="test",
            data_start=date(2015, 1, 1),
            active_train_range=(date(2015, 1, 1), date(2023, 12, 31)),
            active_validation_range=(date(2024, 1, 1), date(2024, 12, 31)),
            support_validation_windows=[sw],
        )
        assert len(policy.support_validation_windows) == 1

    def test_frozen(self):
        policy = SamplePolicy.default()
        with pytest.raises(AttributeError):
            policy.holdout_used = True
