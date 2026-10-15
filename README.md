# Password Security Center

An educational cybersecurity web application built with Flask. It **analyzes password strength** (length, character diversity, predictable patterns, common-password usage and estimated entropy) and **generates cryptographically secure passwords** with Python's `secrets` module.

The project is designed as a capstone and portfolio piece. It demonstrates secure software development, password-security concepts, a modular Flask architecture and automated testing.

> **Privacy notice:** Passwords entered into this tool are analyzed for the current request and are not intentionally stored by the application. Do not enter real passwords that you currently use for important accounts into demonstration systems.

---

## Features

### Password Strength Checker (`/checker`)
- Real-time feedback while typing. Instant character checks run in the browser, and a debounced server call returns the authoritative analysis.
- Strength meter (Very Weak → Very Strong) with a 0–100 score, a text label and an icon, so it never relies on color alone.
- **Estimated entropy** (`length × log2(pool)`) plus a **pattern-adjusted entropy** that discounts predictable parts.
- Detection of:
  - common passwords (exact, and variants with capitals, substitutions or added digits/symbols)
  - sequential numbers (`1234`, `9876`) and letters (`abcdef`, `xyz`)
  - repeated characters (`aaaa`, `!!!!`) and repeated chunks (`ababab`, `123123`)
  - keyboard walks (`qwerty`, `asdfgh`, `zxcvbn`, `1qaz2wsx`)
  - common words embedded anywhere, and leetspeak substitutions (`p@ssw0rd`)
  - years and long digit runs (likely dates or phone numbers)
- "Why this password received this rating" explanation, plus specific recommendations.
- Visibility toggle, Analyze and Clear buttons, and a personal-information warning.

### Secure Password Generator (`/generator`)
- Length from 8 to 128 (default 20), set with a slider, a number input or presets (8, 10, 12, 14, 16, 20, 24, 32).
- Lowercase, uppercase, number and special-character sets, plus an option to exclude ambiguous characters (`0 O 1 l I | ` ' "`).
- Every selected category is guaranteed to appear. The result is shuffled with a CSPRNG.
- Live character-pool size and number of possible combinations.
- Copy (Clipboard API with fallback), Generate New, a visibility toggle, and character count, entropy and strength for each password.

### Other pages
- `/`: landing page with feature cards and six security essentials.
- `/about`: educational content on strength, length, entropy, patterns, reuse, password managers and MFA, plus the scoring methodology, privacy design and limitations.
- Custom 404 page and friendly 400/405/413/429/500 pages. API routes return JSON errors instead.

---

## Technology stack

| Layer    | Technology |
|----------|------------|
| Backend  | Python 3.11+, Flask 3, Flask-WTF (CSRF), python-dotenv |
| Security | `secrets`, CSRF tokens, CSP and security headers, rate limiting |
| Frontend | HTML5, CSS3 (custom properties), vanilla JavaScript (no framework, no build step) |
| Testing  | pytest |

---

## Architecture

```text
.
├── run.py                     # Development entry point
├── config.py                  # Environment-based configuration classes
├── requirements.txt
├── pytest.ini
├── .env.example               # Safe placeholder settings (copy to .env)
├── app/
│   ├── __init__.py            # create_app() application factory
│   ├── extensions.py          # CSRFProtect instance
│   ├── security.py            # Security headers / CSP (after_request)
│   ├── errors.py              # HTML + JSON error handlers
│   ├── routes/                # Blueprints (thin: validate → call service → respond)
│   │   ├── main.py            #   /  /about
│   │   ├── checker.py         #   /checker  POST /api/check-password
│   │   └── generator.py       #   /generator  POST /api/generate-password
│   ├── services/              # Framework-independent security logic
│   │   ├── password_checker.py    # analyze_password(): scoring & feedback
│   │   ├── entropy.py             # pool size, entropy, pattern-adjusted entropy
│   │   ├── pattern_detector.py    # sequences, repeats, keyboard, words, dates
│   │   ├── common_passwords.py    # local common-password lookup
│   │   └── password_generator.py  # secrets-based generator
│   ├── utils/
│   │   ├── validators.py      # JSON payload validation
│   │   ├── api.py             # Consistent JSON success/error envelopes
│   │   └── rate_limit.py      # In-memory sliding-window rate limiter
│   ├── data/common_passwords.txt  # Demonstration list (extendable)
│   ├── templates/             # Jinja2 templates (+ partials/)
│   └── static/                # css/style.css, js/{main,checker,generator}.js, img/
└── tests/                     # pytest suite
```

Requests flow in one direction: **route → service → specialized helper**. The services have no Flask dependency, so they can be used on their own:

```python
from app.services.password_checker import analyze_password
from app.services.password_generator import generate_password

result = analyze_password("P@ssword123!")
print(result["strength"], result["score"])   # Weak 22

password = generate_password(24, exclude_ambiguous=True)
```

---

## Installation

Requires **Python 3.11 or newer**.

```bash
python -m venv venv
```

Activate the virtual environment:

```bash
# Windows
venv\Scripts\activate

# Linux / macOS
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Optional: create a `.env` file from the template and set a secret key:

```bash
cp .env.example .env          # Windows: copy .env.example .env
python -c "import secrets; print(secrets.token_hex(32))"   # paste into SECRET_KEY
```

## Running the application

```bash
python run.py
```

Open <http://127.0.0.1:5000>.

`FLASK_ENV` defaults to `development`, which enables Flask's debug mode. **Never use debug mode or the built-in development server in production.** The interactive debugger allows arbitrary code execution. For deployment, set `FLASK_ENV=production`, set a strong `SECRET_KEY` (the app refuses to start without one), serve over HTTPS, and use a WSGI server, for example:

```bash
pip install waitress
waitress-serve --host 0.0.0.0 --port 8000 --call app:create_app
```

## Running the tests

```bash
pytest
```

The suite covers entropy, character detection, common passwords, every pattern detector, scoring and recommendations, generator validation and randomness, all routes and API endpoints, error handling, CSRF, rate limiting, security headers, and static checks for password leakage.

---

## API

All endpoints accept and return JSON, require `POST`, and need a CSRF token in the `X-CSRFToken` header (the pages provide it in `<meta name="csrf-token">`).

### `POST /api/check-password`

```json
{ "password": "example" }
```

Response `200`:

```json
{
  "success": true,
  "result": {
    "score": 22,
    "strength": "Weak",
    "strength_level": 1,
    "entropy": 78.8,
    "adjusted_entropy": 16.5,
    "length": 12,
    "length_rating": "moderate",
    "character_types": { "lowercase": true, "uppercase": true, "numbers": true, "special": true },
    "character_pool": 95,
    "common_password": true,
    "common_password_match": "variant",
    "patterns": [
      { "type": "sequential_numbers", "label": "Sequential numbers", "message": "...", "severity": "medium", "count": 1 }
    ],
    "strengths": ["..."],
    "weaknesses": ["..."],
    "recommendations": ["..."]
  }
}
```

The response never contains the password or any fragment of it. Pattern findings describe the *type* of pattern, not the matched text.

### `POST /api/generate-password`

```json
{ "length": 20, "lowercase": true, "uppercase": true, "numbers": true, "special": true, "exclude_ambiguous": false }
```

All fields are optional (defaults as shown). Response `200`:

```json
{ "success": true, "password": "…", "length": 20, "pool_size": 89, "entropy": 129.5,
  "strength": "Very Strong", "strength_level": 4, "score": 100 }
```

### Errors

```json
{ "success": false, "error": { "code": "INVALID_INPUT", "message": "Password must be provided." } }
```

| Status | Codes |
|--------|-------|
| 400 | `INVALID_INPUT`, `INVALID_JSON`, `CSRF_FAILED` |
| 404 | `NOT_FOUND` |
| 405 | `METHOD_NOT_ALLOWED` |
| 413 | `PAYLOAD_TOO_LARGE` (body > 16 KiB) |
| 429 | `RATE_LIMITED` (with `Retry-After`) |
| 500 | `SERVER_ERROR` (no internal details are exposed) |

---

## Security architecture

| Control | Implementation |
|---------|----------------|
| Secure randomness | `secrets.choice()` and a Fisher–Yates shuffle driven by `secrets.randbelow()`. The `random` module is never used, and a test enforces this. |
| No password storage | Passwords exist only in memory for the duration of a request. There is no database, the session holds only the CSRF token, and nothing is written to disk. |
| No password logging | There are no `print` calls. The only log call records the method and path of unhandled exceptions. Tests check the logs and scan the source. |
| No passwords in URLs | Passwords travel only in POST bodies. The APIs reject GET, and every form uses `method="post"`, so even a no-JavaScript submission cannot put a password in the query string. |
| No browser storage | The scripts never touch web storage, cookies or IndexedDB (enforced by a test). Password fields are cleared on `pagehide`, and inputs use `autocomplete="off"`. |
| CSRF | Flask-WTF `CSRFProtect` protects every POST. The JavaScript sends the token in a header. |
| Input validation | JSON object required. Type, emptiness and length checks for the password (max 256). Integer and boolean checks for generator options. The service layer re-validates ranges. |
| Request size | `MAX_CONTENT_LENGTH` = 16 KiB. |
| Rate limiting | Sliding window per client IP and endpoint (default 120 requests/minute). |
| Security headers | `Content-Security-Policy` (self only, no inline scripts or styles, `frame-ancestors 'none'`), `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy: strict-origin-when-cross-origin`, `Permissions-Policy`, COOP/CORP, HSTS when secure cookies are enabled, and `Cache-Control: no-store` on pages and API responses. |
| Cookies | `HttpOnly`, `SameSite=Strict`, `Secure` in production. |
| Error handling | Custom handlers for 400/404/405/413/429/500. No tracebacks, paths or secrets in responses. Production refuses to start without `SECRET_KEY`. |
| Safe DOM updates | All dynamic text is inserted with `textContent` / DOM nodes, never `innerHTML`. |
| No third parties | Common-password matching is local. No external API, CDN, font or analytics requests. |

---

## Password-analysis methodology

1. **Character categories:** lowercase (26), uppercase (26), digits (10) and special characters (33: ASCII punctuation plus space). Non-ASCII characters add a conservative 100 to the pool.
2. **Length rating:** under 8 is critical, 8–11 weak, 12–15 moderate, 16–19 strong, 20+ excellent.
3. **Common passwords:** a case-insensitive match against `app/data/common_passwords.txt`. It also matches after reversing leetspeak and after stripping leading or trailing digits and symbols (`!Password123` → `password`).
4. **Pattern detection:** each detector records where a pattern occurs and roughly how many guesses it would take to enumerate it (for example, a word's rank in the list, or start × direction × length for a sequence).
5. **Scoring (0–100):**
   - Base points: up to **30** for length (1.5/char), **0/5/10/15** for 1/2/3/4 categories, and up to **55** for pattern-adjusted entropy (0.55/bit).
   - Penalties: **15/10/5** per distinct high/medium/low-severity pattern type, up to 40.
   - Caps: exact common password ≤ 5; variant of a common password ≤ 25; under 8 characters ≤ 20; 8–11 characters ≤ 55; 60% or more of the characters in patterns ≤ 40.
   - Bands: 0–20 Very Weak, 21–40 Weak, 41–60 Moderate, 61–80 Strong, 81–100 Very Strong.

   Because the caps are applied last and the entropy points use the pattern-adjusted estimate, adding character types cannot mask a predictable password. `P@ssword123!` uses all four categories but rates **Weak**.

The analysis is deterministic: the same input and dataset always produce the same result.

## Entropy methodology

- **Estimated (theoretical) entropy** = `length × log2(pool_size)`. This is an upper bound that assumes each character is chosen uniformly at random.
- **Pattern-adjusted entropy** uses dynamic programming to find the cheapest way to "explain" the password. Each character costs either `log2(pool)` bits as a random character, or it belongs to a detected pattern segment costing `log2(guesses)` bits. The idea is similar to (but much simpler than) zxcvbn.
- Both values are estimates. Neither is a crack-time prediction, which depends on the hash algorithm, attacker hardware and strategy.

## Generator methodology

1. Validate the length (integer, 8–128) and require at least one character category.
2. Build the pool from the selected sets, optionally removing ambiguous characters.
3. Pick one character from each selected set with `secrets.choice()`, which guarantees every category appears.
4. Fill the remaining positions with `secrets.choice(pool)`.
5. Shuffle with a Fisher–Yates shuffle using `secrets.randbelow()`.
6. Report entropy as `length × log2(pool_size)`. The guaranteed-inclusion step removes a negligible fraction of the space, so this is a close upper bound.

---

## Limitations

- Strength estimation is **heuristic** and cannot guarantee real-world security.
- The bundled common-password list is small (about 200 entries). Real attackers use billions of leaked passwords.
- The checker cannot tell whether a password has appeared in a breach or is reused elsewhere.
- It cannot recognize personal information (your name, pet, hometown).
- Pattern detection targets common English and QWERTY/AZERTY/QWERTZ patterns. It misses interleaved sequences (`a1b2c3`), non-English words and many other structures.
- The rate limiter is in-memory and per-process. Multi-worker deployments should use a shared store (for example Redis) or rate-limit at the reverse proxy.
- Passwords are sent to the server for analysis. This is local to your deployment, but you should still serve over HTTPS outside localhost.

## Future improvements

- Optional k-anonymity breach check (Have I Been Pwned range API), opt-in only.
- A larger, frequency-ranked dictionary with names and multilingual word lists.
- Detection of interleaved sequences, dates in more formats, and l33t combinations.
- A passphrase generator (diceware-style word lists).
- Redis-backed rate limiting and a production Docker image.
- Localization and a light theme.
