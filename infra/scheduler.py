from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from application.ports.outbound.logger_port import LoggerPort


@dataclass(frozen=True)
class IntervalJob:
    name: str
    interval_sec: float
    handler: Callable[[], Awaitable[None]]
    run_on_start: bool = True


class InfraScheduler:
    def __init__(self, logger: LoggerPort):
        self.logger = logger
        self._jobs: list[IntervalJob] = []
        self._tasks: list[asyncio.Task[None]] = []
        self._stop_event = asyncio.Event()

    def register_interval(
        self,
        *,
        name: str,
        interval_sec: float,
        handler: Callable[[], Awaitable[None]],
        run_on_start: bool = True,
    ) -> None:
        self._jobs.append(
            IntervalJob(
                name=name,
                interval_sec=interval_sec,
                handler=handler,
                run_on_start=run_on_start,
            )
        )

    def add_interval_job(self, *, name: str, interval_sec: float, handler: Callable[[], Awaitable[None]]) -> None:
        self.register_interval(name=name, interval_sec=interval_sec, handler=handler)

    async def start(self) -> None:
        if self._tasks:
            return
        self._stop_event.clear()
        self._tasks = [asyncio.create_task(self._run_job(job)) for job in self._jobs]

    async def stop(self) -> None:
        self._stop_event.set()
        if not self._tasks:
            return
        await asyncio.gather(*self._tasks, return_exceptions=True)
        self._tasks.clear()

    async def _run_job(self, job: IntervalJob) -> None:
        should_run_now = job.run_on_start
        while not self._stop_event.is_set():
            if should_run_now:
                try:
                    await job.handler()
                except Exception as exc:
                    self.logger.error(f"Scheduler job failed name={job.name} error={exc}")
            else:
                should_run_now = True

            try:
                await asyncio.wait_for(self._stop_event.wait(), timeout=job.interval_sec)
            except asyncio.TimeoutError:
                continue
