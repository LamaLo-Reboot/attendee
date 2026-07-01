import logging
import os
import signal

from celery import shared_task
from celery.signals import worker_shutting_down
from opentelemetry import trace
from opentelemetry.propagate import extract

from bots.bot_controller import BotController

logger = logging.getLogger(__name__)

tracer = trace.get_tracer(__name__)


@shared_task(bind=True, soft_time_limit=3600)
def run_bot(self, bot_id):
    from bots.meeting_url_utils import meeting_type_from_url
    from bots.models import Bot

    logger.info(f"Running bot {bot_id}")

    bot = Bot.objects.get(id=bot_id)
    platform = str(meeting_type_from_url(bot.meeting_url) or "unknown")

    # Extract trace context propagated from worker (if ephemeral container)
    ctx = extract({
        "traceparent": os.environ.get("OTEL_TRACE_PARENT", ""),
        "tracestate": os.environ.get("OTEL_TRACE_STATE", ""),
    })

    with tracer.start_as_current_span("bot.lifecycle", context=ctx, attributes={
        "bot.id": bot_id,
        "bot.object_id": str(bot.object_id),
        "bot.platform": platform,
        "bot.project_id": str(bot.project.object_id),
    }) as span:
        try:
            bot_controller = BotController(bot_id)
            bot_controller.run()
            span.set_status(trace.StatusCode.OK)
        except Exception as e:
            span.set_status(trace.StatusCode.ERROR, str(e))
            span.record_exception(e)
            raise


def kill_child_processes():
    # Get the process group ID (PGID) of the current process
    pgid = os.getpgid(os.getpid())

    try:
        # Send SIGTERM to all processes in the process group
        os.killpg(pgid, signal.SIGTERM)
    except ProcessLookupError:
        pass  # Process group may no longer exist


@worker_shutting_down.connect
def shutting_down_handler(sig, how, exitcode, **kwargs):
    # Just adding this code so we can see how to shut down all the tasks
    # when the main process is terminated.
    # It's likely overkill.
    logger.info("Celery worker shutting down, sending SIGTERM to all child processes")
    kill_child_processes()
