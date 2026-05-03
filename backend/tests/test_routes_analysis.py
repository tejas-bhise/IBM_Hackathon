"""
Tests for routes/analysis.py
Covers: _grade(), _recompute_score() — both are pure functions.
No HTTP client or MongoDB needed.
"""
import pytest
from routes.analysis import _grade, _recompute_score


# ── _grade ─────────────────────────────────────────────────────────────────────

class TestGrade:
    def test_100_is_A(self):
        assert _grade(100) == "A"

    def test_90_is_A(self):
        assert _grade(90) == "A"

    def test_89_is_Bplus(self):
        assert _grade(89) == "B+"

    def test_80_is_Bplus(self):
        assert _grade(80) == "B+"

    def test_79_is_B(self):
        assert _grade(79) == "B"

    def test_70_is_B(self):
        assert _grade(70) == "B"

    def test_69_is_C(self):
        assert _grade(69) == "C"

    def test_60_is_C(self):
        assert _grade(60) == "C"

    def test_59_is_D(self):
        assert _grade(59) == "D"

    def test_50_is_D(self):
        assert _grade(50) == "D"

    def test_49_is_F(self):
        assert _grade(49) == "F"

    def test_0_is_F(self):
        assert _grade(0) == "F"

    def test_5_is_F(self):
        assert _grade(5) == "F"

    @pytest.mark.parametrize("score,expected", [
        (100, "A"), (95, "A"), (90, "A"),
        (89, "B+"), (85, "B+"), (80, "B+"),
        (79, "B"),  (75, "B"),  (70, "B"),
        (69, "C"),  (65, "C"),  (60, "C"),
        (59, "D"),  (55, "D"),  (50, "D"),
        (49, "F"),  (25, "F"),  (0,  "F"),
    ])
    def test_all_grade_boundaries(self, score, expected):
        assert _grade(score) == expected


# ── _recompute_score ──────────────────────────────────────────────────────────

class TestRecomputeScore:
    def test_zero_issues_returns_100(self):
        assert _recompute_score(0, 0, 0, 0, 0) == 100

    def test_total_check_independent_of_counts(self):
        # total=0 overrides all counts → must return 100
        assert _recompute_score(0, 0, 0, 0, total=0) == 100

    def test_one_critical_subtracts_25(self):
        # 1 critical: min(65, 1*25) = 25 → 100-25 = 75
        assert _recompute_score(1, 0, 0, 0, 1) == 75

    def test_two_critical(self):
        # 2 critical: min(65, 50) = 50 → 100-50 = 50
        assert _recompute_score(2, 0, 0, 0, 2) == 50

    def test_critical_penalty_capped_at_65(self):
        # 4 critical: 4*25=100 → min(65,100)=65 → 100-65=35
        assert _recompute_score(4, 0, 0, 0, 4) == 35

    def test_one_high_subtracts_15(self):
        # 1 high: min(30, 15) = 15 → 100-15=85
        assert _recompute_score(0, 1, 0, 0, 1) == 85

    def test_two_high(self):
        # 2 high: min(30, 30) = 30 → 100-30=70
        assert _recompute_score(0, 2, 0, 0, 2) == 70

    def test_high_penalty_capped_at_30(self):
        # 3 high: 3*15=45 → min(30,45)=30 → 100-30=70
        assert _recompute_score(0, 3, 0, 0, 3) == 70

    def test_one_medium_subtracts_7(self):
        # 1 medium: min(10, 7) = 7 → 100-7=93
        assert _recompute_score(0, 0, 1, 0, 1) == 93

    def test_medium_penalty_capped_at_10(self):
        # 2 medium: 2*7=14 → min(10,14)=10 → 100-10=90
        assert _recompute_score(0, 0, 2, 0, 2) == 90

    def test_one_low_subtracts_3(self):
        # 1 low: min(5, 3) = 3 → 100-3=97
        assert _recompute_score(0, 0, 0, 1, 1) == 97

    def test_low_penalty_capped_at_5(self):
        # 2 low: 2*3=6 → min(5,6)=5 → 100-5=95
        assert _recompute_score(0, 0, 0, 2, 2) == 95

    def test_combined_penalties(self):
        # 2 critical (50) + 1 high (15) = 65 → 100-65=35
        assert _recompute_score(2, 1, 0, 0, 3) == 35

    def test_score_never_below_5(self):
        # Max penalties: 65+30+10+5=110 → 100-110=-10 → max(5,-10)=5
        score = _recompute_score(4, 3, 2, 2, 11)
        assert score >= 5

    def test_score_never_above_100(self):
        assert _recompute_score(0, 0, 0, 0, 0) <= 100

    def test_floor_is_5_not_0(self):
        # Even with extreme penalties, minimum is 5
        assert _recompute_score(10, 10, 10, 10, 40) == 5
