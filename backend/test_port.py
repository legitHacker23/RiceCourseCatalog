#!/usr/bin/env python3
"""
Test script to verify port binding
"""

import os
import sys

# Test PORT environment variable
port = os.getenv('PORT', '8000')
print(f"PORT environment variable: {port}")

# Test app import
try:
    from app import app
    print("✅ App imported successfully")
    
    # Test if app can start
    print(f"Testing app startup on port {port}...")
    app.run(debug=False, host='0.0.0.0', port=int(port), use_reloader=False)
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1) 