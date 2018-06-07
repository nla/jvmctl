sendlog
=======

Poll log files for new lines, parse timestamps and send securely to a central syslog server.

Syslog fields are populated by matching regular expressions against file 
paths and log lines and extracting as named groups (`msg`, `app_name`,
`procid`, `date`, `time`).

The log files to send are specified with a string that contain globs and
macros (DAY, MONTH, YEAR) like `/logs/*/${YEAR}${MONTH}/stdio.*.log`.

Usage
-----
```
usage: sendlog [options...] fileglob

optional arguments:
  -h, --help            show this help message and exit
  --host HOST           hostname of syslog server
  --port PORT           port of syslog server
  --ca-certs CA_CERTS   certificate of CA to trust
  --certfile CERTFILE   client certificate to identify as
  --keyfile KEYFILE     key corresponding to the client certificate
  --insecure            disable server certificate validation
  --verbose, -v
  --statefile STATEFILE
                        file to save and load current log reading positions in
  --path-regex PATH_REGEX
  --line-regex LINE_REGEX
  --date-format DATE_FORMAT
  --time-format TIME_FORMAT
  --interval INTERVAL, -i INTERVAL
                        interval in seconds to repeat at
  --reset               reset state to end of all files
  --first-reset         reset if the state file does not exist
  --max-length MAX_LENGTH
                        maximum message length to truncate to
  --facility FACILITY   syslog facility name or number
  --severity SEVERITY   syslog severity level

```

Testing Configurations
----------------------

When testing sendlog configurations it's useful to skip sending to the server. If you omit
the `--host` option then sendlog will instead print the data it would normally send to the
server to stdout.

It's also a good idea to use the `--verbose` option which will cause sendlog to print lines
that didn't match the configured regexs.

Examples
--------

### jvmctl/logduct application logs

    sendlog
    --first-reset
    --interval 5
    --statefile /var/spool/sendlog.state
    --date-format %Y-%m-%d
    --time-format %H:%M:%S.%f
    --path-regex '.*/(?P<app_name>[^/]+)/\d+/stdio\.(?P<date>\d\d\d\d-\d\d-\d\d)\.log'
    --line-regex '(?P<time>\d\d:\d\d:\d\d\.\d\d\d) (?P<procid>[^ *]+): (?P<msg>.*)'
    '/logs/*/${YEAR}${MONTH}/stdio.*.log'

### Web server access logs

Assuming your logs are stored in /var/log/nginx/${sitename}.log:

    sendlog
    --first-reset
    --interval 5
    --statefile /var/spool/sendlog-nginx.state
    --facility uucp
    --date-format %d/%b/%Y
    --time-format %H:%M:%S
    --path-regex '/var/log/(?P<app_name>nginx)/(?P<procid>\w+\.log)'
    --line-regex '(?P<msg>\S+ \S+ \S+ \[(?P<date>\d+\/\w+\/\d+):(?P<time>\d+:\d+:\d+) [+-]\d\d\d\d\] "[^"]*" \S+ \S+ "[^"]*" "[^"]*" \S+ https?:\/\/(?P<procid>[^: ]+).*)'
    '/var/log/nginx/*.log'

### Handling syslog server outages

Currently sendlog has no autoreconnect facility itself. If your syslog server
goes away it exits. We currently recommend running it as a systemd 
service and enable the restart option:

    Restart=always
    RestartSec=30s

Installation
------------

As an RPM:

    python setup.py bdist_rpm
    rpm -i dist/*.noarch.rpm

Or just copy sendlog/main.py somewhere and run it with Python.

Similar software
----------------

We considered most of these before writing sendlog but they either didn't
quite have the right featureset or we ran into some other practical problem.

* [filebeat](https://www.elastic.co/kr/products/beats/filebeat)
* [logstash](https://www.elastic.co/kr/products/logstash)
* [rsyslog imfile](http://www.rsyslog.com/doc/v8-stable/configuration/modules/imfile.html)
* [NXLog](https://nxlog.co/)
* [fluentd](https://www.fluentd.org/)
* [Apache Flume](https://flume.apache.org/)
