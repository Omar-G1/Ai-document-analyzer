# test_auth.py - Test authentication

from auth import (
    hash_password, 
    verify_password, 
    create_access_token,
    decode_access_token
)

print("=" * 50)
print("Testing Authentication")
print("=" * 50)

# Test 1: Hash password
print("\n✓ Test 1: Hash password")
password = "mypassword123"
hashed = hash_password(password)
print(f"  Original: {password}")
print(f"  Hashed:   {hashed[:20]}... (truncated)")

# Test 2: Verify correct password
print("\n✓ Test 2: Verify correct password")
is_correct = verify_password(password, hashed)
print(f"  Password matches: {is_correct}")
assert is_correct == True

# Test 3: Verify wrong password
print("\n✗ Test 3: Verify wrong password")
is_correct = verify_password("wrongpassword", hashed)
print(f"  Password matches: {is_correct}")
assert is_correct == False

# Test 4: Create token
print("\n✓ Test 4: Create JWT token")
token = create_access_token({"sub": "john_doe"})
print(f"  Token: {token[:30]}... (truncated)")

# Test 5: Decode token
print("\n✓ Test 5: Decode JWT token")
username = decode_access_token(token)
print(f"  Decoded username: {username}")
assert username == "john_doe"

# Test 6: Decode invalid token
print("\n✗ Test 6: Decode invalid token")
invalid_token = "invalid.token.here"
username = decode_access_token(invalid_token)
print(f"  Result: {username}")
assert username is None

print("\n" + "=" * 50)
print("✓✓✓ All authentication tests passed! ✓✓✓")
print("=" * 50)
