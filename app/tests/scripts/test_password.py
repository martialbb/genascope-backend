#!/usr/bin/env python3
import bcrypt

# Test password verification
password = "admin123"
stored_hash = "$2b$12$fg7dXzr5B4xJfFbjLXdCfea7Uwet83h2kPGWSc9Aip/PeBaktgG8G"

# Verify password
result = bcrypt.checkpw(password.encode('utf-8'), stored_hash.encode('utf-8'))
print(f"Password '{password}' verification: {result}")

# Test with the superadmin hash
superadmin_hash = "$2b$12$TJANOGQCeto3ICLpfTWQy.KpqccLVyyvcIQfWqzC2oTkzDn6ipwgq"
result2 = bcrypt.checkpw(password.encode('utf-8'), superadmin_hash.encode('utf-8'))
print(f"Password '{password}' verification (superadmin): {result2}")
