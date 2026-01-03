import requests
import json

def test_outreach_leads():
    url = "http://localhost:5000/api/select-leads-for-outreach?status=new&limit=10"
    try:
        response = requests.get(url)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            print("Success!")
            print(json.dumps(response.json(), indent=2))
        else:
            print("Error!")
            print(response.text)
    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    test_outreach_leads()
