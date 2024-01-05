# Jira logger
A console application for reading work logs from a .CSV file
and sending that log to Jira. Log format:

```
start_time\issue_id\end_time\[comment]
```

where:

- *start_time* - in 24h format *hh:mm*. Example: 09:45
- *issue_id* - human id. Example: SSP-942
- *end_time* - in 24h format *hh:mm*. Example: 15:02
- *comment* - any single line text. Optional

Requires python 3.10.

### How to run

```
usage: jlog.py [-h] -j JIRA_URL -f FILEPATH [-e ENCODING] -u USER [-p PASSWORD] [-d START_DATE]

options:
  -h, --help            show this help message and exit
  -j JIRA_URL, --jira-url JIRA_URL
                        jira base URL
  -f FILEPATH, --filepath FILEPATH
                        path to target CSV file with logs
  -e ENCODING, --encoding ENCODING
                        encoding of the target CSV file
  -u USER, --user USER  jira username
  -p PASSWORD, --password PASSWORD
                        jira password. Default: prompted
  -d START_DATE, --start-date START_DATE
                        start date in format 'dd.mm.yyyy'. Default: current date
```

Example:

```commandline
python -m jlog -j https://jira.my.lab -f "C:\Users\MyUser\Documents\log.csv" -u myname
```

