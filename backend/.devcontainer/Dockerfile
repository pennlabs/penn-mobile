FROM --platform=linux/amd64 python:3.11-slim-buster

ARG IMAGE_NAME=pennlabs/mobile-backend-devcontainer

# Install build dependencies
RUN apt-get update && apt-get install -y gcc libpq-dev libc-dev git-all \
    && rm -rf /var/lib/apt/lists/*


RUN pip install pipenv

ENV DJANGO_SETTINGS_MODULE pennmobile.settings.development
ENV SECRET_KEY 'temporary key just to build the docker image'