FROM python:3.9-slim as base

ENV LANG C.UTF-8
ENV LC_ALL C.UTF-8
ENV PYTHONDONTWRITEBYTECODE 1s
ENV PYTHONFAULTHANDLER 1


FROM base AS python-deps

ENV PIPENV_VENV_IN_PROJECT 1

# Install pipenv and compilation dependencies:
#	* gcc is needed to compile various packages
#   * libpq-dev is needed to install psycopg2 from source (psycopg2-binary includes outdated version of pqlib)
RUN pip install pipenv
RUN apt-get update \
	&& apt-get install -y gcc libpq-dev

# Install python dependencies in /.venv
COPY Pipfile .
COPY Pipfile.lock .
RUN pipenv install --deploy

FROM base AS runtime

ENV DEBIAN_FRONTEND noninteractive

RUN apt-get update \
	&& apt-get install -y tshark iptables iptables-persistent libpq5

# Copy virtual env from python-deps stage
COPY --from=python-deps /.venv /.venv
ENV PATH="/.venv/bin:$PATH"

# Create and switch to a new user
# RUN useradd --create-home capture
# WORKDIR /home/capture
# USER capture

WORKDIR /aretha

# Install application into container
COPY . .

# Run the application
ENTRYPOINT ["./start.sh"]

