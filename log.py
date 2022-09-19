from dataclasses import dataclass
from datetime import datetime
from re import compile
from typing import TextIO

time_format = '%H:%M'
time_pattern = compile('\\d\\d:\\d\\d').pattern
issue_id_pattern = compile('\\w+-\\d+').pattern
comment_pattern = compile('.+').pattern
log_write_format = '{start_time}\\{issue_id}\\{end_time}\\{comment}'
log_pattern = compile(f'(?P<start_time>{time_pattern})'
                      f'\\\\(?P<issue_id>{issue_id_pattern})'
                      f'\\\\(?P<end_time>{time_pattern})'
                      f'\\\\(?P<comment>{comment_pattern})?')


@dataclass
class Log:
    issue_id: str
    start_time: datetime
    end_time: datetime
    comment: str


def parse_log(log_line):
    match = log_pattern.fullmatch(log_line)
    if not match:
        raise ValueError(f'Line \'{log_line}\' doesnt match the pattern \'{log_pattern.pattern}\'')

    issue_id = match.group('issue_id')
    start_time = datetime.strptime(match.group('start_time'), time_format)
    end_time = datetime.strptime(match.group('end_time'), time_format)
    comment = match.group('comment')
    if start_time >= end_time:
        raise ValueError('Start time must be less than end time')
    return Log(issue_id, start_time, end_time, comment)


def read_log(file: TextIO):
    lines = (line.strip() for line in file)
    logs = (parse_log(line) for line in lines if line)
    for log in logs:
        yield log
