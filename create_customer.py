import bcrypt
from database import get_db_session
from models import User
from datetime import datetime

def hash_password(password):
    """Secure password hashing using bcrypt with salt"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode(), salt).decode()

def create_customer_user(email, password):
    """Create a customer user with the specified credentials"""
    with get_db_session() as db:
        existing_user = db.query(User).filter(User.email == email).first()
        
        if existing_user:
            existing_user.password_hash = hash_password(password)
            existing_user.is_admin = False
            existing_user.username = email.split('@')[0]
            existing_user.last_login = datetime.utcnow()
            print(f"Updated existing user {email} to customer")
        else:
            customer_user = User(
                email=email,
                username=email.split('@')[0],
                password_hash=hash_password(password),
                is_admin=False,
                created_at=datetime.utcnow(),
                last_login=datetime.utcnow(),
                plan_type='free',
                usage_limit=10
            )
            db.add(customer_user)
            print(f"Created new customer user: {email}")
        
        db.commit()
        print("Customer user created successfully!")

if __name__ == "__main__":
    create_customer_user("tacs8419@gmail.com", "ABCD12345xz")
