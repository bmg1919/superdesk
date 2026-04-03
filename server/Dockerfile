FROM alpine:3.23.3

RUN apk add --no-cache \
python3 python3-dev py3-pip py3-virtualenv git gcc curl \
# lxml
libxml2-dev libxslt-dev \
#  libxmlsec1-dev libxmlsec1-openssl \
xmlsec libxml2-dev pkgconf \
# PIL
zlib-dev jpeg-dev \
# libmagic-dev \
libmagic \
# reportlab
font-dejavu

# setup venv
ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m virtualenv "$VIRTUAL_ENV"
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# update venv
RUN python3 -m pip install -U pip wheel setuptools

# install server
WORKDIR /opt/superdesk/
COPY requirements.txt .
RUN python3 -m pip install -Ur requirements.txt

ENV PYTHONUNBUFFERED=1
ENV C_FORCE_ROOT=False
ENV CELERYBEAT_SCHEDULE_FILENAME=/tmp/celerybeatschedule.db
ENV TZ=Europe/Prague

COPY . .

ENTRYPOINT [ "/opt/superdesk/docker/start.sh" ]
CMD ["honcho", "start"]