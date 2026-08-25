# GitHub release checklist — v3.0.0

Before pushing:

```powershell
cd backend
python scripts\verify.py
python scripts\preflight.py
```

Confirm that none of these are tracked:

- `.env`
- `credentials.json`
- `token.json`
- `dev.db`
- `.venv/`
- runtime logs / caches

Recommended release tag after local + Docker acceptance:

```text
v3.0.0
```

Suggested repository description:

> Review-first AI e-commerce operations system connecting Gmail, Shopify, deterministic policies and human approval with explainable decision traces.

Use Demo Mode screenshots in the public README. Never publish real customer messages, OAuth files or live merchant secrets.

## Suggested Git sequence

```powershell
git init
git add .
git status
git commit -m "Release AI Ops v3.0.0"
git branch -M main
```

Then add the GitHub remote created for the repository and push. Run `git status` and inspect the staged files before the first push.

## Source licensing

This portfolio repository intentionally has no open-source license. Keep `NOTICE.md` and do not add MIT unless you intentionally want to permit broad reuse, modification, redistribution and commercial use.

## Before making the repository public

- Capture 3–5 screenshots from **Demo Mode only** (Overview, Inbox, Case Workspace, Automation Lab, Arabic RTL).
- Do not use screenshots that contain real Gmail addresses, message text, order/customer data, OAuth identifiers, or live store details.
- Use a concise repository name such as `ai-ecommerce-ops`.
- Add GitHub topics such as `fastapi`, `shopify`, `gmail-api`, `docker`, `celery`, `redis`, `postgresql`, `ai-engineering`, `human-in-the-loop`.

## After the first push

In GitHub repository settings, enable the security features available for the account/repository:

- Dependabot alerts and security updates
- secret scanning / push protection where available
- code scanning (the repository already contains a CodeQL workflow)
- private vulnerability reporting if you want a security-contact channel

Check the **Actions** tab and do not consider the release finished until CI and CodeQL complete successfully.
