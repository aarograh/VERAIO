#Because we need python2
FROM python:2.7-slim

#Because the last existing python2 is old
RUN printf '%s\n' \
    'deb http://archive.debian.org/debian buster main' \
    'deb http://archive.debian.org/debian buster-updates main' \
    > /etc/apt/sources.list \
  && apt-get -o Acquire::Check-Valid-Until=false update \
  && apt-get install -y --no-install-recommends \
    perl \
    texlive-base \
    texlive-latex-recommended \
    texlive-latex-extra \
    texlive-fonts-recommended \
    texlive-science \
    texlive-extra-utils \
  && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir "pip<21" "setuptools<45" "wheel<0.35" \
  && pip install --no-cache-dir --no-use-pep517 "pyyaml==5.3.1"

WORKDIR /workspace

#Copy resources in
COPY yml2tex.py /usr/local/bin/yml2tex.py
COPY veraio-docs.sh /usr/local/bin/veraio-docs.sh
RUN chmod +x /usr/local/bin/veraio-docs.sh

ENTRYPOINT ["/usr/local/bin/veraio-docs.sh"]
