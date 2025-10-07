import os
import time
import json
import logging
from typing import Optional
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.by import By


def _get_env_flag(name: str, default: str = "0") -> bool:
    return os.environ.get(name, default) in ("1", "true", "True", "yes")


def _post_2captcha(
    api_key: str,
    site_key: str,
    page_url: str,
    *,
    version: str = "v2",
    action: Optional[str] = None,
    min_score: Optional[float] = None,
    enterprise: bool = False,
    proxy: Optional[str] = None,
) -> Optional[str]:
    import requests

    payload = {"key": api_key, "method": "userrecaptcha", "googlekey": site_key, "pageurl": page_url, "json": 1}
    if version.lower() == "v3":
        payload["version"] = "v3"
        if action:
            payload["action"] = action
        if min_score is not None:
            payload["min_score"] = min_score
    if enterprise:
        payload["enterprise"] = 1
    if proxy:
        payload["proxy"] = proxy

    r = requests.post("https://2captcha.com/in.php", data=payload, timeout=30)
    r.raise_for_status()
    data = r.json()
    if data.get("status") == 1:
        return data.get("request")
    logging.warning(f"2Captcha create task failed: {json.dumps(data)}")
    return None


def _fetch_2captcha_result(api_key: str, request_id: str, max_wait_sec: int = 120, poll_interval: int = 5) -> Optional[str]:
    import requests

    elapsed = 0
    while elapsed < max_wait_sec:
        time.sleep(poll_interval)
        elapsed += poll_interval
        params = {"key": api_key, "action": "get", "id": request_id, "json": 1}
        r = requests.get("https://2captcha.com/res.php", params=params, timeout=30)
        r.raise_for_status()
        data = r.json()
        if data.get("status") == 1:
            return data.get("request")
        if data.get("request") != "CAPCHA_NOT_READY":
            logging.warning(f"2Captcha polling error: {json.dumps(data)}")
            return None
    logging.warning("2Captcha result timeout")
    return None


def _set_recaptcha_token(driver: WebDriver, token: str) -> None:
    # Common pattern: set g-recaptcha-response in textarea and dispatch input event
    driver.execute_script(
        """
        const token = arguments[0];
        const areas = document.querySelectorAll('textarea[g-recaptcha-response], #g-recaptcha-response');
        for (const a of areas) {
          a.style.display = 'block';
          a.value = token;
          a.dispatchEvent(new Event('input', { bubbles: true }));
          a.dispatchEvent(new Event('change', { bubbles: true }));
        }
        // Call grecaptcha if available
        if (window.grecaptcha && window.grecaptcha.getResponse) {
          try { window.___lastGreResp = window.grecaptcha.getResponse(); } catch(e) {}
        }
        """,
        token,
    )


def _detect_site_key(driver: WebDriver) -> Optional[str]:
    # Try common selectors for reCAPTCHA widgets
    try:
        # v2 explicit sitekey
        el = driver.find_element(By.CSS_SELECTOR, "div.g-recaptcha")
        sitekey = el.get_attribute("data-sitekey")
        if sitekey:
            return sitekey
    except Exception:
        pass

    try:
        # invisible v2
        el = driver.find_element(By.CSS_SELECTOR, "div.grecaptcha-badge, div.g-recaptcha")
        sitekey = el.get_attribute("data-sitekey")
        if sitekey:
            return sitekey
    except Exception:
        pass

    # Look for grecaptcha script with render parameter (can expose sitekey)
    try:
        scripts = driver.find_elements(By.CSS_SELECTOR, 'script[src*="/recaptcha/"]')
        for s in scripts:
            src = s.get_attribute("src") or ""
            # e.g., https://www.google.com/recaptcha/api.js?render=SITE_KEY
            if "render=" in src:
                try:
                    return src.split("render=")[-1].split("&")[0]
                except Exception:
                    pass
    except Exception:
        pass

    # Best-effort: read from JS if present
    try:
        return driver.execute_script("return (window.__SITE_KEY__ || window.sitekey || null);")
    except Exception:
        return None


def try_solve_recaptcha_if_present(driver: WebDriver) -> bool:
    if not _get_env_flag("ENABLE_RECAPTCHA_SOLVER", "0"):
        return False

    api_key = os.environ.get("RECAPTCHA_API_KEY")
    if not api_key:
        logging.info("reCAPTCHA solver enabled but RECAPTCHA_API_KEY is missing")
        return False

    site_key = _detect_site_key(driver)
    if not site_key:
        return False

    page_url = driver.current_url
    enterprise = _get_env_flag("RECAPTCHA_ENTERPRISE", "0")
    proxy = os.environ.get("RECAPTCHA_PROXY")
    version = os.environ.get("RECAPTCHA_VERSION", "v2").lower()
    action = os.environ.get("RECAPTCHA_ACTION")
    min_score_str = os.environ.get("RECAPTCHA_MIN_SCORE")
    min_score = None
    try:
        if min_score_str is not None:
            min_score = float(min_score_str)
    except Exception:
        logging.warning("Invalid RECAPTCHA_MIN_SCORE; ignoring")

    logging.info("Submitting reCAPTCHA to 2Captcha")
    req_id = _post_2captcha(
        api_key,
        site_key,
        page_url,
        version=version,
        action=action,
        min_score=min_score,
        enterprise=enterprise,
        proxy=proxy,
    )
    if not req_id:
        return False

    logging.info("Polling 2Captcha for solution")
    token = _fetch_2captcha_result(api_key, req_id)
    if not token:
        return False

    _set_recaptcha_token(driver, token)
    logging.info("reCAPTCHA token injected")
    return True


