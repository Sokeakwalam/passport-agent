# Deploy Passport Agent to PythonAnywhere

The upload archive contains the application and instructions. It excludes your local saved checklists and database. The hosted app creates its own SQLite database on PythonAnywhere.

## 1. Upload the archive

In PythonAnywhere, open **Files**, go to your home folder (`/home/YOUR_USERNAME`), and upload `passport-agent-pythonanywhere.zip`.

## 2. Extract it

Open **Consoles → Bash** and run:

```sh
cd ~
unzip -o passport-agent-pythonanywhere.zip
```

This creates `/home/YOUR_USERNAME/passport-agent`. No packages or virtual environment are needed; the application uses the Python standard library.

Do not run `python3 server.py` on PythonAnywhere. The Web tab will run the hosted entry point for you.

## 3. Create the web app

1. Open **Web → Add a new web app**.
2. Choose your included PythonAnywhere website address.
3. Choose **Manual configuration**.
4. Select **Python 3.11 or newer**.
5. Complete the wizard.

If a web app already exists, use its Web tab and WSGI configuration instead of creating another one.

## 4. Set the WSGI configuration

On the **Web** tab, open the linked **WSGI configuration file**. Replace the example contents with:

```python
import os
import sys

project = os.path.expanduser("~/passport-agent")
if project not in sys.path:
    sys.path.insert(0, project)

from pythonanywhere_wsgi import application
```

This code finds your home directory automatically. You do not need to replace a username in it.

Save the file. Leave the **Virtualenv** field empty. Do not add a static mapping at `/`; the application serves its own assets and API.

The entry point accepts both `YOUR_USERNAME.pythonanywhere.com` and `YOUR_USERNAME.eu.pythonanywhere.com`. If your actual hostname differs, add this line **before** importing `application`:

```python
os.environ["PASSPORT_AGENT_HOST"] = "YOUR_ACTUAL_HOSTNAME"
```

Use the hostname only, without `https://` or `/`.

## 5. Reload and open

Back on the **Web** tab:

1. Enable **Force HTTPS** in the security settings.
2. Click the green **Reload** button.
3. Open the website link using `https://`.

Open `/api/health` on that same address to check that the back end is responding. It should return JSON with `"status": "ok"`.

## 6. Check the hosted journey

- Generate a checklist and select identity documents; verify the total.
- Save progress, refresh the page, and resume it.
- Open a private browser window; it should have its own separate journey.
- Delete the original saved journey and verify it disappears.
- Check print/PDF and text download.

The hosted version says saved progress lives on the website's server. It uses a browser cookie with HttpOnly, SameSite and Secure on HTTPS. People can use it without accounts; their saved journey is accessible in the browser where they saved it.

## Updating the site

Upload a new archive to your home folder, run the same `unzip -o` command, then use **Reload** on the Web tab. Archives exclude the data directory, so extracting one does not overwrite the hosted database.

The hosted data file is `/home/YOUR_USERNAME/passport-agent/data/passport-agent.sqlite3`. Keep a private backup before changing database-related code.

## Troubleshooting

- **Default PythonAnywhere page:** check that you saved the WSGI configuration and clicked Reload.
- **Import error:** verify the files are inside `~/passport-agent`, not an extra nested folder. The Web tab links to the error log.
- **403 response:** verify the hostname. Set `PASSPORT_AGENT_HOST` in the WSGI file if needed.
- **Save error:** check the error log and ensure the app can write to its `data` directory.
- **Old interface:** Reload the web app, then refresh your browser.
- **App expired:** use the renewal control on PythonAnywhere's Web tab; free accounts have an expiry date.

The citizenship-content limitations documented in `CONTENT_REVIEW.md` still apply. Preparing the archive does not publish it; the website becomes available after you complete the Web-tab setup.

Official PythonAnywhere guidance: [manual WSGI configuration](https://help.pythonanywhere.com/pages/Flask/), [static file mappings](https://help.pythonanywhere.com/pages/StaticFiles/).
