from pathlib import Path

from app.models.config import AppConfig, LineCondition, Region


class TestConfigSaveLoad:
    def test_save_and_load(self, tmp_path: Path):
        path = tmp_path / "config.json"
        config = AppConfig(
            cube_type="恢復附加方塊 (紅色)",
            equipment_type="永恆 / 光輝",
            target_attribute="STR",
            is_glove=True,
            potential_region=Region(100, 200, 300, 150),
            delay_ms=800,
        )
        config.save(path)
        loaded = AppConfig.load(path)

        assert loaded.cube_type == "恢復附加方塊 (紅色)"
        assert loaded.equipment_type == "永恆 / 光輝"
        assert loaded.target_attribute == "STR"
        assert loaded.is_glove is True
        assert loaded.is_hat is False
        assert loaded.potential_region.x == 100
        assert loaded.potential_region.width == 300
        assert loaded.delay_ms == 800

    def test_load_missing_file(self, tmp_path: Path):
        path = tmp_path / "nonexistent.json"
        config = AppConfig.load(path)
        assert config.cube_type == "珍貴附加方塊 (粉紅色)"
        assert config.equipment_type == "永恆 / 光輝"
        assert config.delay_ms == 1500

    def test_load_corrupted_file(self, tmp_path: Path):
        path = tmp_path / "bad.json"
        path.write_text("not valid json{{{")
        config = AppConfig.load(path)
        assert config.cube_type == "珍貴附加方塊 (粉紅色)"

    def test_load_partial_data(self, tmp_path: Path):
        path = tmp_path / "partial.json"
        path.write_text('{"cube_type": "絕對附加方塊 (僅洗兩排)", "delay_ms": 1000}')
        config = AppConfig.load(path)
        assert config.cube_type == "絕對附加方塊 (僅洗兩排)"
        assert config.delay_ms == 1000
        assert config.potential_region.is_set() is False

    def test_custom_lines_save_load(self, tmp_path: Path):
        path = tmp_path / "config.json"
        config = AppConfig(
            use_preset=False,
            custom_lines=[
                LineCondition("STR", 5),
                LineCondition("DEX", 3),
                LineCondition("全屬性", 2),
            ],
        )
        config.save(path)
        loaded = AppConfig.load(path)
        assert loaded.use_preset is False
        assert len(loaded.custom_lines) == 3
        assert loaded.custom_lines[0].attribute == "STR"
        assert loaded.custom_lines[0].min_value == 5
        assert loaded.custom_lines[1].attribute == "DEX"
        assert loaded.custom_lines[1].min_value == 3
        assert loaded.custom_lines[2].attribute == "全屬性"
        assert loaded.custom_lines[2].min_value == 2

    def test_load_without_custom_lines(self, tmp_path: Path):
        """config 沒有 custom_lines 欄位時，載入應使用預設值。"""
        path = tmp_path / "minimal.json"
        path.write_text('{"cube_type": "絕對附加方塊 (僅洗兩排)"}')
        config = AppConfig.load(path)
        assert config.cube_type == "絕對附加方塊 (僅洗兩排)"
        assert config.use_preset is True
        assert len(config.custom_lines) == 1
        assert config.custom_lines[0].attribute == "STR"

    def test_custom_lines_basic_save_load(self, tmp_path: Path):
        """自訂條件基本存取。"""
        path = tmp_path / "config.json"
        config = AppConfig(
            use_preset=False,
            custom_lines=[
                LineCondition("STR", 9),
                LineCondition("DEX", 7),
            ],
        )
        config.save(path)
        loaded = AppConfig.load(path)
        assert loaded.custom_lines[0].attribute == "STR"
        assert loaded.custom_lines[0].min_value == 9
        assert loaded.custom_lines[1].attribute == "DEX"
        assert loaded.custom_lines[1].min_value == 7

    def test_position_save_load(self, tmp_path: Path):
        """position 欄位存取。"""
        path = tmp_path / "config.json"
        config = AppConfig(
            use_preset=False,
            custom_lines=[
                LineCondition("STR", 9, position=0),
                LineCondition("DEX", 7, position=2),
                LineCondition("INT", 5, position=3),
            ],
        )
        config.save(path)
        loaded = AppConfig.load(path)
        assert loaded.custom_lines[0].position == 0
        assert loaded.custom_lines[1].position == 2
        assert loaded.custom_lines[2].position == 3

class TestAppConfigValidation:
    """v3 R1: __post_init__ 互斥驗證 + save 路徑 schema 驗證"""

    def test_is_glove_and_is_hat_mutex(self):
        """AC-4 / Signal 3.4: 兩個旗標同時 True → __post_init__ 自動歸零 + warning"""
        config = AppConfig(is_glove=True, is_hat=True)
        assert config.is_glove is False
        assert config.is_hat is False

    def test_is_glove_alone_preserved(self):
        config = AppConfig(is_glove=True, is_hat=False)
        assert config.is_glove is True
        assert config.is_hat is False

    def test_is_hat_alone_preserved(self):
        config = AppConfig(is_glove=False, is_hat=True)
        assert config.is_glove is False
        assert config.is_hat is True

    def test_save_path_omits_is_eternal(self, tmp_path: Path):
        """AC-2 / Signal 3.5: save() 寫出的 JSON 不含 'is_eternal' key"""
        import json
        path = tmp_path / "config.json"
        config = AppConfig(equipment_type="永恆 / 光輝", is_glove=True)
        config.save(path)
        data = json.loads(path.read_text(encoding="utf-8"))
        assert "is_eternal" not in data
        assert "is_glove" in data
        assert "is_hat" in data
