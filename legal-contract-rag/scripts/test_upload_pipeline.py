import requests
import time
import io

backend_url = "http://127.0.0.1:8000"

# 1. Fetch or create a contract
res = requests.get(f"{backend_url}/api/v1/contracts")
contracts = res.json()
if not contracts:
    res = requests.post(f"{backend_url}/api/v1/contracts", json={"name": "Test Upload Contract", "description": "Automated Test"})
    contract = res.json()
else:
    contract = contracts[0]

contract_id = contract["id"]
print(f"Using Contract ID: {contract_id}")

# 2. Upload a sample legal text document
doc_content = b"""CONFIDENTIAL VENDOR SERVICES AGREEMENT
This Vendor Services Agreement is entered into on January 15, 2024.
ARTICLE 10 - TERMINATION
10.1 Either party may terminate for convenience upon ninety (90) days written notice.
10.2 For Material Breach, notice requirements turn on defined Schedule B-2.
"""
files = {"file": ("test_agreement.txt", io.BytesIO(doc_content), "text/plain")}
data = {"contract_id": contract_id}

upload_res = requests.post(f"{backend_url}/api/v1/documents/upload", files=files, data=data)
print("Upload Response Status:", upload_res.status_code)
upload_json = upload_res.json()
print("Upload Response JSON:", upload_json)
doc_id = upload_json["documentId"]
job_id = upload_json["jobId"]

# 3. Poll document status
print("Waiting for processing to complete...")
for i in range(15):
    time.sleep(1)
    doc_res = requests.get(f"{backend_url}/api/v1/documents/{doc_id}")
    doc_info = doc_res.json()
    status = doc_info.get("status")
    print(f"Second {i+1}: Document status is '{status}'")
    if status in ["Completed", "Failed"]:
        break

print("Final Document State:", doc_info)
