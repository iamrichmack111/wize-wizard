#!/usr/bin/env python3
import os
import getpass
import re
import json
import time
from pathlib import Path
from urllib.parse import urljoin, urlparse

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

BASE_URL = os.environ.get("WIZARD_QA_URL", "https://wizard.richmackos.com").rstrip("/")
USERNAME = os.environ.get("WIZARD_QA_USER", "admin")
PASSWORD = getpass.getpass("Wizard admin password: ")
print(f"QA password characters entered: {len(PASSWORD)}")

OUT = Path(os.environ.get("WIZARD_QA_OUT", "docs/screenshots/qa"))
OUT.mkdir(parents=True, exist_ok=True)

if not PASSWORD:
    raise SystemExit("No password entered.")

results = []
console_errors = []
page_errors = []
visited = set()

def slugify(text):
    text = re.sub(r"[^a-zA-Z0-9]+", "-", text.strip().lower()).strip("-")
    return text[:80] or "page"

def record(name, status, detail="", screenshot=""):
    results.append({
        "name": name,
        "status": status,
        "detail": detail,
        "screenshot": screenshot,
    })

def page_health(page, label):
    checks = []

    title = page.title().strip()
    checks.append(("title", bool(title), title or "Missing title"))

    body_text = page.locator("body").inner_text().strip()
    checks.append(("body", len(body_text) > 40, f"{len(body_text)} chars"))

    overflow = page.evaluate(
        "() => document.documentElement.scrollWidth > document.documentElement.clientWidth + 2"
    )
    checks.append(("horizontal-overflow", not overflow, "overflow detected" if overflow else "none"))

    visible_h1 = page.locator("h1:visible").count()
    visible_h2 = page.locator("h2:visible").count()
    checks.append(("heading", (visible_h1 + visible_h2) > 0, f"h1={visible_h1}, h2={visible_h2}"))

    # Simple form-label heuristic
    unlabeled = page.evaluate("""() => {
      const fields = [...document.querySelectorAll('input:not([type=hidden]), select, textarea')];
      return fields.filter(el => {
        if (el.getAttribute('aria-label') || el.getAttribute('aria-labelledby')) return false;
        if (el.id && document.querySelector(`label[for="${CSS.escape(el.id)}"]`)) return false;
        if (el.closest('label')) return false;
        return true;
      }).length;
    }""")
    checks.append(("form-labels", unlabeled == 0, f"{unlabeled} potentially unlabeled controls"))

    failures = [f"{k}: {d}" for k, ok, d in checks if not ok]
    return "; ".join(failures) if failures else "Basic UI checks passed"

def screenshot(page, name, full=True):
    path = OUT / f"{name}.png"
    page.screenshot(path=str(path), full_page=full)
    return str(path)

def goto_and_capture(page, url, label, shot_name):
    try:
        resp = page.goto(url, wait_until="networkidle", timeout=30000)
        code = resp.status if resp else 0
        time.sleep(0.4)
        shot = screenshot(page, shot_name)
        detail = page_health(page, label)
        if code >= 400:
            record(label, "FAIL", f"HTTP {code}; {detail}", shot)
        else:
            record(label, "PASS" if "passed" in detail.lower() else "WARN",
                   f"HTTP {code}; {detail}", shot)
        return True
    except Exception as e:
        record(label, "FAIL", repr(e))
        return False

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(
        viewport={"width": 1440, "height": 1000},
        color_scheme="dark",
        ignore_https_errors=False,
    )
    page = context.new_page()

    page.on("console", lambda msg: console_errors.append(
        {"type": msg.type, "text": msg.text, "url": page.url}
    ) if msg.type == "error" else None)
    page.on("pageerror", lambda exc: page_errors.append(
        {"error": str(exc), "url": page.url}
    ))

    # Login page
    try:
        resp = page.goto(BASE_URL, wait_until="networkidle", timeout=30000)
        screenshot(page, "00-login")
        record("Login page", "PASS" if resp and resp.status < 400 else "WARN",
               f"HTTP {resp.status if resp else 'unknown'}")
    except Exception as e:
        screenshot(page, "00-login-failed")
        record("Login page", "FAIL", repr(e))
        browser.close()
        raise SystemExit("Could not reach Wizard. See QA report artifacts.")

    # Resolve username/password controls flexibly.
    user = page.locator(
        'input[name="username"], input[name="user"], input[type="text"]'
    ).first
    pw = page.locator(
        'input[name="password"], input[type="password"]'
    ).first

    if user.count() == 0 or pw.count() == 0:
        record("Authentication", "FAIL", "Could not locate login controls")
    else:
        user.fill(USERNAME)
        pw.fill(PASSWORD)

        # Submit the actual login form directly. This avoids Playwright
        # waiting on a submit-button click while Flask redirects.
        page.locator("form").first.evaluate("(form) => form.submit()")
        page.wait_for_timeout(1500)

        current_url = page.url
        login_form_visible = (
            page.locator('form input[name="username"]:visible').count() > 0
            and page.locator('form input[type="password"]:visible').count() > 0
        )
        on_login_route = "/login" in current_url.lower()

        if login_form_visible or on_login_route:
            body = page.locator("body").inner_text().strip()
            record(
                "Authentication",
                "FAIL",
                f"Still on login page after submit. URL={current_url}. "
                f"Page text: {body[:400]}",
                str(OUT / "01-dashboard.png"),
            )
        else:
            record(
                "Authentication",
                "PASS",
                f"Authenticated successfully. URL={current_url}",
                str(OUT / "01-dashboard.png"),
            )

            # Capture visible navigation destinations without destructive clicks.
            nav_links = page.locator("a[href]")
            candidates = []
            for i in range(nav_links.count()):
                a = nav_links.nth(i)
                href = a.get_attribute("href")
                text = (a.inner_text() or "").strip()
                if not href or href.startswith("#") or href.startswith("javascript:"):
                    continue
                url = urljoin(BASE_URL + "/", href)
                parsed = urlparse(url)
                if parsed.netloc != urlparse(BASE_URL).netloc:
                    continue
                if any(x in parsed.path.lower() for x in ["/logout", "/delete", "/remove"]):
                    continue
                key = (url.split("#")[0], text)
                if key not in candidates:
                    candidates.append(key)

            # Prioritize app areas likely useful for README/wiki.
            priorities = [
                "dashboard", "strategy", "why", "pert", "communication",
                "lesson", "course", "market", "finance", "risk",
                "monte", "handbook", "report", "admin", "user"
            ]

            def priority(item):
                url, text = item
                hay = (url + " " + text).lower()
                for idx, word in enumerate(priorities):
                    if word in hay:
                        return idx
                return 999

            candidates.sort(key=priority)

            seen_urls = set()
            capture_index = 2
            for url, text in candidates:
                clean = url.split("#")[0]
                if clean in seen_urls:
                    continue
                seen_urls.add(clean)
                label = text or urlparse(clean).path or "Page"

                # D2 source files are downloads, not renderable HTML pages.
                # Validate them through the authenticated HTTP context instead
                # of page.goto(), which raises "Download is starting".
                if urlparse(clean).path.lower().endswith(".d2"):
                    try:
                        response = context.request.get(clean)
                        body = response.body()

                        if response.ok and body:
                            record(
                                label,
                                "PASS",
                                f"HTTP {response.status}; D2 source accessible"
                            )
                        else:
                            record(
                                label,
                                "FAIL",
                                f"HTTP {response.status}; D2 source unavailable or empty"
                            )
                    except Exception as e:
                        record(label, "FAIL", repr(e))

                    continue

                shot_name = f"{capture_index:02d}-{slugify(label)}"
                goto_and_capture(page, clean, label, shot_name)
                capture_index += 1

                # Bound the run so README screenshots don't explode in count.
                if capture_index > 22:
                    break

            # Mobile smoke pass on dashboard/current authenticated landing page.
            mobile = context.new_page()
            mobile.set_viewport_size({"width": 390, "height": 844})
            try:
                mobile.goto(BASE_URL, wait_until="networkidle", timeout=30000)
                shot = screenshot(mobile, "90-mobile-home")
                overflow = mobile.evaluate(
                    "() => document.documentElement.scrollWidth > document.documentElement.clientWidth + 2"
                )
                record("Mobile layout", "WARN" if overflow else "PASS",
                       "Horizontal overflow detected" if overflow else "No page-level horizontal overflow",
                       shot)
            except Exception as e:
                record("Mobile layout", "FAIL", repr(e))
            mobile.close()

    browser.close()

# Console/page errors
for err in console_errors:
    record("Browser console", "WARN", f'{err["url"]}: {err["text"]}')
for err in page_errors:
    record("Page JavaScript", "FAIL", f'{err["url"]}: {err["error"]}')

# Markdown report
report = OUT / "QA_REPORT.md"
passed = sum(r["status"] == "PASS" for r in results)
warned = sum(r["status"] == "WARN" for r in results)
failed = sum(r["status"] == "FAIL" for r in results)

lines = [
    "# Wize Wizard Playwright QA Report",
    "",
    f"- URL: `{BASE_URL}`",
    f"- Passed: **{passed}**",
    f"- Warnings: **{warned}**",
    f"- Failed: **{failed}**",
    "",
    "## Results",
    "",
    "| Check/Page | Status | Detail | Screenshot |",
    "|---|---|---|---|",
]

for r in results:
    shot = ""
    if r["screenshot"]:
        try:
            rel = Path(r["screenshot"]).relative_to(OUT)
            shot = f"[View]({rel.as_posix()})"
        except Exception:
            shot = r["screenshot"]
    detail = r["detail"].replace("|", "\\|").replace("\n", " ")
    lines.append(f'| {r["name"]} | **{r["status"]}** | {detail} | {shot} |')

lines += [
    "",
    "## README / Wiki Screenshot Candidates",
    "",
    "Use the clearest screenshots from this directory for:",
    "",
    "- Login / branding",
    "- Dashboard / guided workflow",
    "- Five Strategic Questions and connected Whys",
    "- PERT / Stress Analysis",
    "- Communications / Management structure",
    "- Strategy Handbook / course",
    "- Market / Finance / Risk interactive labs",
    "- Final Project Plan / report",
    "- Admin / user management",
    "",
    "## Notes",
    "",
    "- This run is intentionally read-only apart from authentication.",
    "- It does not create/delete users or mutate project data.",
    "- Warnings should be reviewed manually before publishing screenshots.",
]
report.write_text("\n".join(lines), encoding="utf-8")

json_path = OUT / "qa-results.json"
json_path.write_text(json.dumps(results, indent=2), encoding="utf-8")

print(f"QA complete: {passed} PASS, {warned} WARN, {failed} FAIL")
print(f"Report: {report}")
print(f"Screenshots: {OUT}")
