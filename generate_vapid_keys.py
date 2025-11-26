#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generate VAPID Keys for Web Push Notifications
Run this script to generate your VAPID public and private keys
"""

try:
    from py_vapid import Vapid01 as Vapid
    
    print("=" * 60)
    print("GENERATING VAPID KEYS FOR WEB PUSH NOTIFICATIONS")
    print("=" * 60)
    print()
    
    # Generate VAPID keys
    v = Vapid()
    v.generate_keys()
    
    public_key = v.save_public_key()
    private_key = v.save_private_key()
    
    print("SUCCESS! VAPID Keys Generated!")
    print()
    print("=" * 60)
    print("COPY THESE TO YOUR .env FILES:")
    print("=" * 60)
    print()
    print("--- BACKEND .env (backend/.env) ---")
    print(f"VAPID_PUBLIC_KEY={public_key}")
    print(f"VAPID_PRIVATE_KEY={private_key}")
    print("VAPID_SUBJECT=mailto:admin@learningapp.com")
    print()
    print("--- FRONTEND .env (frontend/.env) ---")
    print(f"VITE_VAPID_PUBLIC_KEY={public_key}")
    print()
    print("=" * 60)
    print("IMPORTANT NOTES:")
    print("=" * 60)
    print("1. Keep the PRIVATE key secret - NEVER commit to Git")
    print("2. The PUBLIC key is safe to use in frontend")
    print("3. Use the SAME public key in both backend and frontend")
    print("4. Change VAPID_SUBJECT to your actual email")
    print()
    print("Setup complete! Add these to your .env files.")
    print()
    
except ImportError:
    print("ERROR: pywebpush not installed")
    print()
    print("Please install it first:")
    print("  cd backend")
    print("  pip install pywebpush")
    print()
    print("Then run this script again:")
    print("  python generate_vapid_keys.py")



