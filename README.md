# penn-mobile

[![Build and Deploy](https://github.com/pennlabs/penn-mobile/actions/workflows/cdkactions_build-and-deploy.yaml/badge.svg)](https://github.com/pennlabs/penn-mobile/actions/workflows/cdkactions_build-and-deploy.yaml)
[![Coverage Status](https://codecov.io/gh/pennlabs/penn-mobile/branch/master/graph/badge.svg)](https://codecov.io/gh/pennlabs/penn-mobile)

This repository is the Django-based successor to `labs-api-server`, containing API routes to help students manage and keep track of things around campus that matter to them. This repo contains:

- GSR Booking
- Laundry Data
- Dining Data
- Fitness Data
- News and Events
- Posts and Polls
- Notifications

## Install

- `git clone https://github.com/pennlabs/penn-mobile.git`
- `cd penn-mobile/backend`
- `brew install mysql`
- `pipenv install --dev`
- `pipenv run python manage.py migrate`
- `pipenv run python manage.py runserver 8000`

## Creating Users

To create users, you first have to create a main superuser.

- `pipenv run python manage.py createsuperuser` and follow the instructions
- Then, you can go to `localhost:8000/admin/auth/user/add/` to add more users.

## Exploring the API

- Expore the API via our [auto-generated documentation](https://pennmobile.org/api/documentation/)! This is a really good way to click around and discover stuff.