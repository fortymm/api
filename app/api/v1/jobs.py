from typing import Annotated, Any

from arq.connections import ArqRedis
from arq.jobs import Job, JobStatus
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.queue import get_queue

router = APIRouter(prefix="/jobs", tags=["jobs"])


class JobEnqueued(BaseModel):
    job_id: str


class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    result: Any | None = None
    error: str | None = None


@router.post("/hello-cpsat", response_model=JobEnqueued)
async def enqueue_hello_cpsat(
    queue: Annotated[ArqRedis, Depends(get_queue)],
) -> JobEnqueued:
    job = await queue.enqueue_job("hello_cpsat")
    if job is None:
        raise HTTPException(status_code=503, detail="Could not enqueue job")
    return JobEnqueued(job_id=job.job_id)


@router.get("/{job_id}", response_model=JobStatusResponse)
async def get_job(
    job_id: str,
    queue: Annotated[ArqRedis, Depends(get_queue)],
) -> JobStatusResponse:
    job = Job(job_id=job_id, redis=queue)
    status = await job.status()
    if status == JobStatus.not_found:
        raise HTTPException(status_code=404, detail="Job not found")
    if status != JobStatus.complete:
        return JobStatusResponse(job_id=job_id, status=status.value)

    info = await job.result_info()
    if info is None:
        return JobStatusResponse(job_id=job_id, status=status.value)
    if info.success:
        return JobStatusResponse(job_id=job_id, status=status.value, result=info.result)
    return JobStatusResponse(job_id=job_id, status=status.value, error=repr(info.result))
