# Host Passport Agent on GitHub Pages

GitHub Pages is the preferred hosting target. The website runs in the browser and needs no Python server. The Python source remains the source of the checklist rules and is used when rebuilding the site.

## 1. Create a repository

1. Sign in to your GitHub account.
2. Open [Create a new repository](https://github.com/new?name=passport-agent).
3. Enter **passport-agent** as the repository name.
4. Choose **Public** to use GitHub Pages with a free personal account.
5. Select **Add a README file**.
6. Click **Create repository**.

Your expected repository address is `https://github.com/Sokeakwalam/passport-agent` if you create it under your connected account.

## 2. Upload the prepared website

Two upload layouts are supported. Use just one.

### Full project (recommended)

Use `dist/passport-agent-github-source.zip`. Extract it on your Mac. It contains the Python source, browser source, tests, these instructions, and the ready-to-host `docs` folder. Upload the extracted contents to the root of the repository, keeping the `docs`, `static`, and `tests` directories.

Use **Add file → Upload files**, drag the extracted contents into the upload area, and commit the files. Do not upload the ZIP itself as the website. Do not add an extra enclosing folder above `docs`.

Do not upload your local `data` folder or a SQLite database. Neither prepared ZIP includes saved checklists.

### Website files only

Use `dist/passport-agent-github-pages.zip`. Extract it, then upload its contents directly to the repository root. `index.html`, `app.js`, `pages.js` and `pages-data.json` must be alongside each other. This layout does not include the development source or tests.

## 3. Enable Pages

1. Open the repository's **Settings** tab.
2. Click **Pages** in the left sidebar.
3. Under **Build and deployment → Source**, select **Deploy from a branch**.
4. Select the **main** branch.
5. Choose **/docs** for the full project, or **/(root)** for the website-only upload.
6. Click **Save**.
7. Wait for the deployment to finish. The Pages settings page will show the published address.

The expected address for this account and repository name is `https://sokeakwalam.github.io/passport-agent/`. This is an expected address, not confirmation that deployment has happened. Confirm the actual URL on GitHub's Pages settings page.

## What changes from PythonAnywhere

- The full questionnaire, document rules and points calculation run in the browser.
- Optional saved progress uses browser storage, separately for this project's URL.
- Saving, returning, deleting, printing, PDF through the browser, and text export work without a back end.
- Visitors' answers are not uploaded to GitHub. GitHub handles normal website request logs.
- Clearing the site's browser data deletes saved progress. Private browsing or blocked storage may prevent saving; checklist generation remains usable.
- Existing PythonAnywhere progress does not migrate automatically, because it is stored on the old server.
- The previous PythonAnywhere app is independent. This preparation does not delete or disable it. Once the GitHub version is verified, disable the old app from PythonAnywhere's Web tab if you no longer want it online.

## Updating the site

Run from the project directory:

```sh
python3 build_pages.py --zip --source-zip
```

This refreshes `docs` and both ZIPs. The builder enumerates every valid questionnaire combination using `rules.py`, then compresses equivalent decisions into a shared decision graph. Content and decisions remain defined in Python rather than being maintained separately in JavaScript.

Commit the updated source and `docs` files to `main`; Pages republishes from the configured folder. The content review date reflects when the guidance was checked, not the date the site was built.

## Verification

```sh
python3 -m unittest discover -s tests -q
```

Node.js is needed only for the Pages runtime test. The test compares the browser runtime with Python across all 16,488 valid answer combinations, and exercises the real UI scripts with DOM stubs for questionnaire → review → checklist → save → reload → resume → delete. This is functional verification, not browser layout testing.

For a local static preview:

```sh
python3 -m http.server 8001 --bind 127.0.0.1 --directory docs
```

Open `http://127.0.0.1:8001`. Use an HTTP server rather than double-clicking `index.html`, because the app loads its rule-data JSON with fetch.

After publication, test all three routes, saved progress, document points, and exports at the actual GitHub Pages URL. The citizenship-content coverage limits in `CONTENT_REVIEW.md` still apply.

Official references: [About GitHub Pages](https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages), [Configure publishing from a branch](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site).
