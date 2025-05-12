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
Packager: ADMINPEH <adminpeh@shire.nla.gov.au>
Requires: git
Url: https://github.com/nla/jvmctl
Distribution: el9


%description
Deploying and manage Java applications on RHEL servers

%pre
/usr/bin/getent group builder > /dev/null || /usr/bin/groupadd -r builder -g 440
/usr/bin/getent passwd builder > /dev/null || /usr/bin/useradd -r -g builder -u 440 -c "Builder service account" builder
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

%files
%defattr(644,root,root,755)
%attr(755, root, root) %{_bindir}/hsperf
%attr(755, root, root) %{_bindir}/jvmctl
%attr(644, root, root) /etc/bash_completion.d/jvmctl
