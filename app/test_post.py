import requests
import json
import time

def test_post_request():
    """Test the POST endpoint"""
    url = "http://localhost:8000/analyze"
    
    payload = {
        "user1": "instagram",
        "user2": "natgeo",
        "use_credentials": False,
        "max_posts": 10,
        "max_stories": 5
    }
    
    print("Sending POST request...")
    try:
        # First, send the request to start analysis
        response = requests.post(url, json=payload, timeout=10)
        print(f"Initial response: {response.status_code}")
        print(response.json())
        
        # Get the task ID
        task_id = response.json().get('task_id')
        
        if task_id:
            print(f"\nTask ID: {task_id}")
            print("Checking status every 5 seconds...")
            
            # Check status periodically
            status_url = f"http://localhost:8000/status/{task_id}"
            for i in range(10):  # Check up to 10 times
                time.sleep(5)
                status_response = requests.get(status_url, timeout=10)
                status_data = status_response.json()
                print(f"Status check {i+1}: {status_data['status']}")
                
                if status_data['status'] in ['completed', 'error']:
                    print("\nFinal result:")
                    print(json.dumps(status_data, indent=2))
                    break
                    
    except requests.exceptions.Timeout:
        print("Request timed out - the server might be busy")
    except requests.exceptions.ConnectionError:
        print("Could not connect to server - make sure it's running")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_post_request()