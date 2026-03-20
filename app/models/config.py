from dataclasses import dataclass, field


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
