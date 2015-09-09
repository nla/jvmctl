%define versionfile %(cat VERSION)
Summary: jvmctl is a tool for deploying and managing Java applications on EL7 servers.
Name: jvmctl
Version: %{versionfile}
Release: 1.el7
Source0: https://github.com/nla/jvmctl/archive/%{version}.tar.gz
Source1: jvmctl-%{version}.tar.gz
License: MIT
Vendor: NLA BSS
Packager: Ross Paine <rpaine@nla.gov.au>
URL: https://github.com/nla/jvmctl/
Requires(pre): shadow-utils
BuildArch: noarch


%pre
getent group builder > /dev/null || groupadd -r builder
getent passwd builder > /dev/null || \
  useradd -r -g builder -d /opt/jetty -s /sbin/nologin \
  -c "Builder service account" builder
exit 0

%description
jvmctl is a tool for deploying and managing Java applications on EL7 servers.
It wraps systemd, git, jstack and other tools to provide a friendly
command-line interface to common deployment, process management and debugging
tasks.

%prep

%setup

%build

%install
mkdir -p $RPM_BUILD_ROOT/etc/jetty
mkdir -p $RPM_BUILD_ROOT/opt/bin
mkdir -p $RPM_BUILD_ROOT/opt/jetty
pushd $RPM_BUILD_ROOT
ln -s /etc/jetty ./opt/jetty/conf
popd

cp -v jvmctl $RPM_BUILD_ROOT/opt/bin

%clean
rm -fr ${RPM_BUILD_ROOT}

%check
test -e $RPM_BUILD_ROOT/opt/bin/jvmctl

%post
/usr/sbin/update-alternatives --install /usr/local/bin/jvmctl jvmctl /opt/bin/jvmctl 10 \
         --slave /usr/local/bin/jettyctl jettyctl /opt/bin/jvmctl

%files
%defattr(-,root,root)
/etc/jetty
/opt

