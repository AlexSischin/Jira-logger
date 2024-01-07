#!/usr/bin/env python
import datetime
import logging
import time

from jira_client import IssueLog, JiraClient, EXEC_ARGS
from log import Log, read_log

LOG_BATCH_SIZE = 1000
logger = logging.getLogger(__name__)


def read_batch(iterable, n=LOG_BATCH_SIZE):
    while True:
        batch = []
        for i in iterable:
            if len(batch) < n:
                batch.append(i)
            else:
                break
        if batch:
            yield batch
        else:
            return


def create_jira_log(log: Log, start_date: datetime.datetime):
    return IssueLog(log.issue_id,
                    log.end_time - log.start_time,
                    comment=log.comment,
                    start_date=start_date)


async def log_logs(jira_url, resource_file, resource_encoding, username, password, start_date):
    def convert_log(log):
        return create_jira_log(log, start_date)

    start_time = time.time()
    total_count = 0
    successes = 0
    logged_time = datetime.timedelta(0)
    async with JiraClient(jira_url) as jira:
        await jira.login(username, password)
        with resource_file.open('r', encoding=resource_encoding) as log_file:
            for log_batch in read_batch(read_log(log_file)):
                jira_logs = [convert_log(log) for log in log_batch]
                succeeded_execs, failed_execs = await jira.log_works(jira_logs)
                total_count += len(jira_logs)
                successes += len(succeeded_execs)
                logged_deltas = [exe[EXEC_ARGS][0].time_logged for exe in succeeded_execs]
                logged_time += sum(logged_deltas, start=datetime.timedelta(0))
    end_time = time.time()
    total_time = '{:.2f}'.format(end_time - start_time)
    logger.info(f'Logged [{successes}/{total_count}] ({logged_time}) entries in {total_time}s')
