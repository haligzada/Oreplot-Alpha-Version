import bcrypt
from database import get_db_session
from models import User
from datetime import datetime

def hash_password(password):
    """Secure password hashing using bcrypt with salt"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode(), salt).decode()

def create_test_user(email, password):
    """Create a test user with the specified credentials"""
    with get_db_session() as db:
        existing_user = db.query(User).filter(User.email == email).first()
        
        if existing_user:
            existing_user.password_hash = hash_password(password)
            existing_user.is_admin = True
            existing_user.username = email.split('@')[0]
            existing_user.last_login = datetime.utcnow()
            existing_user.plan_type = 'enterprise'
            existing_user.usage_limit = 999999
            print(f"Updated existing user {email}")
        else:
            test_user = User(
                email=email,
                username=email.split('@')[0],
                password_hash=hash_password(password),
                is_admin=True,
                created_at=datetime.utcnow(),
                last_login=datetime.utcnow(),
                plan_type='enterprise',
                usage_limit=999999
            )
            db.add(test_user)
            print(f"Created new test user: {email}")
        
        db.commit()
        print("Test user created successfully!")

if __name__ == "__main__":
    create_test_user("test@test.com", "test123")
