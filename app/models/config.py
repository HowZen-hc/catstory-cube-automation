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
    is_glove: bool = False  # 勾選後：至少 1 排必須為爆擊傷害 3%（絕對附加須 2 排）
    is_hat: bool = False    # 勾選後：至少 1 排必須為冷卻 -1 秒（絕對附加須 2 排）
    potential_region: Region = field(default_factory=Region)
    delay_ms: int = 1500
    ocr_engine: str = "paddle"
    use_gpu: bool = False
    use_preset: bool = True
    custom_lines: list[LineCondition] = field(
        default_factory=lambda: [LineCondition()]
    )

    def __post_init__(self) -> None:
        """驗證互斥條件：is_glove 與 is_hat 不得同時為 True。"""
        if self.is_glove and self.is_hat:
            logger.warning(
                "is_glove and is_hat cannot both be True; resetting to False"
            )
            self.is_glove = False
            self.is_hat = False

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

            # 舊設定遷移（保留非手套 / 帽子的歷史 key）
            equip = data.get("equipment_type", "永恆 / 光輝")
            # 防呆：equipment_type 必須是字串；異常值 fallback 預設
            if not isinstance(equip, str):
                equip = "永恆 / 光輝"
            _OLD_EQUIP_MIGRATION = {
                "永恆裝備·光輝套裝": "永恆 / 光輝",
                "主武器": "主武器 / 徽章 (米特拉)",
                "徽章 (米特拉)": "主武器 / 徽章 (米特拉)",
            }
            if equip in _OLD_EQUIP_MIGRATION:
                equip = _OLD_EQUIP_MIGRATION[equip]

            # v3 防呆（Signal 3.3, FR-11）：舊 "手套" / "帽子" / "手套 (永恆)" 等
            # 不再是合法 equipment_type；fallback 為預設值並 log（不 crash）
            if equip in {"手套", "帽子"} or equip.startswith(("手套 (", "帽子 (")):
                logger.warning(
                    "Legacy equipment_type '%s' is no longer valid; "
                    "fallback to '永恆 / 光輝'. User should reconfigure.",
                    equip,
                )
                equip = "永恆 / 光輝"

            # 方塊類型遷移：無後綴 → 有後綴
            cube_type = data.get("cube_type", "珍貴附加方塊 (粉紅色)")
            if cube_type == "絕對附加方塊":
                cube_type = "絕對附加方塊 (僅洗兩排)"

            return cls(
                cube_type=cube_type,
                equipment_type=equip,
                target_attribute=data.get("target_attribute", "STR"),
                is_glove=bool(data.get("is_glove", False)),
                is_hat=bool(data.get("is_hat", False)),
                potential_region=Region(**data.get("potential_region", {})),
                delay_ms=data.get("delay_ms", 1500),
                ocr_engine=data.get("ocr_engine", "paddle"),
                use_gpu=data.get("use_gpu", False),
                use_preset=data.get("use_preset", True),
                custom_lines=custom_lines,
            )
        except (json.JSONDecodeError, TypeError, KeyError):
            logger.exception("設定檔格式錯誤，使用預設值: %s", path)
            return cls()
