"""Shared read-only Google credentials (service account key kept outside the repo)."""
import os
from google.oauth2 import service_account
KEY = os.path.expanduser("~/.config/herbivoracious/google-readonly.json")
SCOPES = ["https://www.googleapis.com/auth/webmasters.readonly", "https://www.googleapis.com/auth/analytics.readonly"]
def creds():
    return service_account.Credentials.from_service_account_file(KEY, scopes=SCOPES)
