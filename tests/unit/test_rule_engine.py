import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.database import Base
from app.db.models import Incident, MonitorRule
from app.services.incident_mgr import incident_service, generate_fingerprint
from app.services.rule_engine import evaluate_condition, build_promql_query


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()


def test_rule_condition_evaluations():
    assert evaluate_condition(85.5, ">", 80.0) is True
    assert evaluate_condition(75.0, ">", 80.0) is False
    assert evaluate_condition(80.0, ">=", 80.0) is True
    assert evaluate_condition(10.0, "<", 20.0) is True
    assert evaluate_condition(25.0, "<=", 20.0) is False
    assert evaluate_condition(400.0, "==", 400.0) is True


def test_incident_creation_and_deduplication(db_session):
    labels = {"service": "checkout", "env": "prod"}

    # 1. First breach -> Create incident
    inc1 = incident_service.process_breach(
        db=db_session,
        detection_type="STATIC",
        source_id=1,
        metric_name="high_error_rate",
        labels=labels,
        severity="CRITICAL",
        summary="High error rate breach",
        observed_value=92.5
    )

    assert inc1.id is not None
    assert inc1.state == "OPEN"
    assert inc1.occurrence_count == 1
    assert inc1.latest_value == 92.5

    # 2. Repeated breach -> Deduplicate continuing incident
    inc2 = incident_service.process_breach(
        db=db_session,
        detection_type="STATIC",
        source_id=1,
        metric_name="high_error_rate",
        labels=labels,
        severity="CRITICAL",
        summary="High error rate breach",
        observed_value=96.0
    )

    assert inc2.id == inc1.id  # Same incident
    assert inc2.occurrence_count == 2
    assert inc2.latest_value == 96.0
    assert inc2.state == "OPEN"


def test_incident_acknowledgement_and_recovery(db_session):
    labels = {"service": "inventory"}

    # Trigger breach
    inc = incident_service.process_breach(
        db=db_session,
        detection_type="STATIC",
        source_id=2,
        metric_name="disk_usage",
        labels=labels,
        severity="WARNING",
        summary="Disk usage high",
        observed_value=88.0
    )
    assert inc.state == "OPEN"

    # Acknowledge
    acked = incident_service.acknowledge_incident(db_session, inc.id)
    assert acked.state == "ACKNOWLEDGED"
    assert acked.acknowledged_at is not None

    # Normal evaluation 1 (requires 2 recoveries to resolve)
    normal1 = incident_service.process_normal(
        db=db_session,
        detection_type="STATIC",
        source_id=2,
        metric_name="disk_usage",
        labels=labels,
        required_recoveries=2
    )
    assert normal1.state == "ACKNOWLEDGED"  # Not yet resolved
    assert normal1.consecutive_normal_count == 1

    # Normal evaluation 2 -> Auto-resolves
    normal2 = incident_service.process_normal(
        db=db_session,
        detection_type="STATIC",
        source_id=2,
        metric_name="disk_usage",
        labels=labels,
        required_recoveries=2
    )
    assert normal2.state == "RESOLVED"
    assert normal2.resolved_at is not None
