ARG SOURCE_IMAGE
FROM ${SOURCE_IMAGE}

WORKDIR /package

COPY requirements_dev.txt ./

RUN pip install -r requirements_dev.txt

COPY pyproject.toml setup.py ./
COPY bifrostrpc ./bifrostrpc

RUN pip install .

COPY tests ./tests

RUN pytest tests/
