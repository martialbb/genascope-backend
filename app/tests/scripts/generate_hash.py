#!/usr/bin/env python3
import bcrypt

# Generate a proper hash for "admin123"
password = "admin123"
salt = bcrypt.gensalt()
hash_result = bcrypt.hashpw(password.encode('utf-8'), salt)

print(f"Password: {password}")
print(f"Generated hash: {hash_result.decode('utf-8')}")

# Verify it works
verification = bcrypt.checkpw(password.encode('utf-8'), hash_result)
print(f"Verification test: {verification}")
