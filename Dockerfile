##########################################
# Dockerfile for udata
##########################################

FROM udata/system

# Optionnal build arguments
ARG REVISION="N/A"
ARG CREATED="Undefined"

# OCI annotations
# See: https://github.com/opencontainers/image-spec/blob/master/annotations.md
LABEL "org.opencontainers.image.title"="udata all-in-one"
LABEL "org.opencontainers.image.description"="udata with all known plugins and themes"
LABEL "org.opencontainers.image.authors"="Open Data Team"
LABEL "org.opencontainers.image.sources"="https://github.com/opendatateam/docker-udata"
LABEL "org.opencontainers.image.revision"=$REVISION
LABEL "org.opencontainers.image.created"=$CREATED

RUN apt-get update && apt-get install -y --no-install-recommends \
    # uWSGI rooting features
    libpcre3-dev \
    mime-support \
    # Clean up
    && apt-get autoremove\
    && apt-get clean\
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Install udata and all known plugins
COPY ./requirements/install.pip /tmp/requirements/install.pip
COPY requirements.pip /tmp/requirements.pip
RUN pip install --upgrade pip
RUN pip install -r /tmp/requirements.pip && pip check || pip install -r /tmp/requirements.pip
RUN rm -r /root/.cache

RUN mkdir -p /udata/fs /src

COPY udata.cfg entrypoint.sh /udata/
COPY uwsgi/*.ini /udata/uwsgi/

WORKDIR /udata

VOLUME /udata/fs

ENV UDATA_SETTINGS /udata/udata.cfg

EXPOSE 7000

ENTRYPOINT ["/udata/entrypoint.sh"]
CMD ["uwsgi"]
