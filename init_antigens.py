import requests

def initialize_antigens():
    try:
        response = requests.post('http://localhost:5000/api/antigens/initialize')
        if response.status_code == 200:
            print("Successfully initialized antigens!")
            print(response.json())
        else:
            print(f"Error initializing antigens: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    initialize_antigens() 