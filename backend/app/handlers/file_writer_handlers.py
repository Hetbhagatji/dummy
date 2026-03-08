import asyncio
from app.utils.write_json import write_json


async def handle_summary_updated(event):
    await asyncio.to_thread(write_json, event.summary_path, event.summary)


async def handle_jd_parsing_completed(event):
    await asyncio.to_thread(write_json, event.job_path, event.job_dict)


async def handle_resume_parsing_completed(event):
    if event.status != "success" or not event.resume_path:
        return
    await asyncio.to_thread(write_json, event.resume_path, event.resume_dict)


async def handle_candidate_ranked(event):
    await asyncio.to_thread(write_json, event.scores_path, event.candidate_result)