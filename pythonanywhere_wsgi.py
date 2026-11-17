"""Import this application from PythonAnywhere's Web-tab WSGI configuration."""
import getpass
import os

from hosted import create_application

username = getpass.getuser()
configured_host = os.environ.get("PASSPORT_AGENT_HOST")
hosts = {configured_host} if configured_host else {
    f"{username}.pythonanywhere.com",
    f"{username}.eu.pythonanywhere.com",
}
application = create_application(hosts)
