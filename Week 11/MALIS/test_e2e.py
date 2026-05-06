# test_e2e.py
import requests
import time

API_URL = "http://localhost:8000/process-shipment"

payload = {
    "shipment": {
        "customer_id": "CUST-9921",
        "route": "Los Angeles, CA -> Dallas, TX",
        "cost": 4500.00,
        "goods_description": "High-value electronics, laptops and servers."
    }
}

print("Initiating logistics pipeline...")
start_time = time.time()

response = requests.post(API_URL, json=payload)
end_time = time.time()

if response.status_code == 200:
    data = response.json()
    print(f"\n✅ Success! Pipeline completed in {end_time - start_time:.2f} seconds.")
    print(f"Transaction ID: {data['transaction_id']}")
    
    # Print the final state variables
    state = data['final_state']
    print("\n--- Pipeline Results ---")
    print(f"Fraud Score: {state.get('fraud_score')} ({state.get('fraud_reasoning')})")
    print(f"Funding: {state.get('funding_decision')} | Terms: {state.get('funding_terms')}")
    print(f"Invoice Total: ${state.get('invoice_details', {}).get('total')}")
    print(f"Compliance: {state.get('compliance_status')} | Notes: {state.get('compliance_notes')}")
else:
    print(f"❌ Error: {response.status_code}")
    print(response.text)