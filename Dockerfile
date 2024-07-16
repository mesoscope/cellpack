### Build image ###
FROM python:3.10

WORKDIR /cellpack
COPY . /cellpack

RUN python -m pip install --upgrade pip --root-user-action=ignore
RUN python -m pip install . --root-user-action=ignore

# Install AWS CLI
RUN apt-get update && apt-get install -y awscli

COPY docker-entrypoint.sh /usr/local/bin/
RUN ["chmod", "+x", "/usr/local/bin/docker-entrypoint.sh"]


# Copy and set permissions for the AWS configure script
COPY configure-aws.sh /usr/local/bin/
RUN ["chmod", "+x", "/usr/local/bin/configure-aws.sh"]

ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]