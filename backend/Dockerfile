FROM pennlabs/django-base:b269ea1613686b1ac6370154debbb741b012de1a-3.11

RUN wget -q https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
RUN apt-get install ./google-chrome-stable_current_amd64.deb -y

LABEL maintainer="Penn Labs"

# Copy project dependencies
COPY Pipfile* /app/

# Install project dependencies
RUN pipenv install --system

# Copy project files
COPY . /app/

ENV DJANGO_SETTINGS_MODULE pennmobile.settings.development
ENV SECRET_KEY 'temporary key just to build the docker image'

# Collect static files
RUN python3 /app/manage.py collectstatic --noinput
