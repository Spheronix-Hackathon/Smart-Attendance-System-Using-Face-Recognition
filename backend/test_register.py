import requests
import json

url = "http://127.0.0.1:8000/register"
payload = {
    "full_name": "Test Student",
    "roll_number": "12345",
    "email": "test@example.com",
    "department": "Computer Science",
    "password": "password123",
    "face_image": "dummy_base64"
}

resp = requests.post(url, json=payload)
print(f"Status Code: {resp.status_code}")
print(f"Response: {json.dumps(resp.json(), indent=2)}")
