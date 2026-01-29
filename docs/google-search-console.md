# Google Search Console / Indexing Guide

Quick steps to get `ricai.com` indexed by Google:

1. Verify ownership
   - Go to https://search.google.com/search-console
   - Add a property (use the Domain type for broad coverage or URL prefix for single host)
   - Follow the verification steps (DNS TXT record is recommended for Domain property)

2. Submit a sitemap
   - In Search Console, open your property → Sitemaps
   - Enter `https://ricai.com/sitemap.xml` and submit

3. Inspect URLs
   - Use URL Inspection to check whether specific pages are indexed and request indexing if needed


## Automated verification helpers (optional)
You can make Search Console verification easier by letting the webapp serve the required verification file or inject the meta tag automatically.

- Serve verification file from root
  - Set env var `GOOGLE_SITE_VERIFICATION_FILENAME` to the filename provided by Google (e.g. `google123456.html`).
  - Optionally set `GOOGLE_SITE_VERIFICATION_FILE_CONTENT` to the exact content Google expects. If not set the app will serve the filename as plain text.
  - Example (bash):
    ```bash
    export GOOGLE_SITE_VERIFICATION_FILENAME="google1234567890abcdef.html"
    export GOOGLE_SITE_VERIFICATION_FILE_CONTENT="google-site-verification: google1234567890abcdef.html"
    ```

- Inject meta tag into the HTML index
  - Set env var `GOOGLE_SITE_VERIFICATION_META` to the verification token (the content value of the meta tag).
  - Example (bash):
    ```bash
    export GOOGLE_SITE_VERIFICATION_META="abcdef123456"
    ```

After setting environment variables, restart the webapp and then click "Verify" in Search Console. The app will serve the file at `https://ricai.com/<filename>` or the index will include the meta tag automatically.

4. Check robots
   - Visit `https://ricai.com/robots.txt` to ensure it allows crawling and references the sitemap.
   - Ensure meta robots tags on pages do not contain `noindex`.

5. Monitor
   - Use the Coverage report in Search Console to see which URLs are indexed and any crawl/indexing errors.

Tips
- Ensure TLS/HTTPS works and the sitemap is reachable.
- Avoid blocking resources required for rendering (CSS/JS) in `robots.txt`.
- If your site is new, indexing may take time; submitting the sitemap and using URL Inspection speeds it up.