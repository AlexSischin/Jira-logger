import argparse
import asyncio
import logging
import logging.handlers
import pathlib
import sys
from datetime import datetime

import pytz
import yarl

from jlog import log_logs

logger = logging.getLogger(__name__)

if __name__ == '__main__':

    ARG_JIRA_URL = 'jira_url'
    ARG_FILE_PATH = 'file_path'
    ARG_ENCODING = 'encoding'
    ARG_USER = 'user'
    ARG_PASSWORD = 'password'
    ARG_START_DATE = 'start_date'


    def set_excepthook():
        def show_exception_and_exit(exc_type, exc_value, tb):
            import traceback
            traceback.print_exception(exc_type, exc_value, tb)
            input("Press key to exit.")
            sys.exit(-1)

        sys.excepthook = show_exception_and_exit


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
        args[ARG_START_DATE] = pytz.utc.localize(datetime.strptime(args[ARG_START_DATE], '%d.%m.%Y')
                                                 if args[ARG_START_DATE] else datetime.now())
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
        set_excepthook()
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
        except BaseException:
            logger.exception('Exception occurred during execution')
            raise
        finally:
            logger.info(
                '---^-^-^-^-^-^-^-^-^-^-^-^-^-^-^----End of execution----^-^-^-^-^-^-^-^-^-^-^-^-^-^-^---\n\n\n')


    main()
