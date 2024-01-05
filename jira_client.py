import logging
from asyncio import gather
from dataclasses import dataclass
from datetime import datetime, timedelta
from functools import wraps
from json import dumps
from typing import Iterable, Optional, Union

from aiohttp import ClientSession
from yarl import URL

logger = logging.getLogger(__name__)


@dataclass
class IssueLog:
    issue_id: str
    time_logged: timedelta
    comment: Optional[str] = None
    start_date: datetime = datetime.now()


def time_format(dt):
    return "%s:%.3f%s" % (
        dt.strftime('%Y-%m-%dT%H:%M'),
        float("%.3f" % (dt.second + dt.microsecond / 1e6)),
        dt.strftime('%z')
    )


EXEC_CORO = 'coro'
EXEC_ARGS = 'args'
EXEC_KWARGS = 'kwargs'
EXEC_RESULT = 'result'
EXEC_ERROR = 'error'


def exec_info(coro):
    @wraps(coro)
    async def wrapper(*args, **kwargs):
        result = error = None
        try:
            result = await coro(*args, **kwargs)
        except Exception as e:
            error = e
        finally:
            return {
                EXEC_CORO: coro,
                EXEC_ARGS: args,
                EXEC_KWARGS: kwargs,
                EXEC_RESULT: result,
                EXEC_ERROR: error
            }

    return wrapper


class JiraClient:
    _login_path = '/rest/auth/1/session'
    _create_log_path = '/rest/api/2/issue/{issue_id}/worklog'
    _internal_ids_cache_size = 10000

    def __init__(self, base_url: Union[str, URL]) -> None:
        super().__init__()
        self._base_url = URL(base_url)

    async def __aenter__(self):
        self._session = ClientSession(base_url=self._base_url, raise_for_status=True)
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        await self._session.close()

    async def login(self, username, password):
        url = URL(self._login_path)
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        data = dumps({
            'username': username,
            'password': password
        })
        logger.debug('Logging in')
        result = await self._session.post(url, headers=headers, data=data)
        logger.info('Successfully logged in')
        return result

    async def log_work(self, issue_log: IssueLog):
        url = URL(self._create_log_path.format(issue_id=issue_log.issue_id))
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        data = dumps({
            "timeSpentSeconds": issue_log.time_logged.seconds,
            "comment": issue_log.comment,
            "started": time_format(issue_log.start_date)
        })
        logger.debug(f'Sending: data={data}, headers={headers}')
        result = await self._session.post(url, data=data, headers=headers)
        logger.info(f'Successfully logged: {issue_log}')
        return result

    async def log_works(self, logs: Iterable[IssueLog]):
        log_work = exec_info(self.log_work)
        execs_info = await gather(*[log_work(log) for log in logs])
        failed_execs = [info for info in execs_info if info[EXEC_ERROR]]
        succeeded_execs = [info for info in execs_info if not info[EXEC_ERROR]]
        for exe in failed_execs:
            logger.error(f'Failed to log: {exe[EXEC_ARGS][0]}', exc_info=exe[EXEC_ERROR])
        return succeeded_execs, failed_execs
