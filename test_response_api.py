import json
import requests

# Create a payload to be sent to the analysis API
payload = {
    "company_name": "Test Company",
    "documents_url": ["https://storage.googleapis.com/tuning-machines-967a0.firebasestorage.app/companies/8tjpjAEH2FlMbNgztRdk/Pitch%20Deck.pdf"]
}
print("Making Request")
response = requests.post(
    "https://tuning-machines-ai.onrender.com/analyze/all",
    json=payload,
)

if response.status_code == 200:
    
    # Convert response string to json format 
    analysis_data = json.loads(json.loads(response.text))
    print(analysis_data, type(analysis_data))

else: 
    print("Error:", response.status_code, response.text)