import requests
import re
from playwright.sync_api import sync_playwright

phone = 966581915915
base_url = "https://devlos.awn-sa.com"
ad = "ee229694-9a70-35da-ab0c-198fce6fe639"

# Step 1: Login API
login_url = f"{base_url}/api/customer/login"
login_payload = {
    "nid": "1077067922",
    "pin": "159632"
}
login_headers = {
    "deviceid": "1222"
}

resp = requests.post(login_url, data=login_payload, headers=login_headers)
resp.raise_for_status()

login_data = resp.json()
if not login_data.get("success"):
    raise Exception(f"Login failed: {login_data.get('message')}")

user = login_data["data"]["user"]
user_id = user["user_id"]
name = user["name"]
print(f"✅ Login Success. User ID: {user_id}, Name: {name}")

# Loan Application API
loan_url = f"{base_url}/api/loan-application"
loan_payload = {
    "product_id": 1,
    "user_id": user_id,
    "amount": 1500,
    "duration": 3,
    "accountId": ad,
    "purpose_of_finance_id": 1,
}

# Step Order Before Pause
steps_before_pause = ["finance", "verification", "simmah_consent", "counter"]

loan_id = None
for step in steps_before_pause:
    loan_payload["step"] = step
    resp = requests.post(loan_url, data=loan_payload)
    resp.raise_for_status()
    data = resp.json()

    if step == "finance":
        loan_application = data["data"]["loan_application"]
        loan_id = loan_application["id"]
        loan_number = loan_application["loan_application_number"]
        print(f"✅ Step {step} -> Loan Created. ID: {loan_id}, Number: {loan_number}")
    else:
        print(f"✅ Step {step} -> {data.get('message')}")

# Step: e-Promissory
epromissory_url = f"{base_url}/api/e-promissory"
params = {
    "lang": "ar",
    "loan_application_id": loan_id
}
resp = requests.get(epromissory_url, params=params)
resp.raise_for_status()
eprom_data = resp.json()
print("✅ e-Promissory Response:", eprom_data)

# --- Instead of pressing "q", ask for myId here ---
my_id = input("🔑 Enter myId from e-promissory (or paste manually): ")

# --- Playwright Flow (headless, no inspector) ---
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)  # ✅ headless
    page = browser.new_page()

    url = f"https://sandbox.nafith.sa/sanad/{my_id}"
    print(f"🌐 Opening {url}")
    page.goto(url)

    # Remove disabled from input
    page.evaluate("document.getElementById('inputOtp').removeAttribute('disabled')")

    # Fill OTP
    page.fill('#inputOtp', '111111')
    page.press('#inputOtp', 'Enter')

    # Click through the flow
    page.get_by_role("button", name="تأكيد الرمز").click()
    page.get_by_role("button", name="Search").click()
    page.get_by_role("button", name="متابعة 㰏").click()
    page.get_by_role("checkbox").first.check()
    page.locator('#id_hide_packages_reminder').get_by_role("checkbox").check()
    page.get_by_role("button", name="موافقة").click()

    print("✅ Playwright site flow done (headless)")
    browser.close()

# Continue API flow after Playwright
loan_payload["step"] = "contract"
resp = requests.post(loan_url, data=loan_payload)
resp.raise_for_status()
contract_data = resp.json()

otp_text = contract_data.get("data", {}).get("application_data", {}) \
                        .get("original", {}).get("data", {}).get("otp")
if not otp_text:
    raise Exception("❌ Could not find OTP in contract response")

otp_match = re.search(r"\d{4}", otp_text)
if not otp_match:
    raise Exception("❌ Could not extract numeric OTP")

otp_value = otp_match.group()
print(f"✅ Step contract -> OTP Received: {otp_value}")

# Step: otp
loan_payload["step"] = "otp"
loan_payload["otp"] = otp_value
resp = requests.post(loan_url, data=loan_payload)
resp.raise_for_status()
otp_data = resp.json()
print(f"✅ Step otp -> {otp_data.get('message')}")

# Step: ivr
loan_payload["step"] = "ivr"
resp = requests.post(loan_url, data=loan_payload)
resp.raise_for_status()
ivr_data = resp.json()
print(f"✅ Step ivr -> {ivr_data.get('message')}")

# Final: Callback IVR API
callback_url = f"{base_url}/callback/unifonic-ivr"
callback_payload = {
    "digits": 1,
    "callerId": "+966590933211",
    "direction": "outbound-api",
    "recipient": f"+{phone}"
}

resp = requests.post(callback_url, data=callback_payload)
resp.raise_for_status()
print(f"✅ Callback IVR Triggered -> {resp.json()}")
