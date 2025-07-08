%define name jvmctl
%define version %(cat VERSION)
%define release %(cat RELEASE)

Summary: Deploy and manage Java applications on RHEL servers
Name: %{name}
Version: %{version}
Release: %{release}
Source:  %{expand:%%(pwd)}
License: MIT
Group: Development/Libraries
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-buildroot
Prefix: %{_prefix}
BuildArch: noarch
Vendor: NLA BSS
Packager: USER <user@shire.nla.gov.au>
Requires: git
Url: https://github.com/nla/jvmctl
Distribution: elX


%description
Deploy and manage Java applications on RHEL servers

%pre
/usr/bin/getent group builder > /dev/null || /usr/sbin/groupadd -r builder -g 440
/usr/bin/getent passwd builder > /dev/null || /usr/sbin/useradd -r -g builder -u 440 -c "Builder service account" builder
exit 0

%prep
%build

%install
/usr/bin/mkdir -p $RPM_BUILD_ROOT%{_bindir}/ $RPM_BUILD_ROOT/etc/bash_completion.d
/usr/bin/cp %{SOURCEURL0}/%{name}/* $RPM_BUILD_ROOT%{_bindir}/
/usr/bin/cp %{SOURCEURL0}/bash_completion/* $RPM_BUILD_ROOT/etc/bash_completion.d/

%post
# Remove site-packages directories, from previous installations
for dir in $(/usr/bin/ls -d /usr/lib*/python*/site-packages/%{name}* 2>/dev/null)
do
  /usr/bin/rm -rf "${dir}" 2>/dev/null
done
if [ ! -e "/etc/%{name}.conf" ]
then
  echo '[jvm]
EXEC_PREFIX = /usr/bin/logduct-run --fd 3:gc
GC_LOG_OPTS = -Xloggc:/dev/fd/3
LOG_DIR = /misc/bss/jvmctl
' >"/etc/%{name}.conf"
fi
/usr/bin/mkdir -p /etc/jvmctl/apps
/usr/sbin/restorecon -F "/etc/%{name}.conf" /etc/jvmctl/apps

%files
%defattr(644,root,root,755)
%attr(755, root, root) %{_bindir}/hsperf
%attr(755, root, root) %{_bindir}/jvmctl
%attr(644, root, root) /etc/bash_completion.d/jvmctl

%changelog
* Tue Jun 17 2025 Peter Hine <phine@nla.gov.au> 0.6.6
- Revert changes for python 3.12 regex strings.
- Remove some python errors in certain cirumstances, and allow the Operating System's error to be seen.
- list now will show a disabled servcie as disabled, not stopped.

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
- Shutting down fapolicyd on 'deploy' only, and starting back up again, including if build fails.
- jvmctl 'show' uses 'less' and not splat to the screen.
- Builds take place in /var/tmp/jvmctl/ not some random directory. Better for fapolicyd, if it is used.
- jvmctl using a spec file to build rather setup.py (files left in place for review).
  This avoids the problem discussed in jvmctl/README.
