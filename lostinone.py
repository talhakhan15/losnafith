import requests
import re
from playwright.sync_api import sync_playwright

# --- Replace with actual user phone number (used in final IVR callback) ---
phone = 966500000000

# --- Base URL for your environment (e.g., staging/dev/prod) ---
base_url = "https://your-env.example.com"
account_id = "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"

# Step 1: Login API
login_url = f"{base_url}/api/customer/login"
login_payload = {
    "nid": "1234567890",  # Replace with actual NID
    "pin": "******"       # Replace with actual PIN
}
login_headers = {
    "deviceid": "device-id-placeholder"
}

# 🔐 Perform login
resp = requests.post(login_url, data=login_payload, headers=login_headers)
resp.raise_for_status()

login_data = resp.json()
if not login_data.get("success"):
    raise Exception(f"Login failed: {login_data.get('message')}")

user = login_data["data"]["user"]
user_id = user["user_id"]
name = user["name"]
print(f"✅ Login Success. User ID: {user_id}, Name: {name}")

# Step 2: Start loan application process
loan_url = f"{base_url}/api/loan-application"
loan_payload = {
    "product_id": 1,
    "user_id": user_id,
    "amount": 1500,
    "duration": 3,
    "accountId": account_id,
    "purpose_of_finance_id": 1,
}

# These steps are required before moving to contract and signing
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
        print(f"✅ Step '{step}' -> Loan Created. ID: {loan_id}, Number: {loan_number}")
    else:
        print(f"✅ Step '{step}' -> {data.get('message')}")

# Step 3: Get e-Promissory link/info
epromissory_url = f"{base_url}/api/e-promissory"
params = {
    "lang": "ar",
    "loan_application_id": loan_id
}
resp = requests.get(epromissory_url, params=params)
resp.raise_for_status()
eprom_data = resp.json()
print("✅ e-Promissory Response:", eprom_data)

# 🔑 You’ll need to manually enter the myId you get from e-promissory step
my_id = input("🔑 Enter 'myId' from e-promissory (copied from previous response): ")

# Step 4: Headless browser flow using Playwright (simulates user signing process)
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()

    url = f"https://sandbox.example.com/sanad/{my_id}"
    print(f"🌐 Navigating to {url}")
    page.goto(url)

    # Remove "disabled" from OTP input field so we can interact with it
    page.evaluate("document.getElementById('inputOtp').removeAttribute('disabled')")

    # Input test OTP (use correct OTP in production)
    page.fill('#inputOtp', '111111')
    page.press('#inputOtp', 'Enter')

    # Click through UI flow
    page.get_by_role("button", name="تأكيد الرمز").click()
    page.get_by_role("button", name="Search").click()
    page.get_by_role("button", name="متابعة 㰏").click()
    page.get_by_role("checkbox").first.check()
    page.locator('#id_hide_packages_reminder').get_by_role("checkbox").check()
    page.get_by_role("button", name="موافقة").click()

    print("✅ Browser flow completed successfully (headless)")
    browser.close()

# Step 5: Proceed to contract signing step via API
loan_payload["step"] = "contract"
resp = requests.post(loan_url, data=loan_payload)
resp.raise_for_status()
contract_data = resp.json()

# Extract OTP from contract API response
otp_text = contract_data.get("data", {}).get("application_data", {}) \
                        .get("original", {}).get("data", {}).get("otp")
if not otp_text:
    raise Exception("❌ Could not find OTP in contract response")

otp_match = re.search(r"\d{4}", otp_text)
if not otp_match:
    raise Exception("❌ Could not extract numeric OTP")

otp_value = otp_match.group()
print(f"✅ Step 'contract' -> OTP Received: {otp_value}")

# Step 6: Submit OTP
loan_payload["step"] = "otp"
loan_payload["otp"] = otp_value
resp = requests.post(loan_url, data=loan_payload)
resp.raise_for_status()
otp_data = resp.json()
print(f"✅ Step 'otp' -> {otp_data.get('message')}")

# Step 7: Trigger IVR flow
loan_payload["step"] = "ivr"
resp = requests.post(loan_url, data=loan_payload)
resp.raise_for_status()
ivr_data = resp.json()
print(f"✅ Step 'ivr' -> {ivr_data.get('message')}")

# Step 8: Final IVR callback (simulated)
callback_url = f"{base_url}/callback/unifonic-ivr"
callback_payload = {
    "digits": 1,
    "callerId": "+966500000000",  # Redacted caller ID
    "direction": "outbound-api",
    "recipient": f"+{phone}"
}

resp = requests.post(callback_url, data=callback_payload)
resp.raise_for_status()
print(f"✅ Final IVR Callback Triggered -> {resp.json()}")
