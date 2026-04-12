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

    def test_crit_damage_with_space(self):
        """爆擊 傷害（中間有空格）應辨識為爆擊傷害，非傷害"""
        line = parse_potential_line("爆擊 傷害 +8%")
        assert line.attribute == "爆擊傷害%"
        assert line.value == 8

    def test_crit_damage_no_space(self):
        """爆擊傷害（無空格）正常辨識"""
        line = parse_potential_line("爆擊傷害 +8%")
        assert line.attribute == "爆擊傷害%"
        assert line.value == 8

    def test_crit_damage_not_misread_as_damage(self):
        """爆擊傷害不應被誤判為傷害"""
        line = parse_potential_line("爆擊 傷害+8%")
        assert line.attribute != "傷害%"

    def test_final_damage_with_space(self):
        """最終 傷害（中間有空格）應辨識為最終傷害，非傷害"""
        line = parse_potential_line("最終 傷害 +20%")
        assert line.attribute == "最終傷害%"
        assert line.value == 20

    def test_crit_damage_fullwidth_space(self):
        """爆擊\u3000傷害（全形空格）應辨識為爆擊傷害"""
        line = parse_potential_line("爆擊\u3000傷害 +8%")
        assert line.attribute == "爆擊傷害%"
        assert line.value == 8

    def test_final_damage_fullwidth_space(self):
        """最終\u3000傷害（全形空格）應辨識為最終傷害，非傷害"""
        line = parse_potential_line("最終\u3000傷害 +20%")
        assert line.attribute == "最終傷害%"
        assert line.value == 20

    def test_boss_damage_fullwidth_space(self):
        """攻擊Boss怪物時\u3000傷害（全形空格）應辨識為Boss傷害"""
        line = parse_potential_line("攻擊Boss怪物時\u3000傷害 +40%")
        assert line.attribute == "Boss傷害%"
        assert line.value == 40

    def test_boss_damage_real_game_format(self):
        """遊戲實際格式：攻擊Boss怪物時傷害 +12%（數值前有半形空白）"""
        line = parse_potential_line("攻擊Boss怪物時傷害 +12%")
        assert line.attribute == "Boss傷害%"
        assert line.value == 12

    def test_boss_damage_no_space(self):
        """攻擊Boss怪物時傷害+12%（無空白）應辨識為Boss傷害"""
        line = parse_potential_line("攻擊Boss怪物時傷害+12%")
        assert line.attribute == "Boss傷害%"
        assert line.value == 12

    # --- 20260406 log 新增 OCR 修正 ---

    def test_ocr_fix_crit_damage_baohua(self):
        """爆華傷害 → 爆擊傷害"""
        line = parse_potential_line("爆華傷害+1%")
        assert line.attribute == "爆擊傷害%"
        assert line.value == 1

    def test_ocr_fix_crit_damage_baohua_pei(self):
        """爆華佩害 → 爆擊傷害（爆華+佩害 雙重誤讀）"""
        line = parse_potential_line("爆華佩害 +3%")
        assert line.attribute == "爆擊傷害%"
        assert line.value == 3

    def test_ocr_fix_crit_damage_yang(self):
        """煬擊傷害 → 爆擊傷害（爆→煬）"""
        line = parse_potential_line("煬擊傷害+3%")
        assert line.attribute == "爆擊傷害%"
        assert line.value == 3

    def test_ocr_fix_luk_as_lik(self):
        """LIK → LUK"""
        line = parse_potential_line("LIK+9%")
        assert line.attribute == "LUK%"
        assert line.value == 9

    def test_ocr_fix_dex_as_dik(self):
        """DIK → DEX"""
        line = parse_potential_line("DIK+9%")
        assert line.attribute == "DEX%"
        assert line.value == 9

    def test_ocr_fix_you_hai(self):
        """優害 → 傷害"""
        line = parse_potential_line("最終優害：+25%")
        assert line.attribute == "最終傷害%"
        assert line.value == 25

    def test_ocr_fix_xin_hai(self):
        """信害 → 傷害"""
        line = parse_potential_line("最終信害：+25%")
        assert line.attribute == "最終傷害%"
        assert line.value == 25

    def test_ocr_fix_shang_xi(self):
        """傷喜 → 傷害（害→喜）"""
        line = parse_potential_line("最終傷喜：+25%")
        assert line.attribute == "最終傷害%"
        assert line.value == 25

    def test_ocr_fix_ji_xi(self):
        """集喜 → 傷害（傷害→集喜 雙字誤讀）"""
        line = parse_potential_line("最終集喜：+25%")
        assert line.attribute == "最終傷害%"
        assert line.value == 25

    def test_ocr_fix_final_damage_missing_shang(self):
        """最終害 → 最終傷害（傷 被吃掉）"""
        line = parse_potential_line("最終害：+25%")
        assert line.attribute == "最終傷害%"
        assert line.value == 25

    def test_ocr_fix_wushi_simplified(self):
        """無视 → 無視（簡體 视）"""
        line = parse_potential_line("無视怪物防禦率：+50%")
        assert line.attribute == "無視怪物防禦%"
        assert line.value == 50

    def test_ocr_fix_int_as_im(self):
        """IM → INT（M↔N 誤讀）"""
        line = parse_potential_line("以角色等級為準每9級IM+2")
        assert line.attribute == "每級INT"
        assert line.value == 2

    def test_ocr_fix_hp_recovery_complex(self):
        """H恢递具及恢覆技能效率 → HP恢復道具及恢復技能效率"""
        line = parse_potential_line("H恢递具及恢覆技能效率+30%")
        assert line.attribute == "HP恢復效率%"
        assert line.value == 30

    # --- 20260409 log 新增 OCR 修正 ---

    def test_ocr_fix_final_damage_dan_hai(self):
        """最终但害 → 最終傷害（傷→但）"""
        line = parse_potential_line("最终但害：+25%")
        assert line.attribute == "最終傷害%"
        assert line.value == 25

    def test_ocr_fix_final_damage_yi_hai(self):
        """最终亿害 → 最終傷害（傷→亿）"""
        line = parse_potential_line("最终亿害：+25%")
        assert line.attribute == "最終傷害%"
        assert line.value == 25

    def test_ocr_fix_crit_rate_baocao(self):
        """爆草機率 → 爆擊機率（擊→草）"""
        line = parse_potential_line("爆草機率：+25%")
        assert line.attribute == "爆擊機率%"
        assert line.value == 25

    def test_ocr_fix_ignore_def_missing_yu(self):
        """無视怪物防率 → 無視怪物防禦率（禦 被吃掉）"""
        line = parse_potential_line("無视怪物防率：+50%")
        assert line.attribute == "無視怪物防禦%"
        assert line.value == 50

    def test_all_stats_flat_value_is_unknown(self):
        """全属性：+25（萌獸平值，無 %）→ 未知（非目標潛能）"""
        line = parse_potential_line("全属性：+25")
        assert line.attribute == "未知"

    def test_dex_regex_no_false_positive_after_cjk(self):
        """全屬性EX+18%（EX 前有中文）不應誤判為 DEX%"""
        line = parse_potential_line("全屬性EX+18%")
        assert line.attribute != "DEX%"

    # --- 20260409 log 新增 OCR 修正（第二批） ---

    def test_ocr_fix_crit_damage_jiao_hai(self):
        """爆草焦害 → 爆擊傷害（焦害→傷害）"""
        line = parse_potential_line("爆草焦害+1%")
        assert line.attribute == "爆擊傷害%"
        assert line.value == 1

    def test_ocr_fix_crit_damage_qi_hai(self):
        """爆擊氣害 → 爆擊傷害（氣害→傷害）"""
        line = parse_potential_line("爆擊氣害+1%")
        assert line.attribute == "爆擊傷害%"
        assert line.value == 1

    def test_ocr_fix_str_as_ste(self):
        """STE → STR（R→E 誤讀）"""
        line = parse_potential_line("STE+19")
        assert line.attribute == "STR"
        assert line.value == 19

    def test_ocr_fix_dex_as_dt(self):
        """DT+21 → DEX+21（EX→T 誤讀）"""
        line = parse_potential_line("DT+21")
        assert line.attribute == "DEX"
        assert line.value == 21

    def test_ocr_fix_luk_as_ljk(self):
        """LJK → LUK（U→J 誤讀）"""
        line = parse_potential_line("LJK+9%")
        assert line.attribute == "LUK%"
        assert line.value == 9

    def test_ocr_fix_maxhp_as_uxhp(self):
        """uxHP → MaxHP（M 被吃掉 + a→u）"""
        line = parse_potential_line("uxHP+315")
        assert line.attribute == "MaxHP"
        assert line.value == 315

    def test_ocr_fix_lowercase_ex_percent(self):
        """ex+7% → DEX+7% → DEX%（小寫修正）"""
        line = parse_potential_line("ex+7%")
        assert line.attribute == "DEX%"
        assert line.value == 7

    def test_ocr_fix_lowercase_ex_flat(self):
        """ex+19 → DEX+19 → flat DEX（不被 PERCENT_AS_NINE 誤判為 DEX% 1）"""
        line = parse_potential_line("ex+19")
        assert line.attribute == "DEX"
        assert line.value == 19

    # --- 用戶整理第三批 OCR 修正 ---

    def test_ocr_fix_crit_damage_bao_ji_dan_hai(self):
        """爆吉但害 → 爆擊傷害"""
        line = parse_potential_line("爆吉但害+3%")
        assert line.attribute == "爆擊傷害%"
        assert line.value == 3

    def test_ocr_fix_crit_damage_yu_hua_jiang_hai(self):
        """煜華僵害 → 爆擊傷害"""
        line = parse_potential_line("煜華僵害+1%")
        assert line.attribute == "爆擊傷害%"
        assert line.value == 1

    def test_ocr_fix_crit_damage_bao_hua_jiang_hai(self):
        """爆華僵害 → 爆擊傷害"""
        line = parse_potential_line("爆華僵害+3%")
        assert line.attribute == "爆擊傷害%"
        assert line.value == 3

    def test_ocr_fix_dex_as_det(self):
        """DET → DEX"""
        line = parse_potential_line("DET+7%")
        assert line.attribute == "DEX%"
        assert line.value == 7

    def test_ocr_fix_dex_as_dei(self):
        """DEI → DEX"""
        line = parse_potential_line("DEI+9%")
        assert line.attribute == "DEX%"
        assert line.value == 9

    def test_ocr_fix_dex_as_de(self):
        """DE → DEX（X 被吃掉）"""
        line = parse_potential_line("DE+6%")
        assert line.attribute == "DEX%"
        assert line.value == 6

    def test_ocr_fix_dex_as_dek(self):
        """DEK → DEX"""
        line = parse_potential_line("DEK+9%")
        assert line.attribute == "DEX%"
        assert line.value == 9

    def test_ocr_fix_dex_as_dey(self):
        """DEY → DEX"""
        line = parse_potential_line("DEY+7%")
        assert line.attribute == "DEX%"
        assert line.value == 7

    def test_ocr_fix_int_as_iht(self):
        """IHT → INT（N→H 誤讀）"""
        line = parse_potential_line("IHT+6%")
        assert line.attribute == "INT%"
        assert line.value == 6

    def test_ocr_fix_int_as_imt(self):
        """IMT → INT（N→M 誤讀，3 字元）"""
        line = parse_potential_line("IMT+8%")
        assert line.attribute == "INT%"
        assert line.value == 8

    def test_ocr_fix_int_as_iint(self):
        """IINT → INT（多讀一個 I）"""
        line = parse_potential_line("IINT+9%")
        assert line.attribute == "INT%"
        assert line.value == 9

    # --- M3: 泛化辨識（受限 M1' regex + scoped pairs）---
    # tech-spec: docs/features/ocr-matching/2-tech-spec.md Section 6.1 / 6.2.2

    # 6.1 A 組：傷 被替換（suffix pair 路徑）

    def test_m3_crit_damage_baoqing_huihai(self):
        """爆擎悔害 → 爆擊傷害（pair 悔害→傷害 + M1' regex）"""
        line = parse_potential_line("爆擎悔害+9%")
        assert line.attribute == "爆擊傷害%"
        assert line.value == 9

    def test_m3_crit_damage_baoqing_wuhai(self):
        """爆擎侮害 → 爆擊傷害（pair 侮害→傷害 + M1' regex）"""
        line = parse_potential_line("爆擎侮害+9%")
        assert line.attribute == "爆擊傷害%"
        assert line.value == 9

    def test_m3_crit_damage_baoluan_shouhai(self):
        """爆挛售害 → 爆擊傷害（pair 售害→傷害 + M1' regex）"""
        line = parse_potential_line("爆挛售害+9%")
        assert line.attribute == "爆擊傷害%"
        assert line.value == 9

    # 6.1 B 組：傷 被吃掉（scoped pair 路徑）

    def test_m3_crit_damage_baohua_missing_shang(self):
        """爆華害 → 爆擊傷害（scoped pair 必須在 爆華→爆擊 之前）"""
        line = parse_potential_line("爆華害+9%")
        assert line.attribute == "爆擊傷害%"
        assert line.value == 9

    def test_m3_crit_damage_baoluan_missing_shang(self):
        """爆挛害 → 爆擊傷害（scoped pair）"""
        line = parse_potential_line("爆挛害+9%")
        assert line.attribute == "爆擊傷害%"
        assert line.value == 9

    def test_m3_crit_damage_baoqing_missing_shang(self):
        """爆擎害 → 爆擊傷害（scoped pair）"""
        line = parse_potential_line("爆擎害+9%")
        assert line.attribute == "爆擊傷害%"
        assert line.value == 9

    # 6.1 C 組：多出字元

    def test_m3_crit_damage_extra_xin(self):
        """爆馨擊傷害 → 爆擊傷害（scoped pair 爆馨擊→爆擊）"""
        line = parse_potential_line("爆馨擊傷害+9%")
        assert line.attribute == "爆擊傷害%"
        assert line.value == 9

    # 6.1 延伸：真實案例清單中 pair 未涵蓋、靠 M1' regex 直接吸收的變體

    def test_m3_crit_damage_baoqing_jiaohai(self):
        """爆擎焦害 → 爆擊傷害（焦害→傷害 pair + M1' regex，擎 非 pair 對象）"""
        line = parse_potential_line("爆擎焦害+9%")
        assert line.attribute == "爆擊傷害%"
        assert line.value == 9

    def test_m3_crit_damage_baohua_shangxi(self):
        """爆華傷喜 → 爆擊傷害（爆華→爆擊 + 傷喜→傷害 既有 pair）"""
        line = parse_potential_line("爆華傷喜+9%")
        assert line.attribute == "爆擊傷害%"
        assert line.value == 9

    def test_m3_crit_damage_baoluan_shanghai(self):
        """爆挛傷害 → 爆擊傷害（挛 非 pair 對象，完全靠 M1' regex 吸收）"""
        line = parse_potential_line("爆挛傷害+9%")
        assert line.attribute == "爆擊傷害%"
        assert line.value == 9

    def test_m3_crit_damage_baoxin_shanghai(self):
        """爆馨傷害 → 爆擊傷害（馨 非 pair 對象，完全靠 M1' regex 吸收）"""
        line = parse_potential_line("爆馨傷害+9%")
        assert line.attribute == "爆擊傷害%"
        assert line.value == 9

    def test_m3_crit_damage_jp_kanji_geki_jiaohai(self):
        """爆撃焦害 → 爆擊傷害（日文漢字 撃，無 pair，靠 M1' regex 吸收）

        目前 _OCR_FIXES 只有 攻撃→攻擊，不包含一般的 撃→擊；M1' `.{1,3}`
        直接吸收 撃 作為中段 1 字，與原爆擊傷害語意對齊。
        """
        line = parse_potential_line("爆撃焦害+9%")
        assert line.attribute == "爆擊傷害%"
        assert line.value == 9

    def test_m3_crit_damage_baohua_hengxi(self):
        """爆華恆喜 → 爆擊傷害（爆華→爆擊 + M1' 吸收 擊恆 作為中段 2 字，[害喜] 命中 喜）"""
        line = parse_potential_line("爆華恆喜+9%")
        assert line.attribute == "爆擊傷害%"
        assert line.value == 9

    def test_m3_crit_damage_baoxin_pianxi(self):
        """爆馨偏喜 → 爆擊傷害（無 pair，M1' 吸收 馨偏 2 字 + 喜）"""
        line = parse_potential_line("爆馨偏喜+9%")
        assert line.attribute == "爆擊傷害%"
        assert line.value == 9

    # 6.1 D 組：英文屬性誤讀

    def test_m3_dex_as_dx(self):
        """DX → DEX（_OCR_DEX_FIXES 擴充）"""
        line = parse_potential_line("DX+9%")
        assert line.attribute == "DEX%"
        assert line.value == 9

    def test_m3_int_as_jnt(self):
        """JNT → INT（_OCR_INT_FIXES 擴充，I→J）"""
        line = parse_potential_line("JNT+9%")
        assert line.attribute == "INT%"
        assert line.value == 9

    def test_m3_int_as_tit(self):
        """TIT → INT（_OCR_INT_FIXES 擴充，IN→TI 錯位）"""
        line = parse_potential_line("TIT+9%")
        assert line.attribute == "INT%"
        assert line.value == 9

    def test_m3_int_as_gong_t(self):
        """工T → INT（pair 工T→INT）"""
        line = parse_potential_line("工T+9%")
        assert line.attribute == "INT%"
        assert line.value == 9

    def test_m3_regex_boundary_middle_length_upper_reject(self):
        """M1' 中段 {1,3} 上界：4 字元 middle 必須 reject

        合成 adversarial input 驗證 regex 不會因 middle 加長而誤抓；
        若 {1,3} 被改成 {1,4} 或無上界，此測試會失敗。
        {1,3} 上界是為了限制 regex 比對範圍（避免 runaway 匹配跨越整行），
        非針對特定字元，符合「只收真實觀察」方法論。
        """
        line = parse_potential_line("爆擎擎擎擎害+9%")
        assert line.attribute == "未知"
        assert line.value == 0

    def test_m3_regex_boundary_middle_length_3_accept(self):
        """M1' 中段 {1,3} 下界+上界正向測試：3 字元 middle 必須 accept

        若 {1,3} 被改成 {1,2}，此測試會失敗。
        """
        line = parse_potential_line("爆擎擎擎害+9%")
        assert line.attribute == "爆擊傷害%"
        assert line.value == 9


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
        known = [ln for ln in lines if ln.attribute != "未知"]
        assert len(known) == 1
        assert known[0].attribute == "STR%"
        assert known[0].value == 9

    def test_multiple_lines_merged(self):
        """多行潛能，碎片分布在 3 個物理行"""
        frags = [("STR", 10.0), ("+9%", 10.5), ("DEX+7%", 30.0), ("LUK +6%", 50.0)]
        lines = parse_potential_lines(frags)
        assert len(lines) == 3
        attrs = {ln.attribute for ln in lines}
        assert "STR%" in attrs
        assert "DEX%" in attrs
        assert "LUK%" in attrs

    def test_japanese_kanji_fix(self):
        """攻撃 → 攻擊 修正後能解析"""
        lines = parse_potential_lines(self._same_row(["物理攻撃力", "+13%"]))
        known = [ln for ln in lines if ln.attribute != "未知"]
        assert len(known) == 1
        assert known[0].attribute == "物理攻擊力%"
        assert known[0].value == 13

    def test_simplified_chinese_fix(self):
        """簡體字修正：最终→最終, 全国性→全屬性"""
        frags = [("全国性：+7%", 10.0), ("最终傷害：+20%", 30.0)]
        lines = parse_potential_lines(frags)
        known = [ln for ln in lines if ln.attribute != "未知"]
        assert len(known) == 2
        assert known[0].attribute == "全屬性%"
        assert known[0].value == 7
        assert known[1].attribute == "最終傷害%"
        assert known[1].value == 20

    def test_positional_order_preserved(self):
        """結果應按 y 座標排序（物理位置），而非 ATTRIBUTE_PATTERNS 順序"""
        frags = [("最終傷害：+20%", 10.0), ("STR：+9%", 30.0)]
        lines = parse_potential_lines(frags)
        known = [ln for ln in lines if ln.attribute != "未知"]
        assert len(known) == 2
        assert known[0].attribute == "最終傷害%"
        assert known[1].attribute == "STR%"

    def test_cross_fragment_percent_not_matched(self):
        """'DEX +18' 不應因隔壁碎片的 '%' 被誤判為 DEX +18%"""
        frags = self._three_rows("MaxMP+300", "DEX +18", "%9+INI")
        lines = parse_potential_lines(frags)
        attrs = [ln.attribute for ln in lines]
        assert "DEX%" not in attrs

    def test_cross_fragment_percent_second_case(self):
        """'STR +18' 不應因隔壁碎片的 '%' 被誤判為 STR +18%"""
        frags = [("STR +18", 10.0), ("STR +18", 10.5), ("%9+", 30.0), ("XEI", 50.0)]
        lines = parse_potential_lines(frags)
        attrs = [ln.attribute for ln in lines]
        assert "STR%" not in attrs

    def test_pet_cube_ocr_misread(self):
        """實際萌獸方塊 OCR 結果（含簡繁混雜）"""
        frags = [("全国性：+20", 10.0), ("DEX", 10.5), ("最终傷害：+20%", 30.0), ("：+14%", 50.0)]
        lines = parse_potential_lines(frags)
        attrs = [ln.attribute for ln in lines]
        assert "最終傷害%" in attrs

    def test_boss_damage_merged_fragments(self):
        """攻擊Boss怪物時傷害 在碎片合併路徑下應辨識為 Boss傷害（OCR 拆成多段）"""
        frags = self._same_row(["攻擊Boss", "怪物時傷害", "+12%"])
        lines = parse_potential_lines(frags)
        known = [ln for ln in lines if ln.attribute != "未知"]
        assert len(known) == 1
        assert known[0].attribute == "Boss傷害%"
        assert known[0].value == 12

    def test_always_returns_3_lines(self):
        """永遠回傳恰好 3 個 PotentialLine"""
        lines = parse_potential_lines([("STR +9%", 10.0)])
        assert len(lines) == 3

    def test_empty_input(self):
        """空輸入回傳 3 個未知"""
        lines = parse_potential_lines([])
        assert len(lines) == 3
        assert all(ln.attribute == "未知" for ln in lines)

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

    # --- M3: 跨行合併路徑（6.2.3 + B/C 組 merge coverage）---

    def test_m3_scoped_pair_blocks_cross_row_concat_case_a(self):
        """Tech-spec 6.2.3 Case A：pair 層阻斷跨行合併路徑

        兩行 售害+9% 與 售害+7% 各自被 suffix pair 拉回 傷害%，
        合併條件 #1（兩行皆未知）不成立 → 不進入合併路徑 → 無機會觸發 M1'。
        """
        frags = self._three_rows("售害+9%", "售害+7%", "")
        lines = parse_potential_lines(frags)
        assert lines[0].attribute == "傷害%"
        assert lines[0].value == 9
        assert lines[1].attribute == "傷害%"
        assert lines[1].value == 7

    def test_m3_scoped_pair_order_locked_via_merge_raw_text(self):
        """鎖住順序不變量：scoped 爆華害→爆擊傷害 **必須** 在 broad 爆華→爆擊 之前

        parse_potential_lines 每行走 _parse_merged_text，後者將 raw_text 設為
        regex 匹配後的 m.group(0)（_fix_ocr_text 正規化後）。

        - 正確順序：scoped pair 先觸發 → `爆華害+9%` → `爆擊傷害+9%` → raw_text = '爆擊傷害+9%'
        - 錯誤順序：broad pair 先觸發 → `爆華害+9%` → `爆擊害+9%` → M1' via 傷? 仍命中，
          attribute/value 正確但 raw_text = '爆擊害+9%'

        若有開發者把 scoped pair 移到 broad pair 之後，本測試的 raw_text 斷言會失敗。
        """
        lines = parse_potential_lines([("爆華害+9%", 10.0)], num_rows=3)
        assert lines[0].attribute == "爆擊傷害%"
        assert lines[0].value == 9
        # Canonical raw_text — 若 scoped pair 被 broad pair preempt 則退化為 '爆擊害+9%'
        assert lines[0].raw_text == "爆擊傷害+9%"

    def test_m3_crit_damage_baohua_missing_merged(self):
        """爆華害 在碎片合併路徑下仍命中 爆擊傷害（scoped pair 在合併前後都生效）"""
        frags = self._same_row(["爆華害", "+9%"])
        lines = parse_potential_lines(frags)
        known = [ln for ln in lines if ln.attribute != "未知"]
        assert len(known) == 1
        assert known[0].attribute == "爆擊傷害%"
        assert known[0].value == 9

    def test_m3_crit_damage_extra_xin_merged(self):
        """爆馨擊 + 傷害+9% 跨碎片合併後應命中 爆擊傷害"""
        frags = self._same_row(["爆馨擊", "傷害+9%"])
        lines = parse_potential_lines(frags)
        known = [ln for ln in lines if ln.attribute != "未知"]
        assert len(known) == 1
        assert known[0].attribute == "爆擊傷害%"
        assert known[0].value == 9

    def test_m3_dx_merged_fragments(self):
        """DX 與數值分拆為不同碎片時仍被修正為 DEX%"""
        frags = self._same_row(["DX", "+9%"])
        lines = parse_potential_lines(frags)
        known = [ln for ln in lines if ln.attribute != "未知"]
        assert len(known) == 1
        assert known[0].attribute == "DEX%"
        assert known[0].value == 9


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


class TestConditionCheckerSubWeaponConvertible:
    """副手雙攻擊力 (可轉換) — 三排全物攻 或 三排全魔攻皆合格；混合拒絕。

    遊戲機制：副手可透過防具轉換整件互換物攻／魔攻，故兩種屬性皆視為合格。
    整件轉換語意（D1）：混合洗出（例：2 物 1 魔）不通過。
    """

    _ATTR = "物理/魔法攻擊力 (可轉換)"
    _SUB = "輔助武器 (副手)"

    def _make_config(self, cube_type: str = "珍貴附加方塊 (粉紅色)") -> AppConfig:
        return AppConfig(
            cube_type=cube_type,
            equipment_type=self._SUB,
            target_attribute=self._ATTR,
        )

    # ── C1-C7：3 排方塊 ──

    def test_three_rows_pure_phys_pass(self):
        """C1：三排純物攻（S 13 + 罕 10 + 罕 9）通過。"""
        checker = ConditionChecker(self._make_config())
        lines = [
            PotentialLine("物理攻擊力%", 13),
            PotentialLine("物理攻擊力%", 10),
            PotentialLine("物理攻擊力%", 9),
        ]
        assert checker.check(lines) is True

    def test_three_rows_pure_magic_pass(self):
        """C2：三排純魔攻通過。"""
        checker = ConditionChecker(self._make_config())
        lines = [
            PotentialLine("魔法攻擊力%", 13),
            PotentialLine("魔法攻擊力%", 10),
            PotentialLine("魔法攻擊力%", 9),
        ]
        assert checker.check(lines) is True

    def test_three_rows_mixed_reject(self):
        """C3：混合洗出（2 物 1 魔）拒絕 — 整件轉換語意。"""
        checker = ConditionChecker(self._make_config())
        lines = [
            PotentialLine("物理攻擊力%", 13),
            PotentialLine("魔法攻擊力%", 10),
            PotentialLine("物理攻擊力%", 9),
        ]
        assert checker.check(lines) is False

    def test_three_rows_mixed_all_high_reject(self):
        """C4：即便門檻都達標，混合也拒絕。"""
        checker = ConditionChecker(self._make_config())
        lines = [
            PotentialLine("物理攻擊力%", 13),
            PotentialLine("魔法攻擊力%", 12),
            PotentialLine("物理攻擊力%", 13),
        ]
        assert checker.check(lines) is False

    def test_three_rows_phys_low_reject(self):
        """C5：低於罕見門檻（6 + tolerance 2 = 8 < 9）拒絕。"""
        checker = ConditionChecker(self._make_config())
        lines = [
            PotentialLine("物理攻擊力%", 13),
            PotentialLine("物理攻擊力%", 10),
            PotentialLine("物理攻擊力%", 6),
        ]
        assert checker.check(lines) is False

    def test_three_rows_phys_min_edge_pass(self):
        """C6：真實容錯邊界 — S 最低 10 (10+2=12)、R 最低 7 (7+2=9)。"""
        checker = ConditionChecker(self._make_config())
        lines = [
            PotentialLine("物理攻擊力%", 10),
            PotentialLine("物理攻擊力%", 7),
            PotentialLine("物理攻擊力%", 7),
        ]
        assert checker.check(lines) is True

    def test_three_rows_phys_below_min_edge_reject(self):
        """C6b：剛好低於 S 邊界（9+2=11 < 12）→ 拒絕。"""
        checker = ConditionChecker(self._make_config())
        lines = [
            PotentialLine("物理攻擊力%", 9),
            PotentialLine("物理攻擊力%", 7),
            PotentialLine("物理攻擊力%", 7),
        ]
        assert checker.check(lines) is False

    def test_three_rows_magic_min_edge_pass(self):
        """C6c：魔攻對稱邊界 — 證明容錯對稱套用到魔攻路徑。"""
        checker = ConditionChecker(self._make_config())
        lines = [
            PotentialLine("魔法攻擊力%", 10),
            PotentialLine("魔法攻擊力%", 7),
            PotentialLine("魔法攻擊力%", 7),
        ]
        assert checker.check(lines) is True

    def test_three_rows_magic_below_min_edge_reject(self):
        """C6d：魔攻剛好低於 S 邊界 → 拒絕。"""
        checker = ConditionChecker(self._make_config())
        lines = [
            PotentialLine("魔法攻擊力%", 9),
            PotentialLine("魔法攻擊力%", 7),
            PotentialLine("魔法攻擊力%", 7),
        ]
        assert checker.check(lines) is False

    def test_three_rows_illegal_attr_reject(self):
        """C7：OCR 防呆 — 非法屬性（STR）出現時拒絕，不 crash。"""
        checker = ConditionChecker(self._make_config())
        lines = [
            PotentialLine("物理攻擊力%", 13),
            PotentialLine("STR%", 9),
            PotentialLine("物理攻擊力%", 9),
        ]
        assert checker.check(lines) is False

    # ── C8-C10：2 排方塊（絕對附加方塊）──

    def test_two_rows_pure_phys_pass(self):
        """C8：2 排方塊純物攻通過（兩排皆 S 門檻 12）。"""
        checker = ConditionChecker(self._make_config(cube_type="絕對附加方塊 (僅洗兩排)"))
        lines = [
            PotentialLine("物理攻擊力%", 13),
            PotentialLine("物理攻擊力%", 12),
        ]
        assert checker.check(lines) is True

    def test_two_rows_pure_magic_pass(self):
        """C9：2 排方塊純魔攻通過。"""
        checker = ConditionChecker(self._make_config(cube_type="絕對附加方塊 (僅洗兩排)"))
        lines = [
            PotentialLine("魔法攻擊力%", 12),
            PotentialLine("魔法攻擊力%", 12),
        ]
        assert checker.check(lines) is True

    def test_two_rows_mixed_reject(self):
        """C10：2 排方塊混合拒絕。"""
        checker = ConditionChecker(self._make_config(cube_type="絕對附加方塊 (僅洗兩排)"))
        lines = [
            PotentialLine("物理攻擊力%", 13),
            PotentialLine("魔法攻擊力%", 12),
        ]
        assert checker.check(lines) is False

    def test_two_rows_phys_low_reject(self):
        """C10b：2 排方塊低於 S 門檻 12%（含容錯）拒絕。"""
        checker = ConditionChecker(self._make_config(cube_type="絕對附加方塊 (僅洗兩排)"))
        lines = [
            PotentialLine("物理攻擊力%", 13),
            PotentialLine("物理攻擊力%", 9),  # 9+2=11 < 12
        ]
        assert checker.check(lines) is False

    # ── C11-C12：摘要快照 ──

    def test_summary_three_rows_exact(self):
        """C11：三排方塊摘要 — 精確列表快照（回歸偵測）。"""
        config = self._make_config()
        assert generate_condition_summary(config) == [
            "三排需同屬性（全物攻 或 全魔攻）且符合:",
            "  · 物理攻擊力 12% or 9%",
            "  · 魔法攻擊力 12% or 9%",
            "(副手可於遊戲內整件互轉物攻／魔攻，混合洗出不算合格)",
        ]

    def test_summary_two_rows(self):
        """C12：2 排方塊摘要（S 門檻 12）— 逐項檢查。"""
        config = self._make_config(cube_type="絕對附加方塊 (僅洗兩排)")
        summary = generate_condition_summary(config)
        joined = "\n".join(summary)
        assert "兩排需同屬性" in joined
        assert "全物攻 或 全魔攻" in joined
        assert "物理攻擊力 12%" in joined
        assert "魔法攻擊力 12%" in joined
        assert "混合洗出不算合格" in joined
        # 負向斷言：不該出現 3 排語境或舊文案
        assert "三排" not in joined

    # ── C13：D2 強制防線 ──

    def test_main_weapon_rejects_convertible_attr(self):
        """C13：D2 強制 — 主武器 + 可轉換字串應 invalid，summary 回傳錯誤訊息。

        防止手改 config.json 繞過 UI 限制（主武器同樣有物／魔攻門檻）。
        """
        config = AppConfig(
            equipment_type="主武器 / 徽章 (米特拉)",
            target_attribute=self._ATTR,
        )
        checker = ConditionChecker(config)
        # 即便給三排滿分物攻也應被拒絕（_valid = False）
        lines = [
            PotentialLine("物理攻擊力%", 13),
            PotentialLine("物理攻擊力%", 13),
            PotentialLine("物理攻擊力%", 13),
        ]
        assert checker.check(lines) is False

        summary = generate_condition_summary(config)
        assert any("僅適用於輔助武器" in line for line in summary)

    def test_armor_rejects_convertible_attr(self):
        """C13b：D2 強制 — 防具（永恆 / 光輝）+ 可轉換字串同樣應 invalid。

        防止 guard 被誤寫成只阻擋武器類，忽略其他裝備類型。
        """
        config = AppConfig(
            equipment_type="永恆 / 光輝",
            target_attribute=self._ATTR,
        )
        checker = ConditionChecker(config)
        lines = [
            PotentialLine("STR%", 9),
            PotentialLine("STR%", 7),
            PotentialLine("STR%", 7),
        ]
        assert checker.check(lines) is False

        summary = generate_condition_summary(config)
        assert any("僅適用於輔助武器" in line for line in summary)


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

    # ── FR-2 lockdown: crit×N + main_attr×(3-N) ──

    def test_glove_triple_crit_pass(self):
        """FR-2 N=3: 3 排皆為爆擊傷害 3% → pass"""
        config = AppConfig(
            equipment_type="手套", is_eternal=True,
            target_attribute="STR",
        )
        checker = ConditionChecker(config)
        lines = [
            PotentialLine("爆擊傷害%", 3),
            PotentialLine("爆擊傷害%", 3),
            PotentialLine("爆擊傷害%", 3),
        ]
        assert checker.check(lines) is True

    def test_glove_double_crit_plus_stat_pass(self):
        """FR-2 N=2: 2 排爆擊 + 1 排主屬（非全屬）→ pass"""
        config = AppConfig(
            equipment_type="手套", is_eternal=True,
            target_attribute="STR",
        )
        checker = ConditionChecker(config)
        lines = [
            PotentialLine("爆擊傷害%", 3),
            PotentialLine("爆擊傷害%", 3),
            PotentialLine("STR%", 7),
        ]
        assert checker.check(lines) is True

    def test_glove_crit_plus_double_all_stats_pass(self):
        """FR-2 + FR-4: 1 排爆擊 + 2 排全屬性 → pass（全屬作為主屬）"""
        config = AppConfig(
            equipment_type="手套", is_eternal=True,
            target_attribute="STR",
        )
        checker = ConditionChecker(config)
        lines = [
            PotentialLine("爆擊傷害%", 3),
            PotentialLine("全屬性%", 7),
            PotentialLine("全屬性%", 6),
        ]
        assert checker.check(lines) is True


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

    def test_custom_crit_damage_no_tolerance(self):
        """爆擊傷害不套用容錯：1% 不應通過 3% 門檻"""
        config = AppConfig(
            use_preset=False,
            custom_lines=[
                LineCondition("爆擊傷害", 3, position=1),
                LineCondition("爆擊傷害", 3, position=2),
            ],
        )
        checker = ConditionChecker(config)
        # 1% + 3%：第一排 1% 不應通過
        lines = [
            PotentialLine("爆擊傷害%", 1),
            PotentialLine("爆擊傷害%", 3),
            PotentialLine("STR%", 9),
        ]
        assert checker.check(lines) is False

    def test_custom_crit_damage_both_3_pass(self):
        """爆擊傷害兩排都 3% 應通過"""
        config = AppConfig(
            use_preset=False,
            custom_lines=[
                LineCondition("爆擊傷害", 3, position=1),
                LineCondition("爆擊傷害", 3, position=2),
            ],
        )
        checker = ConditionChecker(config)
        lines = [
            PotentialLine("爆擊傷害%", 3),
            PotentialLine("爆擊傷害%", 3),
            PotentialLine("STR%", 9),
        ]
        assert checker.check(lines) is True

    def test_custom_crit_damage_any_pos_no_tolerance(self):
        """爆擊傷害任意一排模式：1% 不應通過 3% 門檻"""
        config = AppConfig(
            use_preset=False,
            custom_lines=[
                LineCondition("爆擊傷害", 3, position=0),
            ],
        )
        checker = ConditionChecker(config)
        lines = [
            PotentialLine("爆擊傷害%", 1),
            PotentialLine("STR%", 9),
            PotentialLine("LUK%", 7),
        ]
        assert checker.check(lines) is False


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

    # ── FR-3 lockdown: cooldown×N + main_attr×(3-N) ──

    def test_hat_triple_cooldown_pass(self):
        """FR-3 N=3: 3 排皆為冷卻 -1 秒 → pass"""
        config = AppConfig(
            equipment_type="帽子", is_eternal=True,
            target_attribute="STR",
        )
        checker = ConditionChecker(config)
        lines = [
            PotentialLine("技能冷卻時間", 1),
            PotentialLine("技能冷卻時間", 1),
            PotentialLine("技能冷卻時間", 1),
        ]
        assert checker.check(lines) is True

    def test_hat_cooldown_plus_double_all_stats_pass(self):
        """FR-3 + FR-4: 1 排冷卻 + 2 排全屬性 → pass（全屬作為主屬）"""
        config = AppConfig(
            equipment_type="帽子", is_eternal=True,
            target_attribute="STR",
        )
        checker = ConditionChecker(config)
        lines = [
            PotentialLine("技能冷卻時間", 1),
            PotentialLine("全屬性%", 7),
            PotentialLine("全屬性%", 6),
        ]
        assert checker.check(lines) is True

    def test_hat_double_cooldown_plus_all_stats_pass(self):
        """FR-3 + FR-4: 2 排冷卻 + 1 排全屬性 → pass"""
        config = AppConfig(
            equipment_type="帽子", is_eternal=True,
            target_attribute="STR",
        )
        checker = ConditionChecker(config)
        lines = [
            PotentialLine("技能冷卻時間", 1),
            PotentialLine("技能冷卻時間", 1),
            PotentialLine("全屬性%", 6),
        ]
        assert checker.check(lines) is True


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
        assert get_num_lines("絕對附加方塊 (僅洗兩排)") == 2
        # 無後綴版本已移除 (FR-19)，不再識別為 2 排
        assert get_num_lines("絕對附加方塊") == 3

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
            cube_type="絕對附加方塊 (僅洗兩排)",
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
            cube_type="絕對附加方塊 (僅洗兩排)",
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

    def test_preset_two_lines_cross_type_str_all_stats_fail(self):
        """FR-13: S潛 STR 9% + S潛 全屬性 7% 跨類型 → 白名單不接受。"""
        config = AppConfig(
            cube_type="絕對附加方塊 (僅洗兩排)",
            equipment_type="永恆 / 光輝",
            target_attribute="STR",
            use_preset=True,
        )
        checker = ConditionChecker(config)
        lines = [
            PotentialLine("STR%", 9),
            PotentialLine("全屬性%", 7),
        ]
        # FR-13: 跨類型雙 S（STR + 全屬）→ 白名單不接受
        assert checker.check(lines) is False

    def test_preset_two_lines_all_stats_below_s_fail(self):
        """全屬性 4%（加容錯 2 = 6，仍低於 S潛 7%）不通過。"""
        config = AppConfig(
            cube_type="絕對附加方塊 (僅洗兩排)",
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
            cube_type="絕對附加方塊 (僅洗兩排)",
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
            cube_type="絕對附加方塊 (僅洗兩排)",
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
            cube_type="絕對附加方塊 (僅洗兩排)",
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
            cube_type="絕對附加方塊 (僅洗兩排)",
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
            cube_type="絕對附加方塊 (僅洗兩排)",
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
            cube_type="絕對附加方塊 (僅洗兩排)",
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
        """摘要：絕對附加方塊顯示白名單格式。"""
        config = AppConfig(
            cube_type="絕對附加方塊 (僅洗兩排)",
            equipment_type="主武器 / 徽章 (米特拉)",
            target_attribute="物理攻擊力",
            use_preset=True,
        )
        summary = generate_condition_summary(config)
        assert summary == [
            "僅支援以下同種 × 2 組合:",
            "  · 物理攻擊力 13% × 2",
        ]

    def test_summary_preset_with_all_stats(self):
        """摘要：絕對附加方塊白名單含全屬性、MaxHP。"""
        config = AppConfig(
            cube_type="絕對附加方塊 (僅洗兩排)",
            equipment_type="永恆 / 光輝",
            target_attribute="STR",
            use_preset=True,
        )
        summary = generate_condition_summary(config)
        assert summary == [
            "僅支援以下同種 × 2 組合:",
            "  · STR 9% × 2 (同種主屬)",
            "  · 全屬性 7% × 2",
            "  · MaxHP 12% × 2",
        ]

    def test_summary_all_attrs(self):
        """摘要：絕對附加 + 所有屬性 → 白名單格式（列出所有主屬 × 2）。"""
        config = AppConfig(
            cube_type="絕對附加方塊 (僅洗兩排)",
            equipment_type="永恆 / 光輝",
            target_attribute="所有屬性",
            use_preset=True,
        )
        summary = generate_condition_summary(config)
        assert summary[0] == "僅支援以下同種 × 2 組合:"
        text = "\n".join(summary)
        assert "STR 9% × 2" in text
        assert "全屬性 7% × 2" in text
        assert "MaxHP 12% × 2" in text

    def test_tolerance_applies(self):
        """OCR 容錯 tolerance=2 套用在絕對附加方塊。"""
        config = AppConfig(
            cube_type="絕對附加方塊 (僅洗兩排)",
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

    # ── FR-12.1 Whitelist pass cases ──

    def test_whitelist_same_stat_eternal_str(self):
        """FR-12.1(a) 永恆: STR 9% × 2 → pass"""
        config = AppConfig(
            cube_type="絕對附加方塊 (僅洗兩排)",
            equipment_type="永恆 / 光輝",
            target_attribute="STR",
            use_preset=True,
        )
        checker = ConditionChecker(config)
        lines = [PotentialLine("STR%", 9), PotentialLine("STR%", 9)]
        assert checker.check(lines) is True

    def test_whitelist_same_stat_normal_str(self):
        """FR-12.1(a) 一般裝備: STR 8% × 2 → pass"""
        config = AppConfig(
            cube_type="絕對附加方塊 (僅洗兩排)",
            equipment_type="一般裝備 (神秘、漆黑、頂培)",
            target_attribute="STR",
            use_preset=True,
        )
        checker = ConditionChecker(config)
        lines = [PotentialLine("STR%", 8), PotentialLine("STR%", 8)]
        assert checker.check(lines) is True

    def test_whitelist_all_stats_eternal(self):
        """FR-12.1(b) 永恆: 全屬性 7% × 2 → pass"""
        config = AppConfig(
            cube_type="絕對附加方塊 (僅洗兩排)",
            equipment_type="永恆 / 光輝",
            target_attribute="STR",
            use_preset=True,
        )
        checker = ConditionChecker(config)
        lines = [PotentialLine("全屬性%", 7), PotentialLine("全屬性%", 7)]
        assert checker.check(lines) is True

    def test_whitelist_all_stats_normal(self):
        """FR-12.1(b) 一般裝備: 全屬性 6% × 2 → pass"""
        config = AppConfig(
            cube_type="絕對附加方塊 (僅洗兩排)",
            equipment_type="一般裝備 (神秘、漆黑、頂培)",
            target_attribute="STR",
            use_preset=True,
        )
        checker = ConditionChecker(config)
        lines = [PotentialLine("全屬性%", 6), PotentialLine("全屬性%", 6)]
        assert checker.check(lines) is True

    def test_whitelist_hp_eternal(self):
        """FR-12.1(c) 永恆: MaxHP 12% × 2 → pass"""
        config = AppConfig(
            cube_type="絕對附加方塊 (僅洗兩排)",
            equipment_type="永恆 / 光輝",
            target_attribute="MaxHP",
            use_preset=True,
        )
        checker = ConditionChecker(config)
        lines = [PotentialLine("MaxHP%", 12), PotentialLine("MaxHP%", 12)]
        assert checker.check(lines) is True

    def test_whitelist_hp_normal(self):
        """FR-12.1(c) 一般裝備: MaxHP 11% × 2 → pass"""
        config = AppConfig(
            cube_type="絕對附加方塊 (僅洗兩排)",
            equipment_type="一般裝備 (神秘、漆黑、頂培)",
            target_attribute="MaxHP",
            use_preset=True,
        )
        checker = ConditionChecker(config)
        lines = [PotentialLine("MaxHP%", 11), PotentialLine("MaxHP%", 11)]
        assert checker.check(lines) is True

    def test_whitelist_cooldown_hat(self):
        """FR-12.1(d) 帽子: 冷卻 -1 × 2 → pass"""
        config = AppConfig(
            cube_type="絕對附加方塊 (僅洗兩排)",
            equipment_type="帽子", is_eternal=True,
            target_attribute="STR",
            use_preset=True,
        )
        checker = ConditionChecker(config)
        lines = [PotentialLine("技能冷卻時間", 1), PotentialLine("技能冷卻時間", 1)]
        assert checker.check(lines) is True

    def test_whitelist_crit_glove(self):
        """FR-12.1(e) 手套: 爆擊傷害 3% × 2 → pass"""
        config = AppConfig(
            cube_type="絕對附加方塊 (僅洗兩排)",
            equipment_type="手套", is_eternal=True,
            target_attribute="STR",
            use_preset=True,
        )
        checker = ConditionChecker(config)
        lines = [PotentialLine("爆擊傷害%", 3), PotentialLine("爆擊傷害%", 3)]
        assert checker.check(lines) is True

    # ── FR-13 Whitelist FP (fail) cases ──

    def test_whitelist_cross_type_str_all_stats_fail(self):
        """FR-13: STR + 全屬 → 跨類型雙 S → fail"""
        config = AppConfig(
            cube_type="絕對附加方塊 (僅洗兩排)",
            equipment_type="永恆 / 光輝",
            target_attribute="STR",
            use_preset=True,
        )
        checker = ConditionChecker(config)
        lines = [PotentialLine("STR%", 9), PotentialLine("全屬性%", 7)]
        assert checker.check(lines) is False

    def test_whitelist_cross_attr_str_dex_fail(self):
        """FR-13 + Q3: STR + DEX → 跨屬性同數值 → fail"""
        config = AppConfig(
            cube_type="絕對附加方塊 (僅洗兩排)",
            equipment_type="永恆 / 光輝",
            target_attribute="STR",
            use_preset=True,
        )
        checker = ConditionChecker(config)
        lines = [PotentialLine("STR%", 9), PotentialLine("DEX%", 9)]
        assert checker.check(lines) is False

    def test_whitelist_cross_type_str_hp_fail(self):
        """FR-13: STR + MaxHP → 跨類型 → fail"""
        config = AppConfig(
            cube_type="絕對附加方塊 (僅洗兩排)",
            equipment_type="永恆 / 光輝",
            target_attribute="STR",
            use_preset=True,
        )
        checker = ConditionChecker(config)
        lines = [PotentialLine("STR%", 9), PotentialLine("MaxHP%", 12)]
        assert checker.check(lines) is False

    def test_whitelist_cooldown_non_hat_fail(self):
        """FR-14.1: 非帽子裝備 → 冷卻 combo 不進白名單"""
        config = AppConfig(
            cube_type="絕對附加方塊 (僅洗兩排)",
            equipment_type="永恆 / 光輝",
            target_attribute="STR",
            use_preset=True,
        )
        checker = ConditionChecker(config)
        lines = [PotentialLine("技能冷卻時間", 1), PotentialLine("技能冷卻時間", 1)]
        assert checker.check(lines) is False

    def test_whitelist_crit_non_glove_fail(self):
        """FR-14.1: 非手套裝備 → 爆擊 combo 不進白名單"""
        config = AppConfig(
            cube_type="絕對附加方塊 (僅洗兩排)",
            equipment_type="永恆 / 光輝",
            target_attribute="STR",
            use_preset=True,
        )
        checker = ConditionChecker(config)
        lines = [PotentialLine("爆擊傷害%", 3), PotentialLine("爆擊傷害%", 3)]
        assert checker.check(lines) is False

    def test_whitelist_crit1_no_tolerance_fail(self):
        """爆擊 1% + 1%（tolerance=0 不套用）→ fail"""
        config = AppConfig(
            cube_type="絕對附加方塊 (僅洗兩排)",
            equipment_type="手套", is_eternal=True,
            target_attribute="STR",
            use_preset=True,
        )
        checker = ConditionChecker(config)
        lines = [PotentialLine("爆擊傷害%", 1), PotentialLine("爆擊傷害%", 1)]
        assert checker.check(lines) is False

    # ── Absolute + 所有屬性 interaction ──

    def test_whitelist_all_attrs_same_stat_pass(self):
        """所有屬性 + 絕對附加: DEX 9% × 2 → pass（迴圈到 DEX 時命中白名單）"""
        config = AppConfig(
            cube_type="絕對附加方塊 (僅洗兩排)",
            equipment_type="永恆 / 光輝",
            target_attribute="所有屬性",
            use_preset=True,
        )
        checker = ConditionChecker(config)
        lines = [PotentialLine("DEX%", 9), PotentialLine("DEX%", 9)]
        assert checker.check(lines) is True

    def test_whitelist_all_attrs_cross_stat_str_dex_fail(self):
        """所有屬性 + 絕對附加: STR + DEX → 跨屬性 → fail"""
        config = AppConfig(
            cube_type="絕對附加方塊 (僅洗兩排)",
            equipment_type="永恆 / 光輝",
            target_attribute="所有屬性",
            use_preset=True,
        )
        checker = ConditionChecker(config)
        lines = [PotentialLine("STR%", 9), PotentialLine("DEX%", 9)]
        assert checker.check(lines) is False

    def test_whitelist_all_attrs_cross_type_fail(self):
        """所有屬性 + 絕對附加: STR + 全屬 → 跨類型 → fail"""
        config = AppConfig(
            cube_type="絕對附加方塊 (僅洗兩排)",
            equipment_type="永恆 / 光輝",
            target_attribute="所有屬性",
            use_preset=True,
        )
        checker = ConditionChecker(config)
        lines = [PotentialLine("STR%", 9), PotentialLine("全屬性%", 7)]
        assert checker.check(lines) is False

    # ── Convertible + absolute precedence ──

    def test_convertible_absolute_uses_convertible_path(self):
        """副手可轉換 + 絕對附加 → 走 convertible path, 不走白名單"""
        config = AppConfig(
            cube_type="絕對附加方塊 (僅洗兩排)",
            equipment_type="輔助武器 (副手)",
            target_attribute="物理/魔法攻擊力 (可轉換)",
            use_preset=True,
        )
        checker = ConditionChecker(config)
        # 兩排物攻 = pass（convertible path accepts this）
        lines = [PotentialLine("物理攻擊力%", 12), PotentialLine("物理攻擊力%", 12)]
        assert checker.check(lines) is True
