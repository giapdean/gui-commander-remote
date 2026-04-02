import requests

def test_ntfy(id):
    try:
        url = f"https://ntfy.sh/{id}"
        response = requests.post(url, data="Test from Machine 1 (AI Assistant)".encode('utf-8'))
        print(f"Sent to {url}, Status: {response.status_code}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_ntfy("antigravity-gui-DESKTOP-OTH6L0T-ee70")
