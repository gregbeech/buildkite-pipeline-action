# Container image that runs your code
FROM python:3.8.2-slim

# Copies your code file from your action repository to the filesystem path `/` of the container
COPY main.py /main.py

# Code file to execute when the docker container starts up (`entrypoint.py`)
ENTRYPOINT ["python", "/main.py"]
