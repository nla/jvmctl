# Make a container for building RHEL8 RPMs
#FROM nla-registry-quay-quay.apps.dev-containers.nla.gov.au/nla/ubi10
FROM registry.access.redhat.com/ubi10/ubi

MAINTAINER Peter Hine <phine@nla.gov.au>
LABEL vendor="RPM BUILD" \
      version="1.0" \
      release="1" \
      summary="RPM builder for RHEL10" \
      description="RPM builder for RHEL10"

USER root
COPY . /tmp/
WORKDIR /tmp
RUN bash ./nla_install.sh && rm -rf /tmp/*

ENTRYPOINT ["bash", "-c", "/docker-entrypoint.sh"]
