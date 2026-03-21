import json
import logging
from dataclasses import asdict, dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)

CONFIG_PATH = Path("config.json")


@dataclass
class Region:
    """螢幕區域座標。"""

    x: int = 0
    y: int = 0
    width: int = 0
    height: int = 0

    def as_tuple(self) -> tuple[int, int, int, int]:
        return (self.x, self.y, self.width, self.height)

    def is_set(self) -> bool:
        return self.width > 0 and self.height > 0


@dataclass
class LineCondition:
    """自訂模式的單行條件。"""

    attribute: str = "STR"
    min_value: int = 1
    include_all_stats: bool = False
    position: int = 0  # 0=任意一排, 1=第1排, 2=第2排, 3=第3排


@dataclass
class AppConfig:
    """應用程式設定。"""

    cube_type: str = "珍貴附加方塊 (粉紅色)"
    equipment_type: str = "永恆裝備·光輝套裝 (250等+)"
    target_attribute: str = "STR"
    include_all_stats: bool = False  # 含全屬性
    potential_region: Region = field(default_factory=Region)
    delay_ms: int = 1000
    ocr_engine: str = "paddle"
    use_gpu: bool = False
    use_preset: bool = True
    custom_lines: list[LineCondition] = field(
        default_factory=lambda: [LineCondition()]
    )

    def save(self, path: Path = CONFIG_PATH) -> None:
        """儲存設定到 JSON 檔案。"""
        try:
            path.write_text(
                json.dumps(asdict(self), ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except OSError:
            logger.exception("無法儲存設定檔: %s", path)

    @classmethod
    def load(cls, path: Path = CONFIG_PATH) -> "AppConfig":
        """從 JSON 檔案載入設定，檔案不存在則回傳預設值。"""
        if not path.exists():
            return cls()
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            raw_lines = data.get("custom_lines", [])
            if raw_lines:
                custom_lines = []
                for i, item in enumerate(raw_lines):
                    if "position" not in item:
                        item["position"] = i + 1
                    custom_lines.append(LineCondition(**item))
            else:
                custom_lines = [LineCondition()]
            return cls(
                cube_type=data.get("cube_type", "珍貴附加方塊 (粉紅色)"),
                equipment_type=data.get("equipment_type", "永恆裝備·光輝套裝 (250等+)"),
                target_attribute=data.get("target_attribute", "STR"),
                include_all_stats=data.get("include_all_stats", False),
                potential_region=Region(**data.get("potential_region", {})),
                delay_ms=data.get("delay_ms", 1000),
                ocr_engine=data.get("ocr_engine", "paddle"),
                use_gpu=data.get("use_gpu", False),
                use_preset=data.get("use_preset", True),
                custom_lines=custom_lines,
            )
        except (json.JSONDecodeError, TypeError, KeyError):
            logger.exception("設定檔格式錯誤，使用預設值: %s", path)
            return cls()
