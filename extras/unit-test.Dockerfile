FROM ubuntu:20.04

RUN apt-get update --fix-missing
RUN apt-get install -y git
RUN apt-get install -y python3
RUN apt-get install -y python3-venv
RUN apt-get install -y python3-pip

WORKDIR /repo

# upgrade pip so that we can install using poetry backend
RUN pip install --upgrade pip

# install PHP
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get install -y php php-curl

# install Node/NPM
RUN apt-get install -y nodejs npm

# install deps
ADD requirements.txt requirements.txt
ADD requirements_dev.txt requirements_dev.txt
RUN pip install -r requirements.txt
RUN pip install -r requirements_dev.txt

ADD .flake8 .flake8
ADD .pylintrc .pylintrc
ADD mypy.ini mypy.ini
ADD pyproject.toml pyproject.toml
ADD poetry.lock poetry.lock
ADD bifrostrpc bifrostrpc
ADD tests tests

# XXX: couldn't use 'poetry install' here because somehow the paradox libs get dropped
RUN pip install -e .

CMD pytest -x tests
