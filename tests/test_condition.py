from app.core.condition import ConditionChecker, generate_condition_summary, get_num_lines, parse_potential_line, parse_potential_lines
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

    def test_flat_value_matched(self):
        line = parse_potential_line("STR +21")
        assert line.attribute == "STR"
        assert line.value == 21

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

    def test_ocr_fix_b_to_8(self):
        """MaxMP+B% → MaxMP+8%"""
        line = parse_potential_line("MaxMP+B%")
        assert line.attribute == "MaxMP%"
        assert line.value == 8

    def test_ocr_fix_japanese_kanji(self):
        """攻撃 → 攻擊 自動修正"""
        line = parse_potential_line("物理攻撃力 +13%")
        assert line.attribute == "物理攻擊力%"
        assert line.value == 13

    def test_ocr_fix_all_stats_wu(self):
        """全屋性 → 全屬性 自動修正"""
        line = parse_potential_line("全屋性 +5%")
        assert line.attribute == "全屬性%"
        assert line.value == 5

    def test_ocr_fix_trailing_digit_after_percent(self):
        """+6%6 → +6% 自動修正（OCR 殘留碎片）"""
        line = parse_potential_line("LUK+6%6")
        assert line.attribute == "LUK%"
        assert line.value == 6

    def test_ocr_fix_trailing_digit_str(self):
        """+6%6 on STR"""
        line = parse_potential_line("STR +6%6")
        assert line.attribute == "STR%"
        assert line.value == 6

    def test_ocr_fix_int_as_it(self):
        """IT+ → INT+ 自動修正"""
        line = parse_potential_line("IT+6%")
        assert line.attribute == "INT%"
        assert line.value == 6

    def test_ocr_fix_it_no_false_positive_on_crit(self):
        """CRIT+3% 不應被誤改為 CRINT+3%（確認不會被誤判為 INT%）"""
        line = parse_potential_line("CRIT+3%")
        assert line.attribute != "INT%"

    def test_ocr_fix_trailing_multi_digit_after_percent(self):
        """+5%12 → +5% 多位數殘留"""
        line = parse_potential_line("DEX+5%12")
        assert line.attribute == "DEX%"
        assert line.value == 5

    def test_ocr_fix_all_stats_guo(self):
        """全國性 → 全屬性 自動修正"""
        line = parse_potential_line("全國性+6%")
        assert line.attribute == "全屬性%"
        assert line.value == 6

    def test_ocr_fix_all_stats_qing(self):
        """全慶性 → 全屬性 自動修正"""
        line = parse_potential_line("全慶性+5%")
        assert line.attribute == "全屬性%"
        assert line.value == 5

    def test_ocr_fix_int_as_1nt(self):
        """1NT → INT（I↔1 混淆）"""
        line = parse_potential_line("1NT+6%")
        assert line.attribute == "INT%"
        assert line.value == 6

    def test_ocr_fix_int_as_1it(self):
        """1IT → INT"""
        line = parse_potential_line("1IT+6%")
        assert line.attribute == "INT%"
        assert line.value == 6

    def test_ocr_fix_int_as_1tt(self):
        """1TT → INT"""
        line = parse_potential_line("1TT+6%")
        assert line.attribute == "INT%"
        assert line.value == 6

    def test_ocr_fix_int_as_iit(self):
        """IIT → INT"""
        line = parse_potential_line("IIT+6%")
        assert line.attribute == "INT%"
        assert line.value == 6

    def test_ocr_fix_maxhp_ax(self):
        """axHP → MaxHP 自動修正"""
        line = parse_potential_line("axHP +121")
        assert line.attribute == "MaxHP"
        assert line.value == 121

    def test_ocr_fix_percent_as_nine(self):
        """全屬性+79 → 全屬性+7%（% 被誤讀為 9）"""
        line = parse_potential_line("全属性+79")
        assert line.attribute == "全屬性%"
        assert line.value == 7

    def test_ocr_fix_percent_as_nine_not_applied_when_percent_exists(self):
        """已有 % 時不套用 9→% 修正"""
        line = parse_potential_line("STR+9%")
        assert line.attribute == "STR%"
        assert line.value == 9

    def test_ocr_fix_percent_as_nine_no_false_positive_flat_str(self):
        """STR+19 是合法平值，不應被誤改為 STR+1%"""
        line = parse_potential_line("STR+19")
        assert line.attribute == "STR"
        assert line.value == 19

    def test_ocr_fix_percent_as_nine_no_false_positive_flat_maxhp(self):
        """MaxHP+219 是合法平值，不應被誤改為 MaxHP+21%"""
        line = parse_potential_line("MaxHP+219")
        assert line.attribute == "MaxHP"
        assert line.value == 219


class TestParsePotentialLines:
    """碎片合併解析（使用 y 座標分群）"""

    @staticmethod
    def _with_y(texts_and_ys: list[tuple[str, float]]) -> list[tuple[str, float]]:
        """輔助：直接傳遞 (text, y) 列表。"""
        return texts_and_ys

    @staticmethod
    def _same_row(texts: list[str], y: float = 10.0) -> list[tuple[str, float]]:
        """輔助：所有碎片在同一行（同一 y）。"""
        return [(t, y + i * 0.1) for i, t in enumerate(texts)]

    @staticmethod
    def _three_rows(row1: str, row2: str, row3: str) -> list[tuple[str, float]]:
        """輔助：三行各一個碎片，y 間距明顯。"""
        return [(row1, 10.0), (row2, 30.0), (row3, 50.0)]

    def test_split_fragments(self):
        """OCR 把 'STR +9%' 拆成 ['STR', '+9%']，同一行"""
        lines = parse_potential_lines(self._same_row(["STR", "+9%"]))
        # 同一行合併後只有一個屬性，其餘行為「未知」
        known = [l for l in lines if l.attribute != "未知"]
        assert len(known) == 1
        assert known[0].attribute == "STR%"
        assert known[0].value == 9

    def test_multiple_lines_merged(self):
        """多行潛能，碎片分布在 3 個物理行"""
        frags = [("STR", 10.0), ("+9%", 10.5), ("DEX+7%", 30.0), ("LUK +6%", 50.0)]
        lines = parse_potential_lines(frags)
        assert len(lines) == 3
        attrs = {l.attribute for l in lines}
        assert "STR%" in attrs
        assert "DEX%" in attrs
        assert "LUK%" in attrs

    def test_japanese_kanji_fix(self):
        """攻撃 → 攻擊 修正後能解析"""
        lines = parse_potential_lines(self._same_row(["物理攻撃力", "+13%"]))
        known = [l for l in lines if l.attribute != "未知"]
        assert len(known) == 1
        assert known[0].attribute == "物理攻擊力%"
        assert known[0].value == 13

    def test_simplified_chinese_fix(self):
        """簡體字修正：最终→最終, 全国性→全屬性"""
        frags = [("全国性：+7%", 10.0), ("最终傷害：+20%", 30.0)]
        lines = parse_potential_lines(frags)
        known = [l for l in lines if l.attribute != "未知"]
        assert len(known) == 2
        assert known[0].attribute == "全屬性%"
        assert known[0].value == 7
        assert known[1].attribute == "最終傷害%"
        assert known[1].value == 20

    def test_positional_order_preserved(self):
        """結果應按 y 座標排序（物理位置），而非 ATTRIBUTE_PATTERNS 順序"""
        frags = [("最終傷害：+20%", 10.0), ("STR：+9%", 30.0)]
        lines = parse_potential_lines(frags)
        known = [l for l in lines if l.attribute != "未知"]
        assert len(known) == 2
        assert known[0].attribute == "最終傷害%"
        assert known[1].attribute == "STR%"

    def test_cross_fragment_percent_not_matched(self):
        """'DEX +18' 不應因隔壁碎片的 '%' 被誤判為 DEX +18%"""
        frags = self._three_rows("MaxMP+300", "DEX +18", "%9+INI")
        lines = parse_potential_lines(frags)
        attrs = [l.attribute for l in lines]
        assert "DEX%" not in attrs

    def test_cross_fragment_percent_second_case(self):
        """'STR +18' 不應因隔壁碎片的 '%' 被誤判為 STR +18%"""
        frags = [("STR +18", 10.0), ("STR +18", 10.5), ("%9+", 30.0), ("XEI", 50.0)]
        lines = parse_potential_lines(frags)
        attrs = [l.attribute for l in lines]
        assert "STR%" not in attrs

    def test_pet_cube_ocr_misread(self):
        """實際萌獸方塊 OCR 結果（含簡繁混雜）"""
        frags = [("全国性：+20", 10.0), ("DEX", 10.5), ("最终傷害：+20%", 30.0), ("：+14%", 50.0)]
        lines = parse_potential_lines(frags)
        attrs = [l.attribute for l in lines]
        assert "最終傷害%" in attrs

    def test_always_returns_3_lines(self):
        """永遠回傳恰好 3 個 PotentialLine"""
        lines = parse_potential_lines([("STR +9%", 10.0)])
        assert len(lines) == 3

    def test_empty_input(self):
        """空輸入回傳 3 個未知"""
        lines = parse_potential_lines([])
        assert len(lines) == 3
        assert all(l.attribute == "未知" for l in lines)

    def test_ocr_skip_row_stability(self):
        """OCR 漏讀中間行時，第1排和第3排不受影響"""
        frags = [("STR +9%", 10.0), ("LUK +6%", 50.0)]
        lines = parse_potential_lines(frags)
        assert len(lines) == 3
        assert lines[0].attribute == "STR%"
        assert lines[0].value == 9
        assert lines[1].attribute == "LUK%"
        assert lines[1].value == 6
        # 第三行是補的「未知」
        assert lines[2].attribute == "未知"


class TestConditionCheckerArmor250:
    """永恆裝備 STR 含全屬性"""

    def _make_checker(self):
        config = AppConfig(
            equipment_type="永恆 / 光輝",
            target_attribute="STR",
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
            PotentialLine("STR%", 6),  # S潛 needs >= 9, 6+2=8 < 9
            PotentialLine("STR%", 6),  # 所有值都不夠當 S 位
            PotentialLine("STR%", 6),
        ]
        assert checker.check(lines) is False

    def test_line2_too_low(self):
        checker = self._make_checker()
        lines = [
            PotentialLine("STR%", 9),
            PotentialLine("STR%", 4),  # 罕見 needs >= 7, 4+2=6 < 7
            PotentialLine("STR%", 7),
        ]
        assert checker.check(lines) is False

    def test_tolerance_saves_borderline(self):
        """容錯=2: STR 7% (可能是 9% 誤讀) 在 S 位通過。"""
        checker = self._make_checker()
        lines = [
            PotentialLine("STR%", 7),  # 7+2=9 >= 9(S) ✓
            PotentialLine("STR%", 7),
            PotentialLine("STR%", 7),
        ]
        assert checker.check(lines) is True

    def test_tolerance_saves_r_position(self):
        """容錯=2: R 位 STR 6% (可能是 8% 誤讀) 通過。"""
        checker = self._make_checker()
        lines = [
            PotentialLine("STR%", 9),
            PotentialLine("STR%", 6),  # 6+2=8 >= 7(R) ✓
            PotentialLine("STR%", 7),
        ]
        assert checker.check(lines) is True

    def test_str_always_includes_all_stats(self):
        """STR 自動含全屬性。"""
        checker = self._make_checker()
        lines = [
            PotentialLine("STR%", 9),
            PotentialLine("全屬性%", 6),
            PotentialLine("STR%", 7),
        ]
        assert checker.check(lines) is True

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


class TestConditionCheckerAllStatsOnly:
    """全屬性 standalone target attribute"""

    def test_pass_all_stats(self):
        config = AppConfig(
            equipment_type="永恆 / 光輝",
            target_attribute="全屬性",
        )
        checker = ConditionChecker(config)
        lines = [
            PotentialLine("全屬性%", 7),
            PotentialLine("全屬性%", 6),
            PotentialLine("全屬性%", 6),
        ]
        assert checker.check(lines) is True

    def test_fail_str_not_accepted(self):
        """全屬性 target 不接受 STR%"""
        config = AppConfig(
            equipment_type="永恆 / 光輝",
            target_attribute="全屬性",
        )
        checker = ConditionChecker(config)
        lines = [
            PotentialLine("全屬性%", 7),
            PotentialLine("STR%", 9),  # 全屬性 mode 不接受 STR
            PotentialLine("全屬性%", 6),
        ]
        assert checker.check(lines) is False

    def test_fail_too_low(self):
        config = AppConfig(
            equipment_type="永恆 / 光輝",
            target_attribute="全屬性",
        )
        checker = ConditionChecker(config)
        lines = [
            PotentialLine("全屬性%", 4),  # S潛 needs >= 7, 4+2=6 < 7
            PotentialLine("全屬性%", 4),  # 所有值都不夠當 S 位
            PotentialLine("全屬性%", 4),
        ]
        assert checker.check(lines) is False


class TestConditionCheckerAllAttributes:
    """所有屬性模式 — 每行可以是任一有效屬性"""

    def test_same_attr_pass(self):
        """三排同主屬性通過"""
        config = AppConfig(
            equipment_type="永恆 / 光輝",
            target_attribute="所有屬性",
        )
        checker = ConditionChecker(config)
        lines = [
            PotentialLine("STR%", 9),
            PotentialLine("STR%", 7),
            PotentialLine("STR%", 7),
        ]
        assert checker.check(lines) is True

    def test_same_attr_with_all_stats(self):
        """主屬性 + 全屬性混搭通過"""
        config = AppConfig(
            equipment_type="永恆 / 光輝",
            target_attribute="所有屬性",
        )
        checker = ConditionChecker(config)
        lines = [
            PotentialLine("INT%", 9),
            PotentialLine("全屬性%", 6),
            PotentialLine("INT%", 7),
        ]
        assert checker.check(lines) is True

    def test_different_attrs_fail(self):
        """不同主屬性混搭不通過"""
        config = AppConfig(
            equipment_type="永恆 / 光輝",
            target_attribute="所有屬性",
        )
        checker = ConditionChecker(config)
        lines = [
            PotentialLine("STR%", 9),
            PotentialLine("DEX%", 7),
            PotentialLine("LUK%", 7),
        ]
        assert checker.check(lines) is False

    def test_maxhp_three_pass(self):
        """三排 MaxHP 通過"""
        config = AppConfig(
            equipment_type="永恆 / 光輝",
            target_attribute="所有屬性",
        )
        checker = ConditionChecker(config)
        lines = [
            PotentialLine("MaxHP%", 12),
            PotentialLine("MaxHP%", 9),
            PotentialLine("MaxHP%", 9),
        ]
        assert checker.check(lines) is True

    def test_fail_value_too_low(self):
        config = AppConfig(
            equipment_type="永恆 / 光輝",
            target_attribute="所有屬性",
        )
        checker = ConditionChecker(config)
        lines = [
            PotentialLine("STR%", 6),  # 沒有一個屬性的 S潛 <= 6
            PotentialLine("DEX%", 6),
            PotentialLine("LUK%", 6),
        ]
        assert checker.check(lines) is False

    def test_glove_with_crit(self):
        config = AppConfig(
            equipment_type="手套", is_eternal=True,
            target_attribute="所有屬性",
        )
        checker = ConditionChecker(config)
        lines = [
            PotentialLine("STR%", 9),
            PotentialLine("爆擊傷害%", 3),
            PotentialLine("全屬性%", 6),
        ]
        assert checker.check(lines) is True

    def test_hat_with_cooldown(self):
        config = AppConfig(
            equipment_type="帽子", is_eternal=True,
            target_attribute="所有屬性",
        )
        checker = ConditionChecker(config)
        lines = [
            PotentialLine("INT%", 9),
            PotentialLine("技能冷卻時間", 1),
            PotentialLine("INT%", 7),
        ]
        assert checker.check(lines) is True

    def test_wrong_attr_rejected(self):
        """所有屬性不接受不在該裝備 threshold 的屬性"""
        config = AppConfig(
            equipment_type="永恆 / 光輝",
            target_attribute="所有屬性",
        )
        checker = ConditionChecker(config)
        lines = [
            PotentialLine("STR%", 9),
            PotentialLine("物理攻擊力%", 13),  # 非裝備屬性
            PotentialLine("DEX%", 7),
        ]
        assert checker.check(lines) is False


class TestConditionCheckerArmorSub250:
    """一般裝備 DEX 含全屬性"""

    def test_pass(self):
        config = AppConfig(
            equipment_type="一般裝備 (神秘、漆黑、頂培)",
            target_attribute="DEX",

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

        )
        checker = ConditionChecker(config)
        lines = [
            PotentialLine("DEX%", 5),  # S潛 needs >= 8, 5+2=7 < 8
            PotentialLine("DEX%", 5),  # 所有值都不夠當 S 位
            PotentialLine("DEX%", 5),
        ]
        assert checker.check(lines) is False


class TestConditionCheckerWeapon:
    """主武器 物理攻擊力"""

    def test_pass(self):
        config = AppConfig(
            equipment_type="主武器 / 徽章 (米特拉)",
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
            equipment_type="主武器 / 徽章 (米特拉)",
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
            equipment_type="輔助武器 (副手)",
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
            equipment_type="手套", is_eternal=True,
            target_attribute="STR",

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
            equipment_type="手套", is_eternal=True,
            target_attribute="STR",

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
            equipment_type="手套", is_eternal=True,
            target_attribute="STR",

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
            equipment_type="手套", is_eternal=True,
            target_attribute="STR",

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
            equipment_type="手套", is_eternal=True,
            target_attribute="STR",

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
            equipment_type="手套", is_eternal=False,
            target_attribute="LUK",

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
            equipment_type="手套", is_eternal=False,
            target_attribute="LUK",

        )
        checker = ConditionChecker(config)
        lines = [
            PotentialLine("爆擊傷害%", 3),
            PotentialLine("LUK%", 3),  # 罕見 needs >= 6, 3+2=5 < 6
            PotentialLine("全屬性%", 5),
        ]
        assert checker.check(lines) is False


class TestConditionCheckerMaxHP:
    def test_maxhp_250(self):
        config = AppConfig(
            equipment_type="永恆 / 光輝",
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
    """自訂模式測試（指定位置）"""

    def test_custom_all_same_attr_pass(self):
        config = AppConfig(
            use_preset=False,
            custom_lines=[
                LineCondition("STR", 1, position=1),
                LineCondition("STR", 1, position=2),
                LineCondition("STR", 1, position=3),
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
                LineCondition("STR", 5, position=1),
                LineCondition("DEX", 3, position=2),
                LineCondition("全屬性", 2, position=3),
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
                LineCondition("STR", 5, position=1),
                LineCondition("DEX", 3, position=2),
                LineCondition("LUK", 2, position=3),
            ],
        )
        checker = ConditionChecker(config)
        lines = [
            PotentialLine("STR%", 9),
            PotentialLine("DEX%", 0),  # 0+2=2 < 3
            PotentialLine("LUK%", 6),
        ]
        assert checker.check(lines) is False

    def test_custom_wrong_attribute(self):
        config = AppConfig(
            use_preset=False,
            custom_lines=[
                LineCondition("STR", 1, position=1),
                LineCondition("DEX", 1, position=2),
                LineCondition("INT", 1, position=3),
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
                LineCondition("最終傷害", 20, position=1),
                LineCondition("最終傷害", 20, position=2),
                LineCondition("被動技能2", 1, position=3),
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
                LineCondition("最終傷害", 20, position=1),
                LineCondition("最終傷害", 20, position=2),
                LineCondition("被動技能2", 1, position=3),
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
                LineCondition("STR", 1, position=1),
                LineCondition("STR", 1, position=2),
                LineCondition("STR", 1, position=3),
            ],
        )
        checker = ConditionChecker(config)
        assert checker.check([PotentialLine("STR%", 9)]) is False

    def test_custom_low_threshold_for_ocr_testing(self):
        """低門檻用於 OCR 測試 — 幾乎任何結果都 match。"""
        config = AppConfig(
            use_preset=False,
            custom_lines=[
                LineCondition("STR", 1, position=1),
                LineCondition("STR", 1, position=2),
                LineCondition("STR", 1, position=3),
            ],
        )
        checker = ConditionChecker(config)
        lines = [
            PotentialLine("STR%", 1),
            PotentialLine("STR%", 1),
            PotentialLine("STR%", 1),
        ]
        assert checker.check(lines) is True


class TestPresetPermutationCheck:
    """預設規則排列檢查：一般裝備 STR + 全屬性。

    S潛=8, 罕見=6, 全屬性S=6, 全屬性罕=5。
    合格組合（數字代表三行值，不限位置）：
    865, 855, 866, 856, 886, 885, 868, 858, 888, 655, 665, 666
    """

    def _make_checker(self):
        config = AppConfig(
            equipment_type="一般裝備 (神秘、漆黑、頂培)",
            target_attribute="STR",

        )
        return ConditionChecker(config)

    def _lines(self, *values):
        """建立測試行。8/6 用 STR%，5 用全屬性%。"""
        result = []
        for v in values:
            if v == 5:
                result.append(PotentialLine("全屬性%", 5))
            elif v == 6:
                result.append(PotentialLine("STR%", 6))
            elif v == 8:
                result.append(PotentialLine("STR%", 8))
            else:
                result.append(PotentialLine("STR%", v))
        return result

    # ── 合格組合 ──

    def test_865(self):
        assert self._make_checker().check(self._lines(8, 6, 5)) is True

    def test_856(self):
        assert self._make_checker().check(self._lines(8, 5, 6)) is True

    def test_685(self):
        """S潛行不在第一排，排列檢查應能找到。"""
        assert self._make_checker().check(self._lines(6, 8, 5)) is True

    def test_658(self):
        assert self._make_checker().check(self._lines(6, 5, 8)) is True

    def test_586(self):
        assert self._make_checker().check(self._lines(5, 8, 6)) is True

    def test_568(self):
        assert self._make_checker().check(self._lines(5, 6, 8)) is True

    def test_855(self):
        assert self._make_checker().check(self._lines(8, 5, 5)) is True

    def test_866(self):
        assert self._make_checker().check(self._lines(8, 6, 6)) is True

    def test_886(self):
        assert self._make_checker().check(self._lines(8, 8, 6)) is True

    def test_885(self):
        assert self._make_checker().check(self._lines(8, 8, 5)) is True

    def test_868(self):
        assert self._make_checker().check(self._lines(8, 6, 8)) is True

    def test_858(self):
        assert self._make_checker().check(self._lines(8, 5, 8)) is True

    def test_888(self):
        assert self._make_checker().check(self._lines(8, 8, 8)) is True

    def test_655(self):
        """三行全屬性/罕見，其中一行全屬性>=6可當S潛。"""
        checker = self._make_checker()
        lines = [
            PotentialLine("全屬性%", 6),
            PotentialLine("全屬性%", 5),
            PotentialLine("全屬性%", 5),
        ]
        assert checker.check(lines) is True

    def test_665(self):
        checker = self._make_checker()
        lines = [
            PotentialLine("全屬性%", 6),
            PotentialLine("全屬性%", 6),
            PotentialLine("全屬性%", 5),
        ]
        assert checker.check(lines) is True

    def test_666(self):
        checker = self._make_checker()
        lines = [
            PotentialLine("全屬性%", 6),
            PotentialLine("全屬性%", 6),
            PotentialLine("全屬性%", 6),
        ]
        assert checker.check(lines) is True

    # ── 不合格組合 ──

    def test_554_fail(self):
        """全部低於門檻（含容錯）。"""
        checker = self._make_checker()
        lines = [
            PotentialLine("全屬性%", 3),  # S需6, 3+2=5 < 6
            PotentialLine("全屬性%", 3),
            PotentialLine("全屬性%", 2),
        ]
        assert checker.check(lines) is False

    def test_764_fail(self):
        """無 S潛行（含容錯仍不夠）。"""
        checker = self._make_checker()
        lines = [
            PotentialLine("STR%", 5),  # S需8, 5+2=7 < 8
            PotentialLine("STR%", 6),
            PotentialLine("全屬性%", 2),  # all_R需5, 2+2=4 < 5
        ]
        assert checker.check(lines) is False

    def test_755_fail(self):
        """含容錯仍不夠當 S潛。"""
        checker = self._make_checker()
        lines = [
            PotentialLine("STR%", 5),  # S需8, 5+2=7 < 8
            PotentialLine("全屬性%", 3),  # all_S需6, 3+2=5 < 6
            PotentialLine("全屬性%", 3),
        ]
        assert checker.check(lines) is False

    def test_tolerance_764_now_passes(self):
        """容錯=2: 原本 7/6/4 不合格，現在通過。"""
        checker = self._make_checker()
        lines = [
            PotentialLine("STR%", 7),   # 7+2=9 >= 8(S) ✓
            PotentialLine("STR%", 6),   # 6+2=8 >= 6(R) ✓
            PotentialLine("全屬性%", 4), # 4+2=6 >= 5(all_R) ✓
        ]
        assert checker.check(lines) is True


class TestParseCooldownLine:
    """技能冷卻時間解析"""

    def test_cooldown_basic(self):
        line = parse_potential_line("技能冷卻時間 -1秒")
        assert line.attribute == "技能冷卻時間"
        assert line.value == 1

    def test_cooldown_no_space(self):
        line = parse_potential_line("技能冷卻時間-1秒")
        assert line.attribute == "技能冷卻時間"
        assert line.value == 1

    def test_cooldown_2_seconds(self):
        line = parse_potential_line("技能冷卻時間 -2秒")
        assert line.attribute == "技能冷卻時間"
        assert line.value == 2

    def test_cooldown_simplified_mixed(self):
        """OCR 實際輸出：簡體「时」+ 繁體「間」混用"""
        line = parse_potential_line("技能冷卻时間-1秒")
        assert line.attribute == "技能冷卻時間"
        assert line.value == 1


class TestConditionCheckerHat:
    """帽子"""

    def test_hat_eternal_str_pass(self):
        config = AppConfig(
            equipment_type="帽子", is_eternal=True,
            target_attribute="STR",

        )
        checker = ConditionChecker(config)
        lines = [
            PotentialLine("STR%", 9),
            PotentialLine("STR%", 7),
            PotentialLine("全屬性%", 6),
        ]
        assert checker.check(lines) is True

    def test_hat_eternal_with_cooldown(self):
        """帽子：冷卻時間替代 S潛行"""
        config = AppConfig(
            equipment_type="帽子", is_eternal=True,
            target_attribute="STR",

        )
        checker = ConditionChecker(config)
        lines = [
            PotentialLine("技能冷卻時間", 1),
            PotentialLine("STR%", 7),
            PotentialLine("全屬性%", 6),
        ]
        assert checker.check(lines) is True

    def test_hat_eternal_cooldown_any_physical_position(self):
        """帽子：冷卻時間不一定在第1排，排列會分配到 S潛 slot"""
        config = AppConfig(
            equipment_type="帽子", is_eternal=True,
            target_attribute="STR",

        )
        checker = ConditionChecker(config)
        lines = [
            PotentialLine("STR%", 7),
            PotentialLine("全屬性%", 6),
            PotentialLine("技能冷卻時間", 1),
        ]
        assert checker.check(lines) is True

    def test_hat_double_cooldown_pass(self):
        """帽子：兩行冷卻 + 一行屬性也合格（任何排都可能出冷卻）"""
        config = AppConfig(
            equipment_type="帽子", is_eternal=True,
            target_attribute="STR",

        )
        checker = ConditionChecker(config)
        lines = [
            PotentialLine("技能冷卻時間", 1),
            PotentialLine("技能冷卻時間", 1),
            PotentialLine("STR%", 7),
        ]
        assert checker.check(lines) is True

    def test_hat_non_eternal_pass(self):
        config = AppConfig(
            equipment_type="帽子", is_eternal=False,
            target_attribute="DEX",

        )
        checker = ConditionChecker(config)
        lines = [
            PotentialLine("DEX%", 8),
            PotentialLine("全屬性%", 5),
            PotentialLine("技能冷卻時間", 1),
        ]
        assert checker.check(lines) is True

    def test_hat_non_eternal_fail(self):
        config = AppConfig(
            equipment_type="帽子", is_eternal=False,
            target_attribute="DEX",

        )
        checker = ConditionChecker(config)
        lines = [
            PotentialLine("DEX%", 5),  # S潛 needs >= 8, 5+2=7 < 8
            PotentialLine("DEX%", 3),  # 罕見 needs >= 6, 3+2=5 < 6
            PotentialLine("技能冷卻時間", 1),
        ]
        assert checker.check(lines) is False

    def test_hat_maxhp(self):
        config = AppConfig(
            equipment_type="帽子", is_eternal=True,
            target_attribute="MaxHP",
        )
        checker = ConditionChecker(config)
        lines = [
            PotentialLine("MaxHP%", 12),
            PotentialLine("MaxHP%", 9),
            PotentialLine("技能冷卻時間", 1),
        ]
        assert checker.check(lines) is True

    def test_hat_all_attr_no_cooldown(self):
        """帽子三行都是屬性也合格"""
        config = AppConfig(
            equipment_type="帽子", is_eternal=True,
            target_attribute="STR",

        )
        checker = ConditionChecker(config)
        lines = [
            PotentialLine("STR%", 9),
            PotentialLine("STR%", 7),
            PotentialLine("全屬性%", 6),
        ]
        assert checker.check(lines) is True

    def test_hat_summary_shows_cooldown(self):
        from app.core.condition import generate_condition_summary

        config = AppConfig(
            equipment_type="帽子", is_eternal=True,
            target_attribute="STR",

        )
        lines = generate_condition_summary(config)
        text = "\n".join(lines)
        assert "技能冷卻時間" in text
        assert "全屬性" in text

    def test_non_hat_no_cooldown(self):
        """非帽子裝備不接受冷卻時間"""
        config = AppConfig(
            equipment_type="永恆 / 光輝",
            target_attribute="STR",

        )
        checker = ConditionChecker(config)
        lines = [
            PotentialLine("STR%", 9),
            PotentialLine("STR%", 7),
            PotentialLine("技能冷卻時間", 1),
        ]
        assert checker.check(lines) is False


class TestConditionCheckerCustomSummary:
    """自訂模式條件摘要測試"""

    def test_custom_summary_mixed(self):
        """混合模式：指定位置 + 任意一排"""
        from app.core.condition import generate_condition_summary

        config = AppConfig(
            use_preset=False,
            custom_lines=[
                LineCondition("STR", 5, position=1),
                LineCondition("DEX", 3, position=2),
                LineCondition("全屬性", 2, position=0),
            ],
        )
        lines = generate_condition_summary(config)
        text = "\n".join(lines)
        assert "需同時符合:" in text
        assert "第 1 排" in text
        assert "STR ≥ 5%" in text
        assert "第 2 排" in text
        assert "DEX ≥ 3%" in text
        assert "且符合任一:" in text
        assert "任意一排" in text
        assert "全屬性 ≥ 2%" in text

    def test_custom_summary_fixed_only(self):
        """只有指定位置"""
        from app.core.condition import generate_condition_summary

        config = AppConfig(
            use_preset=False,
            custom_lines=[
                LineCondition("最終傷害", 20, position=1),
                LineCondition("最終傷害", 20, position=2),
                LineCondition("被動技能2", 1, position=3),
            ],
        )
        lines = generate_condition_summary(config)
        text = "\n".join(lines)
        assert "需同時符合:" in text
        assert "被動技能2" in text
        assert "第 3 排" in text

    def test_custom_summary_any_only(self):
        """只有任意一排"""
        from app.core.condition import generate_condition_summary

        config = AppConfig(
            use_preset=False,
            custom_lines=[
                LineCondition("STR", 9, position=0),
            ],
        )
        lines = generate_condition_summary(config)
        text = "\n".join(lines)
        assert "符合任一即可:" in text
        assert "任意一排" in text
        assert "STR ≥ 9%" in text

class TestConditionCheckerDynamicRows:
    """自訂模式動態排數測試（現在需要固定 3 行 OCR）"""

    def test_single_condition_any_position(self):
        config = AppConfig(
            use_preset=False,
            custom_lines=[LineCondition("STR", 5, position=0)],
        )
        checker = ConditionChecker(config)
        lines = [
            PotentialLine("STR%", 9),
            PotentialLine("DEX%", 3),
            PotentialLine("LUK%", 2),
        ]
        assert checker.check(lines) is True

    def test_single_condition_any_position_fail(self):
        config = AppConfig(
            use_preset=False,
            custom_lines=[LineCondition("STR", 5, position=0)],
        )
        checker = ConditionChecker(config)
        lines = [
            PotentialLine("STR%", 2),  # 2+2=4 < 5
            PotentialLine("DEX%", 3),
            PotentialLine("LUK%", 2),
        ]
        assert checker.check(lines) is False

    def test_two_conditions_specified_positions(self):
        config = AppConfig(
            use_preset=False,
            custom_lines=[
                LineCondition("STR", 5, position=1),
                LineCondition("DEX", 3, position=2),
            ],
        )
        checker = ConditionChecker(config)
        lines = [
            PotentialLine("STR%", 9),
            PotentialLine("DEX%", 3),
            PotentialLine("LUK%", 2),
        ]
        assert checker.check(lines) is True

    def test_not_enough_ocr_lines(self):
        config = AppConfig(
            use_preset=False,
            custom_lines=[
                LineCondition("STR", 5, position=1),
            ],
        )
        checker = ConditionChecker(config)
        lines = [PotentialLine("STR%", 9)]
        assert checker.check(lines) is False


class TestConditionCheckerCustomAnyPosition:
    """自訂模式 position=0（任意一排）測試"""

    def test_any_position_hit_first_line(self):
        config = AppConfig(
            use_preset=False,
            custom_lines=[LineCondition("STR", 9, position=0)],
        )
        checker = ConditionChecker(config)
        lines = [
            PotentialLine("STR%", 9),
            PotentialLine("DEX%", 3),
            PotentialLine("LUK%", 2),
        ]
        assert checker.check(lines) is True

    def test_any_position_hit_third_line(self):
        config = AppConfig(
            use_preset=False,
            custom_lines=[LineCondition("STR", 9, position=0)],
        )
        checker = ConditionChecker(config)
        lines = [
            PotentialLine("DEX%", 3),
            PotentialLine("LUK%", 2),
            PotentialLine("STR%", 9),
        ]
        assert checker.check(lines) is True

    def test_any_position_miss(self):
        config = AppConfig(
            use_preset=False,
            custom_lines=[LineCondition("STR", 9, position=0)],
        )
        checker = ConditionChecker(config)
        lines = [
            PotentialLine("DEX%", 3),
            PotentialLine("LUK%", 2),
            PotentialLine("INT%", 5),
        ]
        assert checker.check(lines) is False

    def test_multiple_any_position_or_logic_both_hit(self):
        """多條 任意一排 條件為 OR 邏輯，兩條都命中"""
        config = AppConfig(
            use_preset=False,
            custom_lines=[
                LineCondition("STR", 5, position=0),
                LineCondition("DEX", 3, position=0),
            ],
        )
        checker = ConditionChecker(config)
        lines = [
            PotentialLine("STR%", 9),
            PotentialLine("DEX%", 3),
            PotentialLine("LUK%", 2),
        ]
        assert checker.check(lines) is True

    def test_multiple_any_position_or_logic_one_hit(self):
        """多條 任意一排 OR 邏輯，只有一條命中也通過"""
        config = AppConfig(
            use_preset=False,
            custom_lines=[
                LineCondition("STR", 5, position=0),
                LineCondition("DEX", 3, position=0),
            ],
        )
        checker = ConditionChecker(config)
        lines = [
            PotentialLine("STR%", 9),
            PotentialLine("LUK%", 7),
            PotentialLine("INT%", 2),
        ]
        assert checker.check(lines) is True

    def test_multiple_any_position_or_logic_none_hit(self):
        """多條 任意一排 OR 邏輯，全部未命中則失敗"""
        config = AppConfig(
            use_preset=False,
            custom_lines=[
                LineCondition("STR", 5, position=0),
                LineCondition("DEX", 3, position=0),
            ],
        )
        checker = ConditionChecker(config)
        lines = [
            PotentialLine("LUK%", 9),
            PotentialLine("INT%", 7),
            PotentialLine("MaxHP%", 2),
        ]
        assert checker.check(lines) is False

    def test_mixed_specified_and_any(self):
        """混合：指定位置 + 任意一排"""
        config = AppConfig(
            use_preset=False,
            custom_lines=[
                LineCondition("STR", 9, position=1),
                LineCondition("DEX", 3, position=0),
            ],
        )
        checker = ConditionChecker(config)
        lines = [
            PotentialLine("STR%", 9),
            PotentialLine("LUK%", 7),
            PotentialLine("DEX%", 5),
        ]
        assert checker.check(lines) is True

    def test_specified_position_wrong_line(self):
        """指定第2排 STR，但 STR 在第1排 → 失敗"""
        config = AppConfig(
            use_preset=False,
            custom_lines=[
                LineCondition("STR", 9, position=2),
            ],
        )
        checker = ConditionChecker(config)
        lines = [
            PotentialLine("STR%", 9),
            PotentialLine("DEX%", 3),
            PotentialLine("LUK%", 2),
        ]
        assert checker.check(lines) is False

    def test_passive_skill2_any_position(self):
        """被動技能2 + 任意一排"""
        config = AppConfig(
            use_preset=False,
            custom_lines=[
                LineCondition("最終傷害", 20, position=0),
                LineCondition("被動技能2", 1, position=0),
            ],
        )
        checker = ConditionChecker(config)
        lines = [
            PotentialLine("DEX%", 3),
            PotentialLine("最終傷害%", 20),
            PotentialLine("被動技能2", 0, "依照被動技能 2 來增加"),
        ]
        assert checker.check(lines) is True


class TestAbsoluteCubeTwoLines:
    """絕對附加方塊只洗 2 排潛能，且兩排都是 S潛等級。"""

    def test_get_num_lines_absolute(self):
        assert get_num_lines("絕對附加方塊") == 2
        assert get_num_lines("絕對附加方塊 (僅洗兩排)") == 2

    def test_get_num_lines_normal(self):
        assert get_num_lines("珍貴附加方塊 (粉紅色)") == 3
        assert get_num_lines("恢復附加方塊 (紅色)") == 3

    def test_parse_potential_lines_two_rows(self):
        fragments = [
            ("STR+9%", 10.0),
            ("DEX+9%", 40.0),
        ]
        lines = parse_potential_lines(fragments, num_rows=2)
        assert len(lines) == 2
        assert lines[0].attribute == "STR%"
        assert lines[1].attribute == "DEX%"

    def test_preset_two_lines_pass(self):
        """兩排 S潛 STR 9% 通過。"""
        config = AppConfig(
            cube_type="絕對附加方塊",
            equipment_type="永恆 / 光輝",
            target_attribute="STR",
            use_preset=True,
        )
        checker = ConditionChecker(config)
        lines = [
            PotentialLine("STR%", 9),
            PotentialLine("STR%", 9),
        ]
        assert checker.check(lines) is True

    def test_preset_two_lines_fail_below_s_tier(self):
        """6% 即使加容錯 2 也只有 8，仍低於 S潛 9%。"""
        config = AppConfig(
            cube_type="絕對附加方塊",
            equipment_type="永恆 / 光輝",
            target_attribute="STR",
            use_preset=True,
        )
        checker = ConditionChecker(config)
        lines = [
            PotentialLine("STR%", 9),
            PotentialLine("STR%", 6),
        ]
        assert checker.check(lines) is False

    def test_preset_two_lines_with_all_stats(self):
        """S潛 STR 9% + S潛 全屬性 7% 通過。"""
        config = AppConfig(
            cube_type="絕對附加方塊",
            equipment_type="永恆 / 光輝",
            target_attribute="STR",
            use_preset=True,
        )
        checker = ConditionChecker(config)
        lines = [
            PotentialLine("STR%", 9),
            PotentialLine("全屬性%", 7),
        ]
        assert checker.check(lines) is True

    def test_preset_two_lines_all_stats_below_s_fail(self):
        """全屬性 4%（加容錯 2 = 6，仍低於 S潛 7%）不通過。"""
        config = AppConfig(
            cube_type="絕對附加方塊",
            equipment_type="永恆 / 光輝",
            target_attribute="STR",
            use_preset=True,
        )
        checker = ConditionChecker(config)
        lines = [
            PotentialLine("STR%", 9),
            PotentialLine("全屬性%", 4),
        ]
        assert checker.check(lines) is False

    def test_preset_two_lines_insufficient_lines(self):
        """只有 1 排不夠，不通過。"""
        config = AppConfig(
            cube_type="絕對附加方塊",
            equipment_type="永恆 / 光輝",
            target_attribute="STR",
            use_preset=True,
        )
        checker = ConditionChecker(config)
        lines = [PotentialLine("STR%", 9)]
        assert checker.check(lines) is False

    def test_all_attrs_two_lines(self):
        """所有屬性模式：兩排同屬性 S潛通過。"""
        config = AppConfig(
            cube_type="絕對附加方塊",
            equipment_type="永恆 / 光輝",
            target_attribute="所有屬性",
            use_preset=True,
        )
        checker = ConditionChecker(config)
        lines = [
            PotentialLine("DEX%", 9),
            PotentialLine("DEX%", 9),
        ]
        assert checker.check(lines) is True

    def test_all_attrs_two_lines_below_s_fail(self):
        """所有屬性模式：6% + 容錯 2 = 8 < S潛 9%，不通過。"""
        config = AppConfig(
            cube_type="絕對附加方塊",
            equipment_type="永恆 / 光輝",
            target_attribute="所有屬性",
            use_preset=True,
        )
        checker = ConditionChecker(config)
        lines = [
            PotentialLine("DEX%", 9),
            PotentialLine("DEX%", 6),
        ]
        assert checker.check(lines) is False

    def test_custom_and_two_lines(self):
        """自訂模式逐排指定 2 排。"""
        config = AppConfig(
            cube_type="絕對附加方塊",
            equipment_type="永恆 / 光輝",
            use_preset=False,
            custom_lines=[
                LineCondition("STR", 9, position=1),
                LineCondition("DEX", 9, position=2),
            ],
        )
        checker = ConditionChecker(config)
        lines = [
            PotentialLine("STR%", 9),
            PotentialLine("DEX%", 9),
        ]
        assert checker.check(lines) is True

    def test_custom_or_two_lines(self):
        """自訂模式符合任一，2 排。"""
        config = AppConfig(
            cube_type="絕對附加方塊",
            equipment_type="永恆 / 光輝",
            use_preset=False,
            custom_lines=[
                LineCondition("STR", 9, position=0),
                LineCondition("DEX", 9, position=0),
            ],
        )
        checker = ConditionChecker(config)
        lines = [
            PotentialLine("STR%", 9),
            PotentialLine("LUK%", 5),
        ]
        assert checker.check(lines) is True

    def test_custom_or_two_lines_fail(self):
        """自訂模式符合任一，2 排都不符合。"""
        config = AppConfig(
            cube_type="絕對附加方塊",
            equipment_type="永恆 / 光輝",
            use_preset=False,
            custom_lines=[
                LineCondition("STR", 9, position=0),
                LineCondition("DEX", 9, position=0),
            ],
        )
        checker = ConditionChecker(config)
        lines = [
            PotentialLine("LUK%", 9),
            PotentialLine("INT%", 5),
        ]
        assert checker.check(lines) is False

    def test_summary_preset_single_attr(self):
        """摘要：絕對附加方塊只顯示 S潛數值，不顯示 or。"""
        config = AppConfig(
            cube_type="絕對附加方塊",
            equipment_type="主武器 / 徽章 (米特拉)",
            target_attribute="物理攻擊力",
            use_preset=True,
        )
        summary = generate_condition_summary(config)
        assert summary == ["兩排: 物理攻擊力 13%"]

    def test_summary_preset_with_all_stats(self):
        """摘要：絕對附加方塊 STR + 全屬性，不顯示 or。"""
        config = AppConfig(
            cube_type="絕對附加方塊",
            equipment_type="永恆 / 光輝",
            target_attribute="STR",
            use_preset=True,
        )
        summary = generate_condition_summary(config)
        assert summary == [
            "兩排需符合以下任一:",
            "  · STR 9%",
            "  · 全屬性 7%",
        ]

    def test_summary_all_attrs(self):
        """摘要：絕對附加方塊所有屬性模式標題為「兩排」。"""
        config = AppConfig(
            cube_type="絕對附加方塊",
            equipment_type="永恆 / 光輝",
            target_attribute="所有屬性",
            use_preset=True,
        )
        summary = generate_condition_summary(config)
        assert summary[0] == "兩排需為同一屬性 (可混搭全屬性):"

    def test_tolerance_applies(self):
        """OCR 容錯 tolerance=2 套用在絕對附加方塊。"""
        config = AppConfig(
            cube_type="絕對附加方塊",
            equipment_type="永恆 / 光輝",
            target_attribute="STR",
            use_preset=True,
        )
        checker = ConditionChecker(config)
        # 9-2=7, 所以 7 應該通過
        lines = [
            PotentialLine("STR%", 7),
            PotentialLine("STR%", 7),
        ]
        assert checker.check(lines) is True
