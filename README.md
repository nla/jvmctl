# jvmctl

`jvmctl` is a tool for deploying and managing Java applications on EL7
servers.  It wraps systemd, git, jstack and other tools to provide a
friendly command-line interface to common deployment, process management
and debugging tasks.

## Installation

jvmctl is a single Python script with no other dependencies.

1. Install Python 2.7 (you probably already have it)
2. `cp jvmctl /usr/local/bin`

## Configuration

Application configuration files look like:

    REPO=svn://svn.example.org/myapp/trunk
    PORT=1234
    HEAP_SIZE=512m

Basic shell-style `$VARIABLE` substition is supported:

    JAVA_OPTS=-Dmyapp.port=$PORT

For backwards compatibility reasons lines can be prefixed with
"export " (this has no effect).  All options are passed to the deployment
script and application as environment variables.

### Deployment Options

Option      | Default        | Description
------------|----------------|-------------------------
REPO        |                | svn or git repository url to deploy from
GIT_BRANCH  | master         | git branch to deploy from 

### Process Options

Option      | Default        | Description
------------|----------------|------------------------
USER        | webapp         | unix account to run the application under
JAVA_HOME   | /usr/lib/jvm/java-1.8.0 | path of the Java runtime to use
JAVA_OPTS   |                | extra options to pass to java (system properties, GC options etc)
HEAP_SIZE   | 128m           | amount of memory allocated to the jvm
OOM_EMAIL   | root@localhost | address to email out of memory errors to

### Webapp Options

Option        | Default        | Description
--------------|----------------|------------------------
CONTAINER     | jetty          | Servlet container to use or `none`
JETTY_VERSION | 9.2.5.v20141112 | Version of jetty to use (will be downloaded automatically)
PORT          |                | HTTP port for servlet container
ROOT_URL_PREFIX | /          | path to mount web application under
NLA_ENVIRON   | devel          | (deprecated) application environment profile

## FAQ

### Where did my logs go??

jvmctl delegates log handling to the systemd journald. Logs are stored 
in an annotated binary format in /var/log/jornal and can be viewed, tailed and
searched using `journalctl`:

    sudo jvmctl myapp log
    sudo journalctl -u jvm:myapp -f
    sudo journalctl -u jvm:myapp -n 100

See `man journalctl` for more options.  You can also configure journald to
forward logs to syslog to write to text files or a remote logserver.  See
`man journald.conf`.

### Why Python 2 and not Python 3/Perl/Ruby/Java/bash/...?

It's installed by default on most servers, starts fast and has a large standard
library with good error handling and APIs for interacting with OS services. And
I know it much better than Perl. ;-)

### How about other OSes?

jvmctl delegates to systemd for process and log management to systemd.  While it
would be possible to add support for other systems (and indeed our previous
generation tool did) standardising on one platform has made the code considerably
simpler.  In future we may consider adding Solaris support again as SMF also
provides much of the required functionality.
