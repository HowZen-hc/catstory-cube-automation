from pathlib import Path

from app.models.config import AppConfig, Region, TargetCondition


class TestConfigSaveLoad:
    def test_save_and_load(self, tmp_path: Path):
        path = tmp_path / "config.json"
        config = AppConfig(
            cube_type="恢復",
            potential_region=Region(100, 200, 300, 150),
            button_region=Region(400, 500, 80, 40),
            delay_ms=800,
            hotkey="F10",
            conditions=[
                TargetCondition(0, "攻擊力%", ">=", 12),
                TargetCondition(1, "BOSS傷害%", ">=", 30),
            ],
        )
        config.save(path)
        loaded = AppConfig.load(path)

        assert loaded.cube_type == "恢復"
        assert loaded.potential_region.x == 100
        assert loaded.potential_region.width == 300
        assert loaded.button_region.y == 500
        assert loaded.delay_ms == 800
        assert loaded.hotkey == "F10"
        assert len(loaded.conditions) == 2
        assert loaded.conditions[0].attribute == "攻擊力%"
        assert loaded.conditions[1].value == 30

    def test_load_missing_file(self, tmp_path: Path):
        path = tmp_path / "nonexistent.json"
        config = AppConfig.load(path)
        assert config.cube_type == "珍貴"
        assert config.delay_ms == 500

    def test_load_corrupted_file(self, tmp_path: Path):
        path = tmp_path / "bad.json"
        path.write_text("not valid json{{{")
        config = AppConfig.load(path)
        assert config.cube_type == "珍貴"

    def test_load_partial_data(self, tmp_path: Path):
        path = tmp_path / "partial.json"
        path.write_text('{"cube_type": "絕對", "delay_ms": 1000}')
        config = AppConfig.load(path)
        assert config.cube_type == "絕對"
        assert config.delay_ms == 1000
        assert config.hotkey == "F9"
        assert config.potential_region.is_set() is False
