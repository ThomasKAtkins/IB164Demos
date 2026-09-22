# Publishing the IB164 demos to GitHub Pages

A one-time setup. After this, republishing is a double-click on
`update_site.bat`.

Everything below is written for **this machine** and the GitHub account
**ThomasKAtkins**. Commands run in **Git Bash** (Start menu → "Git Bash"),
opened in `C:\Users\thoma\Documents\Teaching\IB164`. A quick way to get there:
open the folder in File Explorer, right-click empty space, choose
**Open Git Bash here**.

Total time: about 10 minutes, most of it waiting for the upload.

---

## Before you start

You need a GitHub account. If you are not sure you are signed in, open
<https://github.com> and check for your avatar at the top right.

---

## Step 1 — Create the repository on GitHub

Do this first, in the browser, so the upload in step 5 has somewhere to go.

1. Go to <https://github.com/new>
2. **Repository name:** `IB164`
3. **Public** — required for GitHub Pages on a free account. (Private repos can
   only use Pages on a paid plan.)
4. Leave **"Add a README file"**, `.gitignore` and licence **unticked**. The
   folder already has a README, and adding one here causes a conflict on the
   first push.
5. Click **Create repository**.

You will land on a page showing setup instructions. Ignore them — the steps
below are tailored to this folder.

> **Public repository — what that means here.** Anyone can see the notebooks,
> the built site and the README. That is fine for teaching demos. It does *not*
> publish the lab 3 GWAS data: those files are excluded by `.gitignore` and
> stay on your machine. Do not add student names, marks or unpublished material
> to this folder.

---

## Step 2 — Get an access token (for the upload in step 5)

GitHub stopped accepting account passwords from git in 2021. This machine has
no credential helper set up, so git will ask for a username and password, and
the "password" must be a **Personal Access Token**.

Get one now so step 5 does not stall:

1. Go to <https://github.com/settings/tokens?type=beta>
2. **Generate new token**
3. **Token name:** `IB164 publishing`
4. **Expiration:** 90 days is sensible. Set a calendar reminder; when it
   expires, repeat this step and use the new token.
5. **Repository access:** *Only select repositories* → pick **IB164**
6. **Permissions** → *Repository permissions* → find **Contents** and set it to
   **Read and write**. This is the only permission needed.
7. **Generate token**, then **copy it**. It is shown once and never again.
8. Paste it somewhere safe for the next few minutes — Notepad is fine, but
   delete it afterwards, or store it in a password manager.

The token is a password. Do not put it in a file inside this folder, or it will
be published.

---

## Step 3 — Build the site

In Git Bash, in the IB164 folder:

```bash
py -3.10 build_site.py
```

Expected output, ending with:

```
docs/ built: 26.3 MB
```

If it reports an error about `docs/` being in use, close any
`preview_site.bat` window and any Explorer window inside `docs\`, then run it
again.

---

## Step 4 — Create the local repository and commit

Run these one at a time:

```bash
git init -b main
git add -A
```

**Now check what is staged, before committing.** This is the important safety
check — lab 3 holds 8.8 GB of GWAS data and its largest file is 2.3 GB, over
20x GitHub's 100 MB hard limit:

```bash
git status --short | wc -l
```

Expect **717** (or close to it; a couple either way is fine).

```bash
git diff --cached --name-only | grep -E "\.tsv\.bgz|_app/" || echo "CLEAN"
```

Expect it to print **`CLEAN`**. If it lists any files instead, **stop** and
tell me — do not commit. Something is wrong with `.gitignore`.

Then commit:

```bash
git commit -m "Publish IB164 interactive lab demos"
```

Check the size is sane before uploading:

```bash
git count-objects -vH
```

Look at `size-pack:`. Expect roughly **20–30 MiB**. If it says hundreds of MiB
or any GiB, stop and tell me.

---

## Step 5 — Upload to GitHub

```bash
git remote add origin https://github.com/ThomasKAtkins/IB164.git
git push -u origin main
```

A window or prompt will ask for credentials:

- **Username:** `ThomasKAtkins`
- **Password:** paste the **token** from step 2 (not your GitHub password)

The upload is about 26 MB and takes anywhere from a few seconds to a couple of
minutes. It finishes with a line mentioning `main -> main`.

If nothing is asked and it fails immediately with an authentication error, run
this once and try the push again — it makes Windows remember the token:

```bash
git config --global credential.helper wincred
```

---

## Step 6 — Turn on GitHub Pages

Back in the browser:

1. Go to <https://github.com/ThomasKAtkins/IB164/settings/pages>
2. Under **Build and deployment** → **Source**, choose **Deploy from a branch**
3. Two dropdowns appear. Set them to:
   - **Branch:** `main`
   - **Folder:** `/docs`  ← *not* `/ (root)`
4. Click **Save**

Getting the folder wrong is the most common mistake. If you pick `/ (root)`,
the site shows the README instead of the demos.

---

## Step 7 — Check it works

Pages takes 1–3 minutes to build the first time. Then open:

**<https://thomaskatkins.github.io/IB164/>**

You should see the landing page with Lab 4, Lab 2 and Lab 1 as collapsed
sections. Click a lab to open it, then a demo.

Check these:

- [ ] Landing page loads and the labs expand when clicked
- [ ] A lab 4 demo opens and the images appear
- [ ] A lab 1 demo opens (slower — it loads scipy)
- [ ] It works on your phone, off wi-fi, on mobile data

That last one matters: your own laptop has a warm cache and can hide a slow
first load. A phone on mobile data is the closest thing to a student's
experience.

If you get a 404, wait another two minutes and refresh. If it persists, check
the Folder setting in step 6 really says `/docs`.

---

## Step 8 — Give the link to students

**<https://thomaskatkins.github.io/IB164/>**

Worth saying alongside it:

> Nothing to install. The first demo takes 10–30 seconds to start while it
> loads Python in the background — this is normal. You need to be online, and
> to use a current Chrome, Edge, Firefox or Safari.

The landing page says all of this too, but students who are told in advance are
much less likely to think it is broken.

---

## Afterwards: making a change

1. Edit the notebook:
   `py -3.10 -m marimo edit lab4/peppered_moth.py`
2. Re-export it:
   `py -3.10 -m marimo export html-wasm lab4/peppered_moth.py -o lab4/_peppered_moth_app --mode run`
3. Preview: double-click **`preview_site.bat`**
4. Publish: double-click **`update_site.bat`**

The change is live within about a minute. Students may need one refresh.

To add or remove a demo from the site, edit the `LABS` list at the top of
`build_site.py` — see `README.md`.

---

## If something goes wrong

**`git: command not found`** — you are in the wrong terminal. Use Git Bash, not
PowerShell or Command Prompt.

**`remote origin already exists`** — the remote was added before. Check it with
`git remote -v`; if the URL is right, skip straight to `git push -u origin main`.

**`failed to push some refs` / `fetch first`** — the GitHub repo is not empty,
usually because a README was added in step 1. Simplest fix: delete the repo
(Settings → scroll to the bottom → Delete this repository) and redo step 1 with
everything unticked.

**`Authentication failed`** — the token was mistyped, has expired, or lacks
*Contents: Read and write*. Generate a fresh one (step 2) and try again.

**`support for password authentication was removed`** — you entered your
account password. Use the token instead.

**Site shows the README, not the demos** — the Pages folder is set to
`/ (root)`. Change it to `/docs` (step 6).

**A demo hangs on a spinner** — almost always the network. It needs to reach
`cdn.jsdelivr.net` to download Python. Some institutional networks block CDNs;
test on mobile data to tell the difference.

**Pushed something by accident** — tell me before pushing anything else.
Removing a file from GitHub's history is fiddly but much easier if caught
early.
