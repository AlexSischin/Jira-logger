#!/usr/bin/env python
import asyncio
import datetime
import logging
import time

import yarl

import jira as ji
import log as lo

log_batch_size = 1000
logger = logging.getLogger(__name__)


def read_batch(iterable, n=log_batch_size):
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


def create_jira_log(log: lo.Log, start_date: datetime.datetime):
    return ji.IssueLog(log.issue_id,
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
    async with ji.JiraClient(jira_url) as jira:
        await jira.login(username, password)
        with resource_file.open('r', encoding=resource_encoding) as log_file:
            for log_batch in read_batch(lo.read_log(log_file)):
                jira_logs = [convert_log(log) for log in log_batch]
                succeeded_execs, failed_execs = await jira.log_works(jira_logs)
                total_count += len(jira_logs)
                successes += len(succeeded_execs)
                logged_deltas = [exe[ji.EXEC_ARGS][0].time_logged for exe in succeeded_execs]
                logged_time += sum(logged_deltas, start=datetime.timedelta(0))
    end_time = time.time()
    total_time = '{:.2f}'.format(end_time - start_time)
    logger.info(f'Logged [{successes}/{total_count}] ({logged_time}) entries in {total_time}s')


if __name__ == '__main__':
    import argparse
    import pathlib
    import logging.handlers
    import sys
    import pytz

    ARG_JIRA_URL = 'jira_url'
    ARG_FILE_PATH = 'file_path'
    ARG_ENCODING = 'encoding'
    ARG_USER = 'user'
    ARG_PASSWORD = 'password'
    ARG_START_DATE = 'start_date'


    def get_args():
        parser = argparse.ArgumentParser()
        parser.add_argument("-j", "--jira-url", required=True, default=None,
                            help="jira base URL")
        parser.add_argument("-f", "--filepath", required=True, default=None,
                            help="path to target CSV file with logs")
        parser.add_argument("-e", "--encoding", required=False, default='utf_8_sig',
                            help="encoding of the target CSV file")
        parser.add_argument("-u", "--user", required=True, default=None,
                            help="jira username")
        parser.add_argument("-p", "--password", required=False, default=None,
                            help="jira password. Default: prompted")
        parser.add_argument("-d", "--start-date", required=False, default=None,
                            help="start date in format 'dd.mm.yyyy'. Default: current date")
        args = parser.parse_args()
        return {
            ARG_JIRA_URL: args.jira_url,
            ARG_FILE_PATH: args.filepath,
            ARG_ENCODING: args.encoding,
            ARG_USER: args.user,
            ARG_PASSWORD: args.password,
            ARG_START_DATE: args.start_date
        }


    def complete_args(args: dict):
        args = dict(args)
        if not args[ARG_PASSWORD]:
            args[ARG_PASSWORD] = input(f'Password for {args[ARG_USER]}: ')
        return args


    def convert_args(args: dict):
        args = dict(args)
        args[ARG_JIRA_URL] = yarl.URL(args[ARG_JIRA_URL])
        args[ARG_FILE_PATH] = pathlib.Path(args[ARG_FILE_PATH])
        args[ARG_START_DATE] = pytz.utc.localize(datetime.datetime.strptime(args[ARG_START_DATE], '%d.%m.%Y')
                                                 if args[ARG_START_DATE] else datetime.datetime.now())
        return args


    def setup_logs():
        logs_dir = pathlib.Path('logs')
        app_log_fn = pathlib.Path('app_log.log')
        logging_encoding = 'utf_8_sig'
        app_log_count = 10
        log_max_bytes = 100 * 2 ** 20  # 100 MB
        log_format = ':. %(asctime)s %(module)s | %(levelname)s: %(msg)s'
        logs_dir.mkdir(exist_ok=True)
        handlers = [
            logging.handlers.RotatingFileHandler(logs_dir.joinpath(app_log_fn), encoding=logging_encoding,
                                                 maxBytes=log_max_bytes, backupCount=app_log_count),
            logging.StreamHandler(sys.stdout),
        ]
        logging.basicConfig(level=logging.INFO, format=log_format, handlers=handlers)


    def main():
        args = get_args()
        args = complete_args(args)
        args = convert_args(args)
        setup_logs()
        logger.info('---v-v-v-v-v-v-v-v-v-v-v-v-v-v-v---Start of execution---v-v-v-v-v-v-v-v-v-v-v-v-v-v-v---')
        try:
            log_coro = log_logs(
                args[ARG_JIRA_URL], args[ARG_FILE_PATH], args[ARG_ENCODING],
                args[ARG_USER], args[ARG_PASSWORD], args[ARG_START_DATE]
            )
            asyncio.run(log_coro)
        finally:
            logger.info(
                '---^-^-^-^-^-^-^-^-^-^-^-^-^-^-^----End of execution----^-^-^-^-^-^-^-^-^-^-^-^-^-^-^---\n\n\n')


    main()
