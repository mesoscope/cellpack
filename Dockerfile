### Build image ###
FROM python:3.10

WORKDIR /cellpack
COPY . /cellpack

RUN python -m pip install --upgrade pip --root-user-action=ignore
RUN python -m pip install . --root-user-action=ignore

COPY docker-entrypoint.sh /usr/local/bin/
RUN ["chmod", "+x", "/usr/local/bin/docker-entrypoint.sh"]
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]