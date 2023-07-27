# wareporting
  
  This is a Flask Python app to pull pre-defined reports out of Wild Apricot using the API. It is intended for use
  in situations where the built-in reports are not sufficient.

# Installation
  
The application has been developed under Python 3.10.10. It is recommended that you use a virtual environment to install and run the application.

```shell
python -m venv .venv
```
Activate the virtual environment:

```shell
source .venv/bin/activate
```

Dependencies are in requirements.txt. Install them with:

```shell
pip install -r requirements.txt
```

# Configuration

There are 4 environment variables that must be set for the application to run:

| Variable | Description |
| --- | --- |
| WA_REPORTING_API_KEY | API key for Wild Apricot, found in Authorized Applications -> wareporting |
| WA_REPORTING_CLIENT_SECRET | Client secret for Wild Apricot, found in Authorized Applications -> wareporting |
| WA_REPORTING_FLASK_SECRET_KEY | Flask secret key, used to encrypt session data; any complex value will do |
| WA_REPORTING_DOMAIN | the domain name on which the application is running, e.g. www.nova-labs.org |

Be aware that WA_REPORTING_DOMAIN is used to construct the redirect URI for OAuth2, so it must match the domain name on which the application is running, and it must accept SSL connections under that name. There is no prefix  and no ending slash, just the domain name itself. Localhost is not acceptable. To run the application locally, you can use a service like [ngrok](https://ngrok.com) to create a domain name that will accept SSL connections. You are allowed one free static domain name, use that, because:

WA_REPORTING_DOMAIN must *also* be listed as a trusted redirect URI in the Authorized Applications section of the Wild Apricot account. If it is not, the OAuth2 flow will fail with almost no details.

# Running the application

For production, you should use a WSGI server such as gunicorn. 

For development, you can run the application with:

```python
py wareporting.py
```

which will automatically turn on debug mode and debug log statements. They are fairly verbose.

# Using the application

Users log in with their Nova Labs portal username and password. As this is a separate application, logins from the portal or wautils do not "carry over". Users must have the **\[NL\] reporting** signoff to use the application.

Please note that some reports can be quite slow. It seems as though the API is throttled, so it may take a while to pull down a large amount of data.