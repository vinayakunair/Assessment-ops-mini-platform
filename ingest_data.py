import json
import requests

# Read the JSON data
with open('attempt_events.json', 'r') as f:
    data = json.load(f)

print(f"Loaded {len(data)} attempts from JSON file")

# Send to the API in batches
url = "http://127.0.0.1:8000/api/ingest/attempts"

# Split into batches of 100 to avoid too large request
batch_size = 100
for i in range(0, len(data), batch_size):
    batch = data[i:i+batch_size]
    response = requests.post(url, json=batch)
    result = response.json()
    print(f"Batch {i//batch_size + 1}: Saved={result.get('saved')}, Skipped={result.get('skipped')}")

print("Ingest complete!")
