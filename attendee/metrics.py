from opentelemetry import metrics

meter = metrics.get_meter("attendee")

# Counters
bots_launched = meter.create_counter("attendee.bots.launched", unit="1")
bots_failed = meter.create_counter("attendee.bots.failed", unit="1")
webhooks_delivered = meter.create_counter("attendee.webhooks.delivered", unit="1")
transcription_completed = meter.create_counter("attendee.transcription.completed", unit="1")

# Histograms
bot_join_duration = meter.create_histogram("attendee.bots.join_duration", unit="s")
bot_recording_duration = meter.create_histogram("attendee.bots.recording_duration", unit="s")
webhook_delivery_duration = meter.create_histogram("attendee.webhooks.delivery_duration", unit="ms")


# Gauge — running bot containers (callback via Docker socket)
def _running_bots_callback(options):
    try:
        import docker

        client = docker.from_env()
        count = len(client.containers.list(
            filters={"label": "attendee.type=ephemeral-bot", "status": "running"}
        ))
    except Exception:
        count = 0
    yield metrics.Observation(count)


meter.create_observable_gauge(
    "attendee.bots.running",
    callbacks=[_running_bots_callback],
    unit="1",
)
