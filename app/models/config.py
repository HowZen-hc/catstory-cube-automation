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
class TargetCondition:
    """單行目標潛能條件。"""

    line_index: int  # 第幾行（0, 1, 2）
    attribute: str  # 屬性名稱，"任意" 表示不限
    operator: str = ">="  # >=, =, contains
    value: int = 0


@dataclass
class AppConfig:
    """應用程式設定。"""

    cube_type: str = "珍貴"  # 珍貴, 絕對, 萌獸, 恢復
    potential_region: Region = field(default_factory=Region)
    button_region: Region = field(default_factory=Region)
    delay_ms: int = 500
    hotkey: str = "F9"
    conditions: list[TargetCondition] = field(default_factory=list)

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
            return cls(
                cube_type=data.get("cube_type", "珍貴"),
                potential_region=Region(**data.get("potential_region", {})),
                button_region=Region(**data.get("button_region", {})),
                delay_ms=data.get("delay_ms", 500),
                hotkey=data.get("hotkey", "F9"),
                conditions=[
                    TargetCondition(**c)
                    for c in data.get("conditions", [])
                ],
            )
        except (json.JSONDecodeError, TypeError, KeyError):
            logger.exception("設定檔格式錯誤，使用預設值: %s", path)
            return cls()
