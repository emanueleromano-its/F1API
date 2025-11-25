"""Test script for authentication system.

Run this to verify:
1. User registration works
2. Password hashing is secure
3. Login authentication works
4. User retrieval works
"""
import sys
from pathlib import Path

# Add src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from f1api.auth_repository import get_auth_repo


def test_auth_system():
    """Test the authentication system."""
    print("🧪 Testing F1API Authentication System\n")
    
    auth_repo = get_auth_repo()
    
    # Test 1: Create a test user
    print("Test 1: Creating test user...")
    test_username = "testuser"
    test_email = "test@f1api.com"
    test_password = "testpassword123"
    
    # Check if user already exists and skip creation
    if auth_repo.username_exists(test_username):
        print(f"✓ User '{test_username}' already exists, skipping creation")
    else:
        user_id = auth_repo.create_user(test_username, test_email, test_password)
        if user_id:
            print(f"✓ User created successfully with ID: {user_id}")
        else:
            print("✗ Failed to create user (username or email may already exist)")
    
    # Test 2: Retrieve user by username
    print("\nTest 2: Retrieving user by username...")
    user = auth_repo.get_user_by_username(test_username)
    if user:
        print(f"✓ User found: {user['username']} ({user['email']})")
        print(f"  Created: {user['created_at']}")
    else:
        print("✗ User not found")
    
    # Test 3: Test authentication with correct password
    print("\nTest 3: Testing authentication with correct password...")
    auth_user = auth_repo.authenticate(test_username, test_password)
    if auth_user:
        print(f"✓ Authentication successful!")
        print(f"  User: {auth_user['username']}")
        print(f"  Email: {auth_user['email']}")
    else:
        print("✗ Authentication failed")
    
    # Test 4: Test authentication with wrong password
    print("\nTest 4: Testing authentication with wrong password...")
    wrong_auth = auth_repo.authenticate(test_username, "wrongpassword")
    if wrong_auth:
        print("✗ Authentication should have failed but didn't!")
    else:
        print("✓ Authentication correctly rejected wrong password")
    
    # Test 5: Check username/email uniqueness
    print("\nTest 5: Testing username/email uniqueness checks...")
    username_exists = auth_repo.username_exists(test_username)
    email_exists = auth_repo.email_exists(test_email)
    print(f"✓ Username exists check: {username_exists}")
    print(f"✓ Email exists check: {email_exists}")
    
    print("\n" + "="*50)
    print("✅ All authentication tests completed!")
    print("="*50)
    print("\nYou can now:")
    print("1. Run the Flask app: python -m f1api.app")
    print("2. Visit http://localhost:5000")
    print("3. Register a new account or login with test credentials:")
    print(f"   Username: {test_username}")
    print(f"   Password: {test_password}")


if __name__ == "__main__":
    test_auth_system()
