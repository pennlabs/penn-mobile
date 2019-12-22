# student-life
This repository will hopefully be the django-based successor to labs-api-server, containing API routes to help students
manage keep track of things around campus that matter to them. Currently, this repo contains:
- Group GSR Booking

## Install
- `git clone`
- `cd` in
- `pipenv install`
- `pipenv run python manage.py migrate`
- `pipenv run python manage.py runserver 8000`

You should be good to go!

## Creating Users
To create users, you first have to create a main superuser.
- `python manage.py createsuperuser` and follow the instructions
- Then, you can go to `localhost:8000/admin/auth/user/add/` to add more users.

## Exploring the API
- Go to `localhost:8000/` in your browser to explore the API! This is a really good way to click around and discover stuff.

## Rudimentary API Documentation
- `GET /users/`
    - List all users, with their pennkey and the groups they are members of.
- `GET /users/<pennkey>/`
    - Detail view on one user.
- `GET /users/<pennkey>/invites/`
    - Get all open invites for a user.
- `POST /membership/invite/`
    - Invite a user to a group. This is a POST request, where you sent a JSON payload in the following format: 
    ```
    {
      "user": <pennkey>, 
      "group": <group ID>
    }
    ```
    or, for bulk invites,
    ```
    {
      "user": '<pennkey>,<pennkey2>,...' 
      "group": <group ID>
    }
    ```
- `POST /membership/<invite id>/accept/`
    - Accept an invite.
- `POST /membership/<invite id>/decline/`
    - Decline an invite.
- `POST /membership/pennkey/`
    - Update the pennkey for a user. This is a POST request, where you sent a JSON payload `{"user": <pennkey>, "group": <group ID>, "allow": <true/false>}`
- `POST /membership/notification/`
    - Update the pennkey for a user. This is a POST request, where you sent a JSON payload `{"user": <pennkey>, "group": <group ID>, "active": <true/false>}`
- `GET /groups/`
    - Get a list of all groups
- `POST /groups/`
    - Add a new group. `POST` JSON body needs to include `owner`, `name`, and `color`.
- `GET /groups/<group ID>/`
    - Get a group, with a list of members.
- `PUT /groups/<group ID>/`
    - Update a group's information.
- `GET /groups/<group ID/invites/`
    - Get a list of all open invites to this group.


