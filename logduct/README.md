logduct
=======

Installing
----------

### Building an RPM

    python setup.py bdist_rpm
    rpm -ivh dist/logduct*noarch.rpm

### Building a tarball

    python setup.py bdist_dumb

### Just installing immediately

    python setup.py install

Configuring
-----------

Enable and start the socket:

    systemctl enable logductd.socket
    systemctl start logductd.socket

Add default configuration to /etc/jvmctl.conf:

    [jvm]
    EXEC_PREFIX = /usr/bin/logduct-run --fd 3:gc
    GC_LOG_OPTS = -Xloggc:/dev/fd/3
