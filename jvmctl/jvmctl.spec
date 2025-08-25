%define name jvmctl
%define version %(cat VERSION)
%define release %(cat RELEASE)

Summary: Deploy and manage Java applications on RHEL servers
Name: %{name}
Version: %{version}
Release: %{release}%{?dist}
#Source0: /workspace
License: MIT
Group: Development/Libraries
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-buildroot
Prefix: %{_prefix}
BuildArch: noarch
Vendor: NLA BSS
Packager: USER <user@shire.nla.gov.au>
Requires: git
BuildRequires: python3
BuildRequires: python3-setuptools
Url: https://github.com/nla/jvmctl
Distribution: elX

%description
Deploy and manage Java applications on RHEL servers

%pre
/usr/bin/getent group builder > /dev/null || /usr/sbin/groupadd -r builder -g 440
/usr/bin/getent passwd builder > /dev/null || /usr/sbin/useradd -r -g builder -u 440 -c "Builder service account" -m builder
/usr/bin/getent group webapp > /dev/null || /usr/sbin/groupadd -r webapp -g 1002
/usr/bin/getent passwd webapp > /dev/null || /usr/sbin/useradd -r -g webapp -u 439 -c "webapp service account" webapp
/usr/bin/getent group logger > /dev/null || /usr/sbin/groupadd -r logger -g 1000
/usr/bin/getent passwd logger > /dev/null || /usr/sbin/useradd -r -g logger -u 437 -c "logger service account" builder



exit 0

%prep
%build

%install
cd /workspace
python3 setup.py install --root=%{buildroot} --prefix=/usr

%post

if [ ! -e "/etc/%{name}.conf" ]
then
  echo '[jvm]
EXEC_PREFIX = /usr/bin/logduct-run --fd 3:gc
GC_LOG_OPTS = -Xloggc:/dev/fd/3
LOG_DIR = /misc/bss/jvmctl
' >"/etc/%{name}.conf"
fi
if [ -x /usr/sbin/restorecon ]; then
  /usr/sbin/restorecon -F "/etc/%{name}.conf" /etc/jvmctl/apps
fi

%files
%defattr(644,root,root,755)
%attr(755, root, root) /usr/bin/hsperf
%attr(755, root, root) /usr/bin/jvmctl
%attr(644, root, root) /etc/bash_completion.d/jvmctl
%attr(644, root, root) /etc/jvmctl/apps
%attr(644, webapp, webapp) /apps
%attr(644, logger, logger) /logs
/usr/lib/python3*

%changelog
* Mon Jul 28 2025 Peter Hine <phine@nla.gov.au> 0.6.8
- Fixed params like -d and -s not getting through to 'deploy'
- Updated Usage.
- 'deploy' adds port to the firewall.
- Add 'EXTRA_FIREWALL_PORTS' to config to specify other ports to open that just the one specified by PORT=

* Wed Jul 09 2025 Peter Hine <phine@nla.gov.au> 0.6.7
- Revert 'show' to using 'cat'. 'show' now takes a parameter of -l, which will cause it to use 'less'.
- 'list' can now take multiple application names.
- Removed the default JAVA_HOME, so applications that don't use java, do not show a java home when using 'list'.
- Added 'black' to PyCharm to format the code properly.
- Added 'view', which uses 'less' by default.

* Tue Jun 17 2025 Peter Hine <phine@nla.gov.au> 0.6.6
- Revert changes for python 3.12 regex strings.
- Remove some python errors in certain cirumstances, and allow the Operating System's error to be seen.
- 'list' now will show a disabled service as disabled, not stopped.

* Tue Jun 17 2025 Peter Hine <phine@nla.gov.au> 0.6.5
- Add changes for python 3.12 regex strings.

* Wed May 21 2025 Peter Hine <phine@nla.gov.au> 0.6.4
- Protect against trying to open the log when not root.
- Produce a better error when using 'list' or 'show' with a non existent application.

* Wed May 14 2025 Peter Hine <phine@nla.gov.au> 0.6.3
- Remove hardcoding of log directory.

* Wed May 14 2025 Peter Hine <phine@nla.gov.au> 0.6.2
- Solve deprecation warnings on RHEL9 for configparser.

* Tue May 13 2025 Peter Hine <phine@nla.gov.au> 0.6.1
- 'stop', 'start' and 'restart' actions now log to /misc/bss/jvmctl/

* Mon May 12 2025 Peter Hine <phine@nla.gov.au> 0.6.0
- 'list' can now take a parameter, of a current app, like other commands.
- Shutting down fapolicyd on 'deploy' only, and starting it back up again, including if build fails.
- jvmctl 'show' uses 'less' so as to not splat the config to the console.
- Builds take place in /var/tmp/jvmctl/ not some random directory. Better for fapolicyd, if it is used.
- jvmctl using a spec file to build rather setup.py (files left in place for review).
  This avoids the problem discussed in jvmctl/README.
