from app.core.condition import ConditionChecker, parse_potential_line, parse_potential_lines
from app.models.config import AppConfig, LineCondition
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

    def test_ocr_fix_japanese_kanji(self):
        """攻撃 → 攻擊 自動修正"""
        line = parse_potential_line("物理攻撃力 +13%")
        assert line.attribute == "物理攻擊力%"
        assert line.value == 13


class TestParsePotentialLines:
    """碎片合併解析"""

    def test_split_fragments(self):
        """OCR 把 'STR +9%' 拆成 ['STR', '+9%']"""
        lines = parse_potential_lines(["STR", "+9%"])
        assert len(lines) == 1
        assert lines[0].attribute == "STR%"
        assert lines[0].value == 9

    def test_multiple_lines_merged(self):
        """多行潛能全部合併後解析"""
        lines = parse_potential_lines(["STR", "+9%", "DEX+7%", "LUK +6%"])
        attrs = {l.attribute for l in lines}
        assert "STR%" in attrs
        assert "DEX%" in attrs
        assert "LUK%" in attrs
        assert len(lines) == 3

    def test_japanese_kanji_fix(self):
        """攻撃 → 攻擊 修正後能解析"""
        lines = parse_potential_lines(["物理攻撃力", "+13%"])
        assert len(lines) == 1
        assert lines[0].attribute == "物理攻擊力%"
        assert lines[0].value == 13

    def test_simplified_chinese_fix(self):
        """簡體字修正：最终→最終, 全国性→全屬性"""
        lines = parse_potential_lines(["全国性：+7%", "最终傷害：+20%"])
        assert len(lines) == 2
        assert lines[0].attribute == "全屬性%"
        assert lines[0].value == 7
        assert lines[1].attribute == "最終傷害%"
        assert lines[1].value == 20

    def test_positional_order_preserved(self):
        """結果應按原始文字位置排序，而非 ATTRIBUTE_PATTERNS 順序"""
        lines = parse_potential_lines(["最終傷害：+20%", "STR：+9%"])
        assert len(lines) == 2
        assert lines[0].attribute == "最終傷害%"
        assert lines[1].attribute == "STR%"

    def test_cross_fragment_percent_not_matched(self):
        """'DEX +18' 不應因隔壁碎片的 '%' 被誤判為 DEX +18%"""
        lines = parse_potential_lines(["MaxMP+300", "DEX +18", "%9+INI"])
        attrs = [l.attribute for l in lines]
        assert "DEX%" not in attrs

    def test_cross_fragment_percent_second_case(self):
        """'STR +18' 不應因隔壁碎片的 '%' 被誤判為 STR +18%"""
        lines = parse_potential_lines(["STR +18", "STR +18", "%9+", "XEI"])
        # STR +18 是固定值，不是百分比，不應被解析
        attrs = [l.attribute for l in lines]
        assert "STR%" not in attrs

    def test_pet_cube_ocr_misread(self):
        """實際萌獸方塊 OCR 結果（含簡繁混雜）"""
        lines = parse_potential_lines(["全国性：+20", "DEX", "最终傷害：+20%", "：+14%"])
        attrs = [l.attribute for l in lines]
        assert "最終傷害%" in attrs


class TestConditionCheckerArmor250:
    """永恆裝備 STR 含全屬性"""

    def _make_checker(self, include_all=True):
        config = AppConfig(
            equipment_type="永恆裝備·光輝套裝 (250等+)",
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
            equipment_type="一般裝備 (神秘、漆黑、頂培)",
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
            equipment_type="一般裝備 (神秘、漆黑、頂培)",
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
            equipment_type="手套 (永恆)",
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
            equipment_type="手套 (永恆)",
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
            equipment_type="手套 (永恆)",
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
            equipment_type="手套 (永恆)",
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
            equipment_type="手套 (永恆)",
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
            equipment_type="手套 (非永恆)",
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
            equipment_type="手套 (非永恆)",
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
            equipment_type="永恆裝備·光輝套裝 (250等+)",
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
            equipment_type="一般裝備 (神秘、漆黑、頂培)",
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


class TestConditionCheckerCustomMode:
    """自訂模式測試"""

    def test_custom_all_same_attr_pass(self):
        config = AppConfig(
            use_preset=False,
            custom_lines=[
                LineCondition("STR", 1),
                LineCondition("STR", 1),
                LineCondition("STR", 1),
            ],
        )
        checker = ConditionChecker(config)
        lines = [
            PotentialLine("STR%", 3),
            PotentialLine("STR%", 5),
            PotentialLine("STR%", 1),
        ]
        assert checker.check(lines) is True

    def test_custom_mixed_attrs_pass(self):
        config = AppConfig(
            use_preset=False,
            custom_lines=[
                LineCondition("STR", 5),
                LineCondition("DEX", 3),
                LineCondition("全屬性", 2),
            ],
        )
        checker = ConditionChecker(config)
        lines = [
            PotentialLine("STR%", 9),
            PotentialLine("DEX%", 3),
            PotentialLine("全屬性%", 6),
        ]
        assert checker.check(lines) is True

    def test_custom_value_too_low(self):
        config = AppConfig(
            use_preset=False,
            custom_lines=[
                LineCondition("STR", 5),
                LineCondition("DEX", 3),
                LineCondition("LUK", 2),
            ],
        )
        checker = ConditionChecker(config)
        lines = [
            PotentialLine("STR%", 9),
            PotentialLine("DEX%", 2),  # < 3
            PotentialLine("LUK%", 6),
        ]
        assert checker.check(lines) is False

    def test_custom_wrong_attribute(self):
        config = AppConfig(
            use_preset=False,
            custom_lines=[
                LineCondition("STR", 1),
                LineCondition("DEX", 1),
                LineCondition("INT", 1),
            ],
        )
        checker = ConditionChecker(config)
        lines = [
            PotentialLine("STR%", 9),
            PotentialLine("LUK%", 7),  # wrong attr
            PotentialLine("INT%", 6),
        ]
        assert checker.check(lines) is False

    def test_custom_passive_skill2(self):
        config = AppConfig(
            use_preset=False,
            custom_lines=[
                LineCondition("最終傷害", 20),
                LineCondition("最終傷害", 20),
                LineCondition("被動技能2", 1),
            ],
        )
        checker = ConditionChecker(config)
        lines = [
            PotentialLine("最終傷害%", 25),
            PotentialLine("最終傷害%", 20),
            PotentialLine("被動技能2", 0, "依照被動技能 2 來增加"),
        ]
        assert checker.check(lines) is True

    def test_custom_passive_skill2_missing(self):
        config = AppConfig(
            use_preset=False,
            custom_lines=[
                LineCondition("最終傷害", 20),
                LineCondition("最終傷害", 20),
                LineCondition("被動技能2", 1),
            ],
        )
        checker = ConditionChecker(config)
        lines = [
            PotentialLine("最終傷害%", 25),
            PotentialLine("最終傷害%", 20),
            PotentialLine("最終傷害%", 20),
        ]
        assert checker.check(lines) is False

    def test_custom_less_than_3_lines(self):
        config = AppConfig(
            use_preset=False,
            custom_lines=[
                LineCondition("STR", 1),
                LineCondition("STR", 1),
                LineCondition("STR", 1),
            ],
        )
        checker = ConditionChecker(config)
        assert checker.check([PotentialLine("STR%", 9)]) is False

    def test_custom_low_threshold_for_ocr_testing(self):
        """低門檻用於 OCR 測試 — 幾乎任何結果都 match。"""
        config = AppConfig(
            use_preset=False,
            custom_lines=[
                LineCondition("STR", 1),
                LineCondition("STR", 1),
                LineCondition("STR", 1),
            ],
        )
        checker = ConditionChecker(config)
        lines = [
            PotentialLine("STR%", 1),
            PotentialLine("STR%", 1),
            PotentialLine("STR%", 1),
        ]
        assert checker.check(lines) is True


class TestConditionCheckerCustomSummary:
    """自訂模式條件摘要測試"""

    def test_custom_summary(self):
        from app.core.condition import generate_condition_summary

        config = AppConfig(
            use_preset=False,
            custom_lines=[
                LineCondition("STR", 5),
                LineCondition("DEX", 3),
                LineCondition("全屬性", 2),
            ],
        )
        lines = generate_condition_summary(config)
        assert len(lines) == 3
        assert "第1排" in lines[0]
        assert "STR 至少 5%" in lines[0]
        assert "DEX 至少 3%" in lines[1]
        assert "全屬性 至少 2%" in lines[2]

    def test_custom_summary_passive(self):
        from app.core.condition import generate_condition_summary

        config = AppConfig(
            use_preset=False,
            custom_lines=[
                LineCondition("最終傷害", 20),
                LineCondition("最終傷害", 20),
                LineCondition("被動技能2", 1),
            ],
        )
        lines = generate_condition_summary(config)
        assert "被動技能2" in lines[2]
        assert "第3排" in lines[2]

class TestConditionCheckerDynamicRows:
    """自訂模式動態排數測試"""

    def test_single_row(self):
        config = AppConfig(
            use_preset=False,
            custom_lines=[LineCondition("STR", 5)],
        )
        checker = ConditionChecker(config)
        lines = [PotentialLine("STR%", 9)]
        assert checker.check(lines) is True

    def test_single_row_fail(self):
        config = AppConfig(
            use_preset=False,
            custom_lines=[LineCondition("STR", 5)],
        )
        checker = ConditionChecker(config)
        lines = [PotentialLine("STR%", 4)]
        assert checker.check(lines) is False

    def test_two_rows(self):
        config = AppConfig(
            use_preset=False,
            custom_lines=[
                LineCondition("STR", 5),
                LineCondition("DEX", 3),
            ],
        )
        checker = ConditionChecker(config)
        lines = [
            PotentialLine("STR%", 9),
            PotentialLine("DEX%", 3),
        ]
        assert checker.check(lines) is True

    def test_two_rows_not_enough_lines(self):
        config = AppConfig(
            use_preset=False,
            custom_lines=[
                LineCondition("STR", 5),
                LineCondition("DEX", 3),
            ],
        )
        checker = ConditionChecker(config)
        lines = [PotentialLine("STR%", 9)]
        assert checker.check(lines) is False
