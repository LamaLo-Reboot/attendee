from datetime import datetime, timezone

from opentelemetry import trace
from pythonjsonlogger import jsonlogger


class ISOJsonFormatter(jsonlogger.JsonFormatter):
    """
    JSON formatter that adds ISO 8601 timestamp and OTel trace correlation
    """

    def add_fields(self, log_record, record, message_dict):
        super().add_fields(log_record, record, message_dict)

        # Add ISO timestamp from the record's created time
        # record.created is a Unix timestamp (float)
        dt = datetime.fromtimestamp(record.created, tz=timezone.utc)
        log_record["timestamp"] = dt.isoformat()

        # OTel trace correlation
        span = trace.get_current_span()
        ctx = span.get_span_context()
        if ctx and ctx.trace_id:
            log_record["trace_id"] = format(ctx.trace_id, "032x")
            log_record["span_id"] = format(ctx.span_id, "016x")
