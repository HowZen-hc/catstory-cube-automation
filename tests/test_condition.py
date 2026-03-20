from app.core.condition import ConditionChecker, parse_potential_line
from app.models.config import AppConfig
from app.models.potential import PotentialLine


class TestParsePotentialLine:
    def test_str_percent(self):
        line = parse_potential_line("STR +9%")
        assert line.attribute == "STR%"
        assert line.value == 9

    def test_dex_percent(self):
        line = parse_potential_line("DEX +7%")
        assert line.attribute == "DEX%"
        assert line.value == 7

    def test_int_percent(self):
        line = parse_potential_line("INT +8%")
        assert line.attribute == "INT%"
        assert line.value == 8

    def test_luk_percent(self):
        line = parse_potential_line("LUK +6%")
        assert line.attribute == "LUK%"
        assert line.value == 6

    def test_all_stats(self):
        line = parse_potential_line("全屬性 +7%")
        assert line.attribute == "全屬性%"
        assert line.value == 7

    def test_maxhp(self):
        line = parse_potential_line("MaxHP +12%")
        assert line.attribute == "MaxHP%"
        assert line.value == 12

    def test_physical_attack(self):
        line = parse_potential_line("物理攻擊力 +13%")
        assert line.attribute == "物理攻擊力%"
        assert line.value == 13

    def test_magic_attack(self):
        line = parse_potential_line("魔法攻擊力 +12%")
        assert line.attribute == "魔法攻擊力%"
        assert line.value == 12

    def test_crit_damage(self):
        line = parse_potential_line("爆擊傷害 +3%")
        assert line.attribute == "爆擊傷害%"
        assert line.value == 3

    def test_crit_damage_1(self):
        line = parse_potential_line("爆擊傷害 +1%")
        assert line.attribute == "爆擊傷害%"
        assert line.value == 1

    def test_final_damage(self):
        line = parse_potential_line("最終傷害：+20%")
        assert line.attribute == "最終傷害%"
        assert line.value == 20

    def test_buff_duration(self):
        line = parse_potential_line("加持技能持續時間：+55%")
        assert line.attribute == "加持技能持續時間%"
        assert line.value == 55

    def test_passive_skill_2(self):
        line = parse_potential_line("依照被動技能 2 來增加")
        assert line.attribute == "被動技能2"
        assert line.value == 0

    def test_passive_skill_2_no_space(self):
        line = parse_potential_line("依照被動技能2來增加")
        assert line.attribute == "被動技能2"
        assert line.value == 0

    def test_unknown_text(self):
        line = parse_potential_line("道具掉落率 +20%")
        assert line.attribute == "未知"
        assert line.value == 0

    def test_flat_value_not_matched(self):
        line = parse_potential_line("STR +21")
        assert line.attribute == "未知"
        assert line.value == 0

    def test_fullwidth_colon(self):
        line = parse_potential_line("STR：+9%")
        assert line.attribute == "STR%"
        assert line.value == 9

    def test_no_space(self):
        line = parse_potential_line("STR+9%")
        assert line.attribute == "STR%"
        assert line.value == 9

    def test_raw_text_preserved(self):
        text = "STR +9%"
        line = parse_potential_line(text)
        assert line.raw_text == text


class TestConditionCheckerArmor250:
    """永恆裝備 STR 含全屬性"""

    def _make_checker(self, include_all=True):
        config = AppConfig(
            equipment_type="永恆裝備·光輝套裝 (250+)",
            target_attribute="STR",
            include_all_stats=include_all,
        )
        return ConditionChecker(config)

    def test_all_str(self):
        checker = self._make_checker()
        lines = [
            PotentialLine("STR%", 9),
            PotentialLine("STR%", 7),
            PotentialLine("STR%", 7),
        ]
        assert checker.check(lines) is True

    def test_str_with_all_stats(self):
        checker = self._make_checker()
        lines = [
            PotentialLine("STR%", 9),
            PotentialLine("全屬性%", 6),
            PotentialLine("STR%", 7),
        ]
        assert checker.check(lines) is True

    def test_all_all_stats(self):
        checker = self._make_checker()
        lines = [
            PotentialLine("全屬性%", 7),
            PotentialLine("全屬性%", 6),
            PotentialLine("全屬性%", 6),
        ]
        assert checker.check(lines) is True

    def test_line1_too_low(self):
        checker = self._make_checker()
        lines = [
            PotentialLine("STR%", 7),  # S潛 needs >= 9
            PotentialLine("STR%", 7),
            PotentialLine("STR%", 7),
        ]
        assert checker.check(lines) is False

    def test_line2_too_low(self):
        checker = self._make_checker()
        lines = [
            PotentialLine("STR%", 9),
            PotentialLine("STR%", 6),  # 罕見 needs >= 7
            PotentialLine("STR%", 7),
        ]
        assert checker.check(lines) is False

    def test_without_all_stats(self):
        checker = self._make_checker(include_all=False)
        lines = [
            PotentialLine("STR%", 9),
            PotentialLine("全屬性%", 6),  # not accepted
            PotentialLine("STR%", 7),
        ]
        assert checker.check(lines) is False

    def test_wrong_attribute(self):
        checker = self._make_checker()
        lines = [
            PotentialLine("STR%", 9),
            PotentialLine("DEX%", 7),  # wrong attribute
            PotentialLine("STR%", 7),
        ]
        assert checker.check(lines) is False

    def test_less_than_3_lines(self):
        checker = self._make_checker()
        lines = [PotentialLine("STR%", 9)]
        assert checker.check(lines) is False

    def test_empty_lines(self):
        checker = self._make_checker()
        assert checker.check([]) is False


class TestConditionCheckerArmorSub250:
    """一般裝備 DEX 含全屬性"""

    def test_pass(self):
        config = AppConfig(
            equipment_type="一般裝備 (<250)",
            target_attribute="DEX",
            include_all_stats=True,
        )
        checker = ConditionChecker(config)
        lines = [
            PotentialLine("DEX%", 8),
            PotentialLine("全屬性%", 5),
            PotentialLine("DEX%", 6),
        ]
        assert checker.check(lines) is True

    def test_fail_line1(self):
        config = AppConfig(
            equipment_type="一般裝備 (<250)",
            target_attribute="DEX",
            include_all_stats=True,
        )
        checker = ConditionChecker(config)
        lines = [
            PotentialLine("DEX%", 7),  # S潛 needs >= 8
            PotentialLine("DEX%", 6),
            PotentialLine("DEX%", 6),
        ]
        assert checker.check(lines) is False


class TestConditionCheckerWeapon:
    """主武器 物理攻擊力"""

    def test_pass(self):
        config = AppConfig(
            equipment_type="主武器",
            target_attribute="物理攻擊力",
        )
        checker = ConditionChecker(config)
        lines = [
            PotentialLine("物理攻擊力%", 13),
            PotentialLine("物理攻擊力%", 10),
            PotentialLine("物理攻擊力%", 10),
        ]
        assert checker.check(lines) is True

    def test_fail(self):
        config = AppConfig(
            equipment_type="主武器",
            target_attribute="物理攻擊力",
        )
        checker = ConditionChecker(config)
        lines = [
            PotentialLine("物理攻擊力%", 13),
            PotentialLine("物理攻擊力%", 9),  # 罕見 needs >= 10
            PotentialLine("物理攻擊力%", 10),
        ]
        assert checker.check(lines) is False

    def test_sub_weapon(self):
        config = AppConfig(
            equipment_type="輔助武器",
            target_attribute="魔法攻擊力",
        )
        checker = ConditionChecker(config)
        lines = [
            PotentialLine("魔法攻擊力%", 12),
            PotentialLine("魔法攻擊力%", 9),
            PotentialLine("魔法攻擊力%", 9),
        ]
        assert checker.check(lines) is True


class TestConditionCheckerGlove:
    """手套"""

    def test_glove_250_pass(self):
        config = AppConfig(
            equipment_type="手套 (250+)",
            target_attribute="STR",
            include_all_stats=True,
        )
        checker = ConditionChecker(config)
        lines = [
            PotentialLine("爆擊傷害%", 3),
            PotentialLine("STR%", 7),
            PotentialLine("全屬性%", 6),
        ]
        assert checker.check(lines) is True

    def test_glove_250_double_s(self):
        config = AppConfig(
            equipment_type="手套 (250+)",
            target_attribute="STR",
            include_all_stats=True,
        )
        checker = ConditionChecker(config)
        lines = [
            PotentialLine("爆擊傷害%", 3),
            PotentialLine("爆擊傷害%", 3),  # 雙S
            PotentialLine("全屬性%", 6),
        ]
        assert checker.check(lines) is True

    def test_glove_crit1_rejected(self):
        config = AppConfig(
            equipment_type="手套 (250+)",
            target_attribute="STR",
            include_all_stats=True,
        )
        checker = ConditionChecker(config)
        lines = [
            PotentialLine("爆擊傷害%", 1),  # 1% is useless
            PotentialLine("STR%", 7),
            PotentialLine("STR%", 7),
        ]
        assert checker.check(lines) is False

    def test_glove_line1_attr_line2_crit(self):
        """第1行屬性、第2行爆傷也保留"""
        config = AppConfig(
            equipment_type="手套 (250+)",
            target_attribute="STR",
            include_all_stats=True,
        )
        checker = ConditionChecker(config)
        lines = [
            PotentialLine("STR%", 9),
            PotentialLine("爆擊傷害%", 3),
            PotentialLine("全屬性%", 6),
        ]
        assert checker.check(lines) is True

    def test_glove_all_attr_no_crit(self):
        """手套三行都是屬性也合格"""
        config = AppConfig(
            equipment_type="手套 (250+)",
            target_attribute="STR",
            include_all_stats=True,
        )
        checker = ConditionChecker(config)
        lines = [
            PotentialLine("STR%", 9),
            PotentialLine("STR%", 7),
            PotentialLine("全屬性%", 6),
        ]
        assert checker.check(lines) is True

    def test_glove_sub250(self):
        config = AppConfig(
            equipment_type="手套 (<250)",
            target_attribute="LUK",
            include_all_stats=True,
        )
        checker = ConditionChecker(config)
        lines = [
            PotentialLine("爆擊傷害%", 3),
            PotentialLine("LUK%", 6),
            PotentialLine("全屬性%", 5),
        ]
        assert checker.check(lines) is True

    def test_glove_sub250_fail(self):
        config = AppConfig(
            equipment_type="手套 (<250)",
            target_attribute="LUK",
            include_all_stats=True,
        )
        checker = ConditionChecker(config)
        lines = [
            PotentialLine("爆擊傷害%", 3),
            PotentialLine("LUK%", 5),  # 罕見 needs >= 6
            PotentialLine("全屬性%", 5),
        ]
        assert checker.check(lines) is False


class TestConditionCheckerMaxHP:
    def test_maxhp_250(self):
        config = AppConfig(
            equipment_type="永恆裝備·光輝套裝 (250+)",
            target_attribute="MaxHP",
        )
        checker = ConditionChecker(config)
        lines = [
            PotentialLine("MaxHP%", 12),
            PotentialLine("MaxHP%", 9),
            PotentialLine("MaxHP%", 9),
        ]
        assert checker.check(lines) is True

    def test_maxhp_sub250(self):
        config = AppConfig(
            equipment_type="一般裝備 (<250)",
            target_attribute="MaxHP",
        )
        checker = ConditionChecker(config)
        lines = [
            PotentialLine("MaxHP%", 11),
            PotentialLine("MaxHP%", 8),
            PotentialLine("MaxHP%", 8),
        ]
        assert checker.check(lines) is True


class TestConditionCheckerPet:
    """萌獸"""

    def test_final_damage_3_lines(self):
        config = AppConfig(equipment_type="萌獸", target_attribute="最終傷害")
        checker = ConditionChecker(config)
        lines = [
            PotentialLine("最終傷害%", 25),
            PotentialLine("最終傷害%", 20),
            PotentialLine("最終傷害%", 20),
        ]
        assert checker.check(lines) is True

    def test_final_damage_too_low(self):
        config = AppConfig(equipment_type="萌獸", target_attribute="最終傷害")
        checker = ConditionChecker(config)
        lines = [
            PotentialLine("最終傷害%", 25),
            PotentialLine("最終傷害%", 19),  # < 20
            PotentialLine("最終傷害%", 20),
        ]
        assert checker.check(lines) is False

    def test_physical_attack_3_lines(self):
        config = AppConfig(equipment_type="萌獸", target_attribute="物理攻擊力")
        checker = ConditionChecker(config)
        lines = [
            PotentialLine("物理攻擊力%", 25),
            PotentialLine("物理攻擊力%", 20),
            PotentialLine("物理攻擊力%", 20),
        ]
        assert checker.check(lines) is True

    def test_buff_duration_3_lines(self):
        config = AppConfig(equipment_type="萌獸", target_attribute="加持技能持續時間")
        checker = ConditionChecker(config)
        lines = [
            PotentialLine("加持技能持續時間%", 55),
            PotentialLine("加持技能持續時間%", 50),
            PotentialLine("加持技能持續時間%", 50),
        ]
        assert checker.check(lines) is True

    def test_buff_duration_too_low(self):
        config = AppConfig(equipment_type="萌獸", target_attribute="加持技能持續時間")
        checker = ConditionChecker(config)
        lines = [
            PotentialLine("加持技能持續時間%", 55),
            PotentialLine("加持技能持續時間%", 49),  # < 50
            PotentialLine("加持技能持續時間%", 50),
        ]
        assert checker.check(lines) is False

    def test_雙終被_pass(self):
        config = AppConfig(equipment_type="萌獸", target_attribute="雙終被")
        checker = ConditionChecker(config)
        lines = [
            PotentialLine("被動技能2", 0, "依照被動技能 2 來增加"),
            PotentialLine("最終傷害%", 20),
            PotentialLine("最終傷害%", 20),
        ]
        assert checker.check(lines) is True

    def test_雙終被_any_order(self):
        config = AppConfig(equipment_type="萌獸", target_attribute="雙終被")
        checker = ConditionChecker(config)
        lines = [
            PotentialLine("最終傷害%", 25),
            PotentialLine("被動技能2", 0, "依照被動技能 2 來增加"),
            PotentialLine("最終傷害%", 20),
        ]
        assert checker.check(lines) is True

    def test_雙終被_final_too_low(self):
        config = AppConfig(equipment_type="萌獸", target_attribute="雙終被")
        checker = ConditionChecker(config)
        lines = [
            PotentialLine("被動技能2", 0, "依照被動技能 2 來增加"),
            PotentialLine("最終傷害%", 19),  # < 20
            PotentialLine("最終傷害%", 20),
        ]
        assert checker.check(lines) is False

    def test_雙終被_missing_passive(self):
        config = AppConfig(equipment_type="萌獸", target_attribute="雙終被")
        checker = ConditionChecker(config)
        lines = [
            PotentialLine("最終傷害%", 25),
            PotentialLine("最終傷害%", 20),
            PotentialLine("最終傷害%", 20),
        ]
        assert checker.check(lines) is False
