sendlog
=======

Examples
--------

### Web server access logs

Assuming your logs are stored in /var/log/nginx/${sitename}.log:

    --date-format %d/%b/%Y
    --time-format %H:%M:%S
    --path-regex '/var/log/(?P<app_name>nginx)/(?P<procid>\w+\.log)'
    --line-regex '(?P<msg>\S+ \S+ \S+ \[(?P<date>\d+\/\w+\/\d+):(?P<time>\d+:\d+:\d+) [+-]\d\d\d\d\] "[^"]*" \S+ \S+ "[^"]*" "[^"]*" \S+ https?:\/\/(?P<procid>[^: ]+).*)'