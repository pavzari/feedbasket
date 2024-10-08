import asyncio
import logging
from collections.abc import Callable
from functools import wraps

log = logging.getLogger(__name__)


class RetryLimitError(Exception):
    def __init__(self, func_name, args, kwargs):
        self.func_name = func_name
        self.args = args
        self.kwargs = kwargs

    def __str__(self):
        return f"{self.func_name} failed after retrying: {self.args} {self.kwargs}"


def retry(
    *exceptions: type[Exception],
    retries: int = 3,
    wait: int = 1,
    emit_log: bool = False,
) -> Callable:
    """Decorator that retries an async function through specified exceptions.

    exceptions: The exceptions that will trigger the retry.
    retries: Number of retries of function execution.
    wait: Seconds to wait before retry.
    emit_log: Log unsuccessful attempts."""

    def wrap(func):
        @wraps(func)
        async def inner(*args, **kwargs):
            retries_count = 0

            while True:
                try:
                    response = await func(*args, **kwargs)
                except exceptions as e:
                    retries_count += 1
                    msg = f"Exception during {func} execution. {retries_count} of {retries} retries attempted."

                    if retries_count >= retries:
                        if emit_log:
                            log.warning(msg)
                        raise RetryLimitError(func.__name__, args, kwargs) from e
                    else:
                        if emit_log:
                            log.warning(msg)
                    if wait:
                        await asyncio.sleep(wait)
                else:
                    return response

        return inner

    return wrap
