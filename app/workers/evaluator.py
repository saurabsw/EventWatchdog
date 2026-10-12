import asyncio
import logging
from app.config import settings
from app.core.database import SessionLocal
from app.services.rule_engine import rule_engine_service
from app.services.anomaly_evaluator import anomaly_evaluator
from app.services.telemetry_exporter import telemetry_exporter_service

logger = logging.getLogger(__name__)


class EvaluationWorker:
    """Continuously running background worker for static rules and anomaly evaluation."""

    def __init__(self, interval_seconds: int = 15):
        self.interval_seconds = interval_seconds
        self.is_running = False
        self._task = None

    async def start(self):
        self.is_running = True
        logger.info("EvaluationWorker started (interval=%ds)", self.interval_seconds)
        while self.is_running:
            try:
                db = SessionLocal()
                try:
                    await rule_engine_service.evaluate_all_rules(db)
                    await anomaly_evaluator.evaluate_all_enrollments(db)
                    await telemetry_exporter_service.export_telemetry(db)
                finally:
                    db.close()
            except Exception as e:
                logger.error("Error in EvaluationWorker run: %s", e)
            await asyncio.sleep(self.interval_seconds)

    def stop(self):
        self.is_running = False
        if self._task:
            self._task.cancel()
        logger.info("EvaluationWorker stopped")


evaluator_worker = EvaluationWorker(interval_seconds=settings.EVALUATION_INTERVAL_SECONDS)
