#!/usr/bin/env python3
"""
Seed demo data for CI testing
"""
import os
from app.models.database import SessionLocal
from app.models.user import User
from app.models.api_key import APIKey

def main():
    db = SessionLocal()
    try:
        admin_email = 'admin@example.com'
        admin = db.query(User).filter_by(email=admin_email).first()
        if not admin:
            admin = User(email=admin_email, name='Admin')
            admin.set_password('adminpass')
            admin.email_verified = True
            db.add(admin)
            db.commit()
            print('Created admin user:', admin_email)

        # Create demo API key for admin
        existing = db.query(APIKey).filter_by(user_id=admin.id, name='Demo Key').first()
        if not existing:
            api = APIKey(user_id=admin.id, name='Demo Key', permissions=['read'])
            # Generate and capture the actual API key string
            actual_key = api._generate_key()
            db.add(api)
            db.commit()
            print('Created demo API key for admin. Key prefix:', api.prefix)
            print('DEMO_API_KEY='+actual_key)
        else:
            print('Demo API key already exists')
    finally:
        db.close()

if __name__ == '__main__':
    main()