import asyncio
from app.messaging.rabbitmq_publisher import publish_event
from app.messaging import events as ev, payloads as pl


async def handle_job_started(event):
    await asyncio.to_thread(
        publish_event, ev.JOB_STARTED,
        pl.job_started(event.drive_id, event.jd_id, event.total_resumes)
    )

async def handle_job_failed(event):
    await asyncio.to_thread(
        publish_event, ev.JOB_FAILED,
        pl.job_failed(event.drive_id, event.jd_id, event.error)
    )

async def handle_job_completed(event):
    await asyncio.to_thread(
        publish_event, ev.JOB_COMPLETED,
        pl.job_completed(event.drive_id, event.jd_id, event.total_resumes)
    )

async def handle_jd_parsing_started(event):
    await asyncio.to_thread(
        publish_event, ev.JD_PARSING_STARTED,
        pl.jd_parsing_started(event.drive_id, event.jd_id)
    )

async def handle_jd_parsing_completed(event):
    await asyncio.to_thread(
        publish_event, ev.JD_PARSING_COMPLETED,
        pl.jd_parsing_completed(event.drive_id, event.jd_id, event.job_dict)
    )

async def handle_resumes_parsing_started(event):
    await asyncio.to_thread(
        publish_event, ev.RESUMES_PARSING_STARTED,
        pl.resumes_parsing_started(event.drive_id, event.jd_id, event.total)
    )

async def handle_resumes_parsing_completed(event):
    await asyncio.to_thread(
        publish_event, ev.RESUMES_PARSING_COMPLETED,
        pl.resumes_parsing_completed(
            event.drive_id, event.jd_id,
            event.total, event.succeeded, event.failed
        )
    )

async def handle_resume_parsing_started(event):
    await asyncio.to_thread(
        publish_event, ev.RESUME_PARSING_STARTED,
        pl.resume_parsing_started(
            event.drive_id, event.jd_id, event.resume_id, event.index
        )
    )

async def handle_resume_parsing_completed(event):
    await asyncio.to_thread(
        publish_event, ev.RESUME_PARSING_COMPLETED,
        pl.resume_parsing_completed(
            job_id=event.drive_id, jd_id=event.jd_id,
            resume_id=event.resume_id, index=event.index,
            status=event.status, parsed_resume=event.resume_dict,
            error=event.error,
        )
    )

async def handle_resumes_matching_started(event):
    await asyncio.to_thread(
        publish_event, ev.RESUMES_MATCHING_STARTED,
        pl.resumes_matching_started(event.drive_id, event.jd_id, event.total)
    )

async def handle_resumes_matching_completed(event):
    await asyncio.to_thread(
        publish_event, ev.RESUMES_MATCHING_COMPLETED,
        pl.resumes_matching_completed(
            event.drive_id, event.jd_id, event.total, event.succeeded, event.failed
        )
    )

# ✅ FIX in rabbit_publisher_handlers.py
async def handle_resume_matching_completed(event):
    await asyncio.to_thread(
        publish_event, ev.RESUME_MATCHING_COMPLETED,
        pl.resume_matching_completed(
            job_id=event.drive_id, jd_id=event.jd_id,
            resume_id=event.resume_id, index=event.index,
            status=event.status,
            candidate_result=event.candidate_result,
            error=event.error,
        )
    )
    
async def handle_resumes_ranking_started(event):
    await asyncio.to_thread(
        publish_event, ev.RESUMES_RANKING_STARTED,
        pl.resumes_ranking_started(event.drive_id, event.jd_id, event.total)
    )

async def handle_resumes_ranking_completed(event):
    await asyncio.to_thread(
        publish_event, ev.RESUMES_RANKING_COMPLETED,
        pl.resumes_ranking_completed(
            event.drive_id, event.jd_id, event.total, event.ranking
        )
    )
async def handle_resume_matching_started(event):
    await asyncio.to_thread(
        publish_event, ev.RESUME_MATCHING_STARTED,
        pl.resume_matching_started(
            event.drive_id, event.jd_id, event.resume_id, event.index
        )
    )