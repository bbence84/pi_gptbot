# NOT WORKING YET, WORK IN PROGRESS

# For more information, please refer to https://aka.ms/vscode-docker-python
FROM ubuntu:latest

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1

# Install package dependencies
RUN apt-get update -y && \
    apt-get install python3 -y && \
    apt-get install python3-pip -y && \
    apt-get install usbutils -y && \
    apt-get install -y sudo -y && \
    apt-get install -y --no-install-recommends \
        libasound2-dev \
        alsa-base \
        alsa-utils \
        libsndfile1-dev && \
    apt-get clean
RUN pip3 install pyalsaaudio
# Install pip requirements
COPY requirements.txt .
RUN python3 -m pip install -r requirements.txt

WORKDIR /app
COPY . /app

# Creates a non-root user with an explicit UID and adds permission to access the /app folder
RUN adduser -u 5678 --disabled-password --gecos "" appuser && chown -R appuser /app
USER appuser

CMD ["python3", "app/bot.py"]
