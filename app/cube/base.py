from abc import ABC, abstractmethod

from app.core.condition import ConditionChecker
from app.core.mouse import MouseController
from app.core.ocr import OCREngine
from app.core.ocr_logger import OCRLogSession
from app.core.screen import ScreenCapture
from app.models.config import AppConfig
from app.models.potential import RollResult


class CubeStrategy(ABC):
    """抽象方塊策略基類。"""

    def __init__(
        self,
        config: AppConfig,
        screen: ScreenCapture,
        ocr: OCREngine,
        mouse: MouseController,
        checker: ConditionChecker,
        log_session: OCRLogSession,
    ) -> None:
        self.config = config
        self.screen = screen
        self.ocr = ocr
        self.mouse = mouse
        self.checker = checker
        self.log_session = log_session

    @abstractmethod
    def execute_roll(self, roll_number: int) -> RollResult:
        """執行一次洗方塊流程，回傳結果。"""
        ...
