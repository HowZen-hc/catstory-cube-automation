from pathlib import Path

from app.models.config import AppConfig, Region


class TestConfigSaveLoad:
    def test_save_and_load(self, tmp_path: Path):
        path = tmp_path / "config.json"
        config = AppConfig(
            cube_type="恢復附加方塊(紅色)",
            equipment_type="手套 (250+)",
            target_attribute="STR",
            include_all_stats=True,
            potential_region=Region(100, 200, 300, 150),
            delay_ms=800,
            hotkey="F10",
        )
        config.save(path)
        loaded = AppConfig.load(path)

        assert loaded.cube_type == "恢復附加方塊(紅色)"
        assert loaded.equipment_type == "手套 (250+)"
        assert loaded.target_attribute == "STR"
        assert loaded.include_all_stats is True
        assert loaded.potential_region.x == 100
        assert loaded.potential_region.width == 300
        assert loaded.delay_ms == 800
        assert loaded.hotkey == "F10"

    def test_load_missing_file(self, tmp_path: Path):
        path = tmp_path / "nonexistent.json"
        config = AppConfig.load(path)
        assert config.cube_type == "珍貴附加方塊(粉紅色)"
        assert config.equipment_type == "永恆裝備·光輝套裝 (250+)"
        assert config.delay_ms == 500

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
        assert config.hotkey == "F9"
        assert config.potential_region.is_set() is False
        assert config.include_all_stats is False
