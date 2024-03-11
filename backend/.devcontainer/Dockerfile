FROM --platform=linux/amd64 python:3.11-slim-buster

ARG IMAGE_NAME=pennlabs/mobile-backend-devcontainer

# Install build dependencies
RUN apt-get update && apt-get install -y gcc libpq-dev libc-dev git-all wget \
    && rm -rf /var/lib/apt/lists/*


RUN wget -q https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb

RUN apt install -y ./google-chrome-stable_current_amd64.deb

RUN pip install pipenv

ENV DJANGO_SETTINGS_MODULE pennmobile.settings.development
ENV SECRET_KEY 'temporary key just to build the docker image'