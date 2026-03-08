from app.events.event_bus import event_bus
from app.events.events_types import (
    JOB_STARTED, JOB_FAILED, JOB_COMPLETED,
    JD_PARSING_STARTED, JD_PARSING_COMPLETED,
    RESUMES_PARSING_STARTED, RESUMES_PARSING_COMPLETED,
    RESUME_PARSING_STARTED, RESUME_PARSING_COMPLETED,
    RESUMES_MATCHING_STARTED, RESUMES_MATCHING_COMPLETED,
    RESUME_MATCHING_STARTED, RESUME_MATCHING_COMPLETED,
    SUMMARY_UPDATED,RESUMES_RANKING_COMPLETED,RESUMES_RANKING_STARTED
)
from app.handlers.file_writer_handlers import (
    handle_summary_updated,
    handle_jd_parsing_completed,
    handle_resume_parsing_completed,
    handle_candidate_ranked
)
from app.handlers.rabbit_publisher_handlers import (
    handle_job_started,
    handle_job_failed,
    handle_job_completed,
    handle_jd_parsing_started,
    handle_jd_parsing_completed       as rabbit_jd_parsing_completed,
    handle_resumes_parsing_started,
    handle_resumes_parsing_completed,
    handle_resume_parsing_started,
    handle_resume_parsing_completed   as rabbit_resume_parsing_completed,
    handle_resumes_matching_started,
    handle_resumes_matching_completed,
    handle_resume_matching_started,
    handle_resume_matching_completed,
    handle_resumes_ranking_completed,
    handle_resumes_ranking_started
)


def register_all_handlers() -> None:
    _register_file_writer()        # ← comment out = zero file writing
    _register_rabbit_publisher()   # ← comment out = zero RabbitMQ


def _register_file_writer() -> None:
    event_bus.subscribe(SUMMARY_UPDATED,           handle_summary_updated)
    event_bus.subscribe(JD_PARSING_COMPLETED,      handle_jd_parsing_completed)
    event_bus.subscribe(RESUME_PARSING_COMPLETED,  handle_resume_parsing_completed)
    event_bus.subscribe(RESUME_MATCHING_COMPLETED, handle_candidate_ranked)


def _register_rabbit_publisher() -> None:
    event_bus.subscribe(JOB_STARTED,                handle_job_started)
    event_bus.subscribe(JOB_FAILED,                 handle_job_failed)
    event_bus.subscribe(JOB_COMPLETED,              handle_job_completed)
    event_bus.subscribe(JD_PARSING_STARTED,         handle_jd_parsing_started)
    event_bus.subscribe(JD_PARSING_COMPLETED,       rabbit_jd_parsing_completed)
    event_bus.subscribe(RESUMES_PARSING_STARTED,    handle_resumes_parsing_started)
    event_bus.subscribe(RESUMES_PARSING_COMPLETED,  handle_resumes_parsing_completed)
    event_bus.subscribe(RESUME_PARSING_STARTED,     handle_resume_parsing_started)
    event_bus.subscribe(RESUME_PARSING_COMPLETED,   rabbit_resume_parsing_completed)
    event_bus.subscribe(RESUMES_MATCHING_STARTED,   handle_resumes_matching_started)
    event_bus.subscribe(RESUMES_MATCHING_COMPLETED, handle_resumes_matching_completed)
    event_bus.subscribe(RESUME_MATCHING_STARTED,    handle_resume_matching_started)
    event_bus.subscribe(RESUME_MATCHING_COMPLETED,  handle_resume_matching_completed)
    event_bus.subscribe(RESUMES_RANKING_STARTED,    handle_resumes_ranking_started)
    event_bus.subscribe(RESUMES_RANKING_COMPLETED,  handle_resumes_ranking_completed)
    