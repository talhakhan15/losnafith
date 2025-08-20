# Loan Application Automation (API + UI)

This project automates a **loan application process** by combining **REST API testing** with **Playwright UI automation**, all in **Python**.  

The flow is fully scripted to simulate a real customer journey:
1. User login (API)
2. Loan application process via API steps:
   - Finance
   - Verification
   - Simmah Consent
   - Counter
   - e-Promissory Note
   - (Pause for manual confirmation)
   - Contract
   - OTP
   - IVR
3. Dashboard verification using Playwright (headless browser).

---

## 🔧 Tech Stack
- **Python 3**
- **Requests** → API testing  
- **Playwright (Python)** → Headless UI verification  
- **Virtualenv** → Dependency isolation  

---

## 🚀 Features
- End-to-end loan application simulation.  
- Pauses at e-Promissory step for manual input (`press q to continue`).  
- Verifies loan status in the dashboard UI (headless).  
- Handles multiple users and test data.  

---

## 📦 Setup Instructions

### 1. Clone repo
```bash
git clone https://github.com/yourusername/loan-automation.git
cd loan-automation
