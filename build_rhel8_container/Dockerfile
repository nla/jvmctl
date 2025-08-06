# Make a container for building RHEL8 RPMs
FROM container-registry.nla.gov.au.nla.gov.au/nla/ubi8

MAINTAINER Peter Hine <phine@nla.gov.au>
LABEL vendor="RPM BUILD" \
      version="1.0" \
      release="1" \
      summary="RPM builder for RHEL8" \
      description="RPM builder for RHEL8"

USER root
COPY . /tmp/
WORKDIR /tmp
RUN bash ./nla_install.sh && rm -rf /tmp/*

ENTRYPOINT ["bash", "-c", "/docker-entrypoint.sh"]
