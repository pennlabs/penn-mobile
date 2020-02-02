# student-life

This repository will hopefully be the Django-based successor to `labs-api-server`, containing API routes to help students manage keep track of things around campus that matter to them. Currently, this repo contains:

- Group GSR Booking

## Install

- `git clone https://github.com/pennlabs/student-life.git`
- `cd student-life`
- `pipenv install`
- `pipenv run python manage.py migrate`
- `pipenv run python manage.py runserver 8000`

You should be good to go!

## Creating Users

To create users, you first have to create a main superuser.

- `pipenv run python manage.py createsuperuser` and follow the instructions
- Then, you can go to `localhost:8000/admin/auth/user/add/` to add more users.

## Exploring the API

- Go to `localhost:8000/` in your browser to explore the API! This is a really good way to click around and discover stuff.

## Rudimentary API Documentation

- `GET /users/`
  - List all users, with their pennkey and the groups they are members of.

- `GET /users/<pennkey>/`
  - Detail view on one user.

- `GET /users/<pennkey>/gsr_booking_credentials`
  - List Wharton Session ID (if available), its expiration date, and school email.

- `POST /users/<pennkey>/save_session_id/`
  - Associates a Wharton Session ID with a user.
<table>
    <tbody>
        <tr>
            <td>URL</td>
            <td><code>https://studentlife.pennlabs.org/{pennkey}/save_session_id/</code></td>
        </tr>
        <tr>
            <td>HTTP Methods</td>
            <td>POST</td>
        </tr>
        <tr>
            <td>Response Formats</td>
            <td>JSON</td>
        </tr>
        <tr>
            <td>Parameters</td>
            <td>
                <table>
                    <thead>
                        <tr>
                            <th>Name</th>
                            <th>Default</th>
                            <th>Description</th>
                            <th>Example Values</th>
                        </tr>
                    </thead>
                    <tbody>
                      <tr>
                          <td><tt>session_id</tt></td>
                          <td><strong>Optional</strong></td>
                          <td>The student's Wharton Session ID</td>
                          <td><tt>k44mhe1ta84jw9vdva8y5dv387a1ozd9</tt></td>
                      </tr>
                      <tr>
                          <td><tt>expiration_date</tt></td>
                          <td><strong>Required</strong></td>
                          <td>Session ID expiration date</td>
                          <td><tt>2020-01-25</tt></td>
                      </tr>
                    </tbody>
                </table>
            </td>
        </tr>
        <tr>
          <td>Notes</td>
          <td><tt>session_id</tt> can be <tt>null</tt> as it is always a temporary value.</td>
        </tr>
    </tbody>
</table>

- `POST /users/<pennkey>/save_email/`
  - Associates a school email with a user for LibCal.
<table>
    <tbody>
        <tr>
            <td>URL</td>
            <td><code>https://studentlife.pennlabs.org/{pennkey}/save_email/</code></td>
        </tr>
        <tr>
            <td>HTTP Methods</td>
            <td>POST</td>
        </tr>
        <tr>
            <td>Response Formats</td>
            <td>JSON</td>
        </tr>
        <tr>
            <td>Parameters</td>
            <td>
                <table>
                    <thead>
                        <tr>
                            <th>Name</th>
                            <th>Default</th>
                            <th>Description</th>
                            <th>Example Values</th>
                        </tr>
                    </thead>
                    <tbody>
                      <tr>
                          <td><tt>email</tt></td>
                          <td><strong>Required</strong></td>
                          <td>The student's school email</td>
                          <td><tt>pennkey@seas.upenn.edu</tt></td>
                      </tr>
                    </tbody>
                </table>
            </td>
        </tr>
    </tbody>
</table>

- `GET /users/<pennkey>/invites/`
  - Get all open invites for a user.

- `POST /users/<pennkey>/activate/`
  - **IMPORTANT** This endpoint should be called when the user logs in. Updates any invites with the user's Pennkey to be associated with their account (now that it exists), and also adds their name and pennkey to the search index (see below)

- `GET /users/search/?q=<search query>`
  - Returns all users whose name or pennkey matches the search query. Users are only included in the autocomplete if they have an account in the system and their account has been activated -- otherwise users will need to invite based off of Pennkey.

- `POST /membership/invite/`
  - Invite a user to a group. This is a POST request, where you sent a JSON payload in the following format:

    ```json
    {
      "user": <pennkey>,
      "group": <group id>
    }
    ```

    or, for bulk invites,

    ```json
    {
      "user": '<pennkey>, <pennkey2>, ...'
      "group": <group id>
    }
    ```

    **Note** that the user with the associated Pennkey *need not* have an account in the system. the invite will be entered either way!
- `POST /membership/<invite id>/accept/`
  - Accept an invite. If an invite with the given ID has already been accepted, will return a 400.

- `POST /membership/<invite id>/decline/`
  - Decline an invite. If the invite has already been accepted, will return a 400.

- `POST /membership/pennkey/`
  - Update the pennkey for a user. This is a POST request, where you sent a JSON payload `{"user": <pennkey>, "group": <group ID>, "allow": <true/false>}`.

- `POST /membership/notification/`
  - Update the pennkey for a user. This is a POST request, where you sent a JSON payload `{"user": <pennkey>, "group": <group ID>, "active": <true/false>}`.

- `GET /groups/`
  - Get a list of all groups.

- `POST /groups/`
  - Add a new group. `POST` JSON body needs to include `owner`, `name`, and `color`.

- `GET /groups/<group ID>/`
  - Get a group, with a list of members.

- `PUT /groups/<group ID>/`
  - Update a group's information.

- `GET /groups/<group ID>/invites/`
  - Get a list of all open invites to this group.
