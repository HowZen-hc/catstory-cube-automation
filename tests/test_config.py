from pathlib import Path

from app.models.config import AppConfig, LineCondition, Region


class TestConfigSaveLoad:
    def test_save_and_load(self, tmp_path: Path):
        path = tmp_path / "config.json"
        config = AppConfig(
            cube_type="恢復附加方塊(紅色)",
            equipment_type="手套 (250等+)",
            target_attribute="STR",
            include_all_stats=True,
            potential_region=Region(100, 200, 300, 150),
            delay_ms=800,
        )
        config.save(path)
        loaded = AppConfig.load(path)

        assert loaded.cube_type == "恢復附加方塊(紅色)"
        assert loaded.equipment_type == "手套 (250等+)"
        assert loaded.target_attribute == "STR"
        assert loaded.include_all_stats is True
        assert loaded.potential_region.x == 100
        assert loaded.potential_region.width == 300
        assert loaded.delay_ms == 800

    def test_load_missing_file(self, tmp_path: Path):
        path = tmp_path / "nonexistent.json"
        config = AppConfig.load(path)
        assert config.cube_type == "珍貴附加方塊(粉紅色)"
        assert config.equipment_type == "永恆裝備·光輝套裝 (250等+)"
        assert config.delay_ms == 1000

    def test_load_corrupted_file(self, tmp_path: Path):
        path = tmp_path / "bad.json"
        path.write_text("not valid json{{{")
        config = AppConfig.load(path)
        assert config.cube_type == "珍貴附加方塊(粉紅色)"

    def test_load_partial_data(self, tmp_path: Path):
        path = tmp_path / "partial.json"
        path.write_text('{"cube_type": "絕對附加方塊", "delay_ms": 1000}')
        config = AppConfig.load(path)
        assert config.cube_type == "絕對附加方塊"
        assert config.delay_ms == 1000
        assert config.potential_region.is_set() is False
        assert config.include_all_stats is False

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
        """舊設定檔沒有 custom_lines 欄位，載入時應使用預設值。"""
        path = tmp_path / "old.json"
        path.write_text('{"cube_type": "絕對附加方塊"}')
        config = AppConfig.load(path)
        assert config.use_preset is True
        assert len(config.custom_lines) == 3
        assert config.custom_lines[0].attribute == "STR"
