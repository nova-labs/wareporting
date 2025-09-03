# wareporting
  
  This is a Flask Python app to pull pre-defined reports out of Wild Apricot using the API. It is intended for use
  in situations where the built-in reports are not sufficient. Wild Apricot pagination has been added
  for API calls that support `$top` and `$skip`, using a default page size of 500 records.

# Installation
  
The application has been developed under Python 3.10.10. It is recommended that you use a virtual environment to install and run the application. (Either `.venv` or `venv` will be ignored by git.) The directions below are for bash but similar ones with slightly different commands will work on Windows as well.

```shell
python -m venv .venv
```
Activate the virtual environment and install `pip-tools` if not already installed:

```shell

```bash
source .venv/bin/activate
python -m pip install pip-tools
```

Dependencies are managed by [pip-tools](https://github.com/jazzband/pip-tools) in requirements.in, and compiled by `pip-sync` to `requirements.txt`. 
Install them with:

```shell
pip-sync requirements.txt
```
If you add or remove dependencies, please update `requirements.in` and run `pip-compile` to update `requirements.txt`, followed by pip-sync.

For development, developer-only dependencies are listed in `requirements-dev.in`. Install them with:

```shell
pip-sync requirements-dev.txt
```

If you update the dependencies in `requirements-dev.in`, run: `pip-compile dev-requirements.in -c requirements.txt` (this constrains the development packages to obey `requirements.txt`). Then run `pip-sync requirements-dev.txt`.

# Configuration

There are 4 environment variables that must be set for the application to run:

| Variable | Description |
| --- | --- |
| WA_REPORTING_API_KEY | API key for Wild Apricot, found in Authorized Applications -> wareporting |
| WA_REPORTING_CLIENT_SECRET | Client secret for Wild Apricot, found in Authorized Applications -> wareporting |
| WA_REPORTING_FLASK_SECRET_KEY | Flask secret key, used to encrypt session data; any complex value will do |
| WA_REPORTING_DOMAIN | the domain name on which the application is running, e.g. `wareporting.nova-labs.org` For development you may wish to use `localhost`, see below. |

The app will look for a `.env` file in the main directory, and if found will set / override any environment variables. This is useful for development, for production you will want a service file instead.

# User OAuth and domain names

Be aware that `WA_REPORTING_DOMAIN` is used to construct the redirect URI for OAuth2, so it must match the domain name on which the application is running, and it must accept SSL connections under that name. There is no prefix  and no ending slash, just the domain name itself. To run the OAuth locally, you can use a service like [ngrok](https://ngrok.com) to create a domain name that will accept SSL connections. You are allowed one free static domain name, use that, because:

`WA_REPORTING_DOMAIN` must *also* be listed as a trusted redirect URI in the Authorized Applications section of the Wild Apricot account. If it is not, the OAuth2 flow will fail with almost no details.

## Skipping user OAuth

Don't want to bother with ngrok? Set `WA_REPORTING_DOMAIN` to `localhost` and start the application by running wareporting directly (see below). Access your application on localhost or 127.0.0.1.

In this configuration, **the "Login" buttons will not work**. Just go straight to the Report Catalog, which should be visible on all relevant pages.

Whatever you choose, you will, of course, still need to know the API key.

# Running the application

For production, you should use a WSGI server such as gunicorn. The WSGI app name is `wareporting:app`

For development, you can run the application with:

```python
python wareporting.py
```

which will automatically turn on debug mode and debug log statements. They are fairly verbose. This will also allow you to use `localhost` as the `WA_REPORTING_DOMAIN` and skip user OAuth.

# Running tests

The repository includes tests.

- Run tests: `pytest -s`.

Note: The test uses network access and valid Wild Apricot credentials. These are read-only so are safe. Because we go against the live API, network issues may cause intermittent test failures. We often cannot assert the exact number of objects the reports should return. The tests will however perform a basic sanity check.

# Using the application

Users log in with their Nova Labs portal username and password. As this is a separate application, logins from the portal or wautils do not "carry over". Users must have the `[NL] reporting` signoff to use the application.

Please note that some reports can be quite slow. It seems as though the API is throttled, so it may take a while to pull down a large amount of data.

# Wild Apricot API

There is SwaggerHub documentation for [Wild Apricot API version 2.2](https://app.swaggerhub.com/apis-docs/WildApricot/wild-apricot_public_api/7.24.0) Also see [API Version 2.2 differences](https://gethelp.wildapricot.com/en/articles/1683-api-version-2-2-differences) which has links in the sidebar that show available filters.

Postman can be configured to help you explore the API. In your Authorization area, set as follows:

| Variable | Value |
| --- | --- |
| Type | OAuth 2.0 |
| Add auth data to | Request Headers |
| Auto-refresh token | On |
| Grant Type | Client Credentials |
| Access Token URL | https://oauth.wildapricot.org/auth/token |
| Client ID | APIKEY |
| Client Secret | API key for Wild Apricot, found in Authorized Applications -> wareporting |
| Scope | auto |
| Client Authentication | Send as Basic Auth header |
| Token Request | add Key = obtain_refresh_token and Value = true, Send In = Request Body |
