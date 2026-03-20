from app.core.condition import ConditionChecker, check_condition, parse_potential_line
from app.models.config import TargetCondition
from app.models.potential import PotentialLine


class TestParsePotentialLine:
    def test_attack_percent(self):
        line = parse_potential_line("攻擊力: +12%")
        assert line.attribute == "攻擊力%"
        assert line.value == 12

    def test_magic_percent(self):
        line = parse_potential_line("魔力: +9%")
        assert line.attribute == "魔力%"
        assert line.value == 9

    def test_boss_damage(self):
        line = parse_potential_line("BOSS傷害: +30%")
        assert line.attribute == "BOSS傷害%"
        assert line.value == 30

    def test_boss_damage_lowercase(self):
        line = parse_potential_line("boss傷害: +20%")
        assert line.attribute == "BOSS傷害%"
        assert line.value == 20

    def test_ignore_defense(self):
        line = parse_potential_line("無視怪物防禦: +15%")
        assert line.attribute == "無視防禦%"
        assert line.value == 15

    def test_ignore_defense_short(self):
        line = parse_potential_line("無視防禦: +10%")
        assert line.attribute == "無視防禦%"
        assert line.value == 10

    def test_total_damage(self):
        line = parse_potential_line("總傷害: +12%")
        assert line.attribute == "總傷害%"
        assert line.value == 12

    def test_crit_damage(self):
        line = parse_potential_line("暴擊傷害: +8%")
        assert line.attribute == "暴擊傷害%"
        assert line.value == 8

    def test_all_stats(self):
        line = parse_potential_line("全屬性: +6%")
        assert line.attribute == "全屬性%"
        assert line.value == 6

    def test_hp_percent(self):
        line = parse_potential_line("HP: +12%")
        assert line.attribute == "HP%"
        assert line.value == 12

    def test_unknown_text(self):
        line = parse_potential_line("某個無法辨識的文字")
        assert line.attribute == "未知"
        assert line.value == 0
        assert line.raw_text == "某個無法辨識的文字"

    def test_no_space_format(self):
        line = parse_potential_line("攻擊力+12%")
        assert line.attribute == "攻擊力%"
        assert line.value == 12

    def test_fullwidth_colon(self):
        line = parse_potential_line("攻擊力：+12%")
        assert line.attribute == "攻擊力%"
        assert line.value == 12

    def test_raw_text_preserved(self):
        text = "攻擊力: +12%"
        line = parse_potential_line(text)
        assert line.raw_text == text


class TestCheckCondition:
    def test_any_attribute_always_matches(self):
        line = PotentialLine("攻擊力%", 5)
        cond = TargetCondition(0, "任意")
        assert check_condition(line, cond) is True

    def test_gte_pass(self):
        line = PotentialLine("攻擊力%", 12)
        cond = TargetCondition(0, "攻擊力%", ">=", 12)
        assert check_condition(line, cond) is True

    def test_gte_fail(self):
        line = PotentialLine("攻擊力%", 9)
        cond = TargetCondition(0, "攻擊力%", ">=", 12)
        assert check_condition(line, cond) is False

    def test_eq_pass(self):
        line = PotentialLine("攻擊力%", 12)
        cond = TargetCondition(0, "攻擊力%", "=", 12)
        assert check_condition(line, cond) is True

    def test_eq_fail(self):
        line = PotentialLine("攻擊力%", 15)
        cond = TargetCondition(0, "攻擊力%", "=", 12)
        assert check_condition(line, cond) is False

    def test_wrong_attribute(self):
        line = PotentialLine("魔力%", 12)
        cond = TargetCondition(0, "攻擊力%", ">=", 12)
        assert check_condition(line, cond) is False

    def test_contains_pass(self):
        line = PotentialLine("未知", 0, raw_text="BOSS傷害: +30%")
        cond = TargetCondition(0, "BOSS", "contains")
        assert check_condition(line, cond) is True

    def test_contains_fail(self):
        line = PotentialLine("未知", 0, raw_text="攻擊力: +12%")
        cond = TargetCondition(0, "BOSS", "contains")
        assert check_condition(line, cond) is False


class TestConditionChecker:
    def test_all_conditions_met(self):
        lines = [
            PotentialLine("攻擊力%", 12),
            PotentialLine("BOSS傷害%", 30),
            PotentialLine("無視防禦%", 15),
        ]
        conditions = [
            TargetCondition(0, "攻擊力%", ">=", 12),
            TargetCondition(1, "BOSS傷害%", ">=", 20),
        ]
        checker = ConditionChecker(conditions)
        assert checker.check(lines) is True

    def test_one_condition_fails(self):
        lines = [
            PotentialLine("攻擊力%", 9),
            PotentialLine("BOSS傷害%", 30),
        ]
        conditions = [
            TargetCondition(0, "攻擊力%", ">=", 12),
            TargetCondition(1, "BOSS傷害%", ">=", 20),
        ]
        checker = ConditionChecker(conditions)
        assert checker.check(lines) is False

    def test_no_conditions_always_true(self):
        lines = [PotentialLine("攻擊力%", 5)]
        checker = ConditionChecker([])
        assert checker.check(lines) is True

    def test_line_index_out_of_range(self):
        lines = [PotentialLine("攻擊力%", 12)]
        conditions = [TargetCondition(2, "攻擊力%", ">=", 12)]
        checker = ConditionChecker(conditions)
        assert checker.check(lines) is False

    def test_empty_lines(self):
        conditions = [TargetCondition(0, "攻擊力%", ">=", 12)]
        checker = ConditionChecker(conditions)
        assert checker.check([]) is False
