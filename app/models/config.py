import json
import logging
from dataclasses import asdict, dataclass, field
from pathlib import Path

from app.paths import CONFIG_PATH

logger = logging.getLogger(__name__)


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
    position: int = 0  # 0=任意一排, 1=第1排, 2=第2排, 3=第3排


@dataclass
class AppConfig:
    """應用程式設定。"""

    cube_type: str = "珍貴附加方塊 (粉紅色)"
    equipment_type: str = "永恆 / 光輝"
    target_attribute: str = "STR"
    is_eternal: bool = True  # 手套/帽子是否為永恆裝備
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
                    item.pop("include_all_stats", None)  # 舊欄位移除
                    custom_lines.append(LineCondition(**item))
            else:
                custom_lines = [LineCondition()]
            # 舊設定遷移
            equip = data.get("equipment_type", "永恆 / 光輝")
            is_eternal = data.get("is_eternal", True)
            _OLD_EQUIP_MIGRATION = {
                "手套 (永恆)": ("手套", True),
                "手套 (非永恆)": ("手套", False),
                "帽子 (永恆)": ("帽子", True),
                "帽子 (非永恆)": ("帽子", False),
                "永恆裝備·光輝套裝": ("永恆 / 光輝", None),
                "主武器": ("主武器 / 徽章 (米特拉)", None),
                "徽章 (米特拉)": ("主武器 / 徽章 (米特拉)", None),
            }
            if equip in _OLD_EQUIP_MIGRATION:
                new_equip, new_eternal = _OLD_EQUIP_MIGRATION[equip]
                equip = new_equip
                if new_eternal is not None:
                    is_eternal = new_eternal

            return cls(
                cube_type=data.get("cube_type", "珍貴附加方塊 (粉紅色)"),
                equipment_type=equip,
                target_attribute=data.get("target_attribute", "STR"),
                is_eternal=is_eternal,
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
