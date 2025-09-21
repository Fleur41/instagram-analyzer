import requests
import json
import time

def test_detailed_analysis():
    """Test with detailed analysis"""
    url = "http://localhost:8000/analyze"
    
    # Test with popular accounts that likely interact
    test_cases = [
        {
            "user1": "therock",
            "user2": "kevinhart4real",
            "max_posts": 15
        },
        {
            "user1": "kyliejenner", 
            "user2": "kimkardashian",
            "max_posts": 10
        },
        {
            "user1": "instagram",
            "user2": "natgeo",
            "max_posts": 10
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n=== Test Case {i}: {test_case['user1']} -> {test_case['user2']} ===")
        
        payload = {
            "user1": test_case["user1"],
            "user2": test_case["user2"],
            "use_credentials": False,
            "max_posts": test_case["max_posts"],
            "max_stories": 0
        }
        
        try:
            # Send the request
            response = requests.post(url, json=payload, timeout=20)
            
            if response.status_code == 200:
                data = response.json()
                task_id = data.get('task_id')
                
                if task_id:
                    print(f"Task started: {task_id}")
                    print("Waiting for analysis...")
                    
                    # Wait for completion
                    for wait in range(8):  # Wait up to 40 seconds
                        time.sleep(5)
                        status_url = f"http://localhost:8000/status/{task_id}"
                        status_response = requests.get(status_url, timeout=10)
                        
                        if status_response.status_code == 200:
                            status_data = status_response.json()
                            
                            if status_data['status'] == 'completed':
                                result = status_data['result']
                                print(f"\n✅ Analysis completed in {result.get('analysis_time', 0):.1f}s")
                                
                                # Print key results
                                print(f"Posts analyzed: {result.get('posts_analyzed', 0)}")
                                print(f"Likes found: {result.get('user1_likes_count', 0)}")
                                print(f"Comments found: {result.get('user1_comments_count', 0)}")
                                
                                # Show comments if any
                                comments = result.get('user1_comments', [])
                                if comments:
                                    print(f"\n📝 Comments found:")
                                    for comment in comments[:3]:  # Show first 3 comments
                                        print(f"  - {comment.get('text', '')[:50]}...")
                                
                                # Show recent posts info
                                recent_posts = result.get('recent_posts', [])
                                if recent_posts:
                                    print(f"\n📊 Recent posts analyzed:")
                                    for post in recent_posts[:2]:  # Show first 2 posts
                                        print(f"  - {post.get('likes', 0)} likes, {post.get('comments', 0)} comments")
                                
                                break
                                
                            elif status_data['status'] == 'error':
                                print(f"❌ Error: {status_data.get('error', 'Unknown error')}")
                                break
                    
                    print("\n" + "="*50)
                    
            else:
                print(f"Error: HTTP {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"Test failed: {e}")
        
        time.sleep(2)  # Brief pause between tests

if __name__ == "__main__":
    test_detailed_analysis()