# test_config.py - Verify configuration loads correctly

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from config import (
        DATABASE_URL, 
        SECRET_KEY, 
        OPENAI_API_KEY,
        ACCESS_TOKEN_EXPIRE_MINUTES
    )
    
    print("✓ DATABASE_URL loaded")
    print("✓ SECRET_KEY loaded")
    print("✓ OPENAI_API_KEY loaded")
    print("✓ ACCESS_TOKEN_EXPIRE_MINUTES loaded")
    print("\n✓✓✓ All configurations loaded successfully! ✓✓✓")
    
except Exception as e:
    print(f"✗ Error loading configuration: {e}")
    print("Make sure your .env file is created correctly!")
