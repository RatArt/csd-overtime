"""
Database initialization script for Overtime Management System.

This script creates all database tables and optionally seeds them with test data.
"""
import os
from dotenv import load_dotenv
from app import app
from models import db, User, Group, AdminGroup, Overtime
from datetime import date, timedelta

# Load environment variables
load_dotenv()


def init_database():
    """Initialize the database with tables."""
    with app.app_context():
        print("Creating database tables...")
        db.create_all()
        print("Database tables created successfully!")


def seed_test_data():
    """Seed the database with test data."""
    with app.app_context():
        # Check if data already exists
        if User.query.first():
            print("Database already contains data. Skipping seed.")
            return

        print("Seeding test data...")

        # Create groups
        group1 = Group(name='Engineering')
        group2 = Group(name='Marketing')
        group3 = Group(name='Sales')

        db.session.add_all([group1, group2, group3])
        db.session.commit()

        # Create admin user
        admin = User(
            username='admin',
            user_type='admin',
            group_id=group1.id
        )
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()

        # Assign groups to admin
        admin_group1 = AdminGroup(admin_id=admin.id, group_id=group1.id)
        admin_group2 = AdminGroup(admin_id=admin.id, group_id=group2.id)
        db.session.add_all([admin_group1, admin_group2])
        db.session.commit()

        # Create common users
        user1 = User(
            username='john',
            user_type='common',
            group_id=group1.id
        )
        user1.set_password('password123')

        user2 = User(
            username='jane',
            user_type='common',
            group_id=group1.id
        )
        user2.set_password('password123')

        user3 = User(
            username='bob',
            user_type='common',
            group_id=group2.id
        )
        user3.set_password('password123')

        user4 = User(
            username='alice',
            user_type='common',
            group_id=group3.id
        )
        user4.set_password('password123')

        db.session.add_all([user1, user2, user3, user4])
        db.session.commit()

        # Create sample overtime records
        today = date.today()

        # John's overtime
        overtime1 = Overtime(
            user_id=user1.id,
            date=today - timedelta(days=5),
            minutes=120,
            description='Fixed critical production bug'
        )
        overtime2 = Overtime(
            user_id=user1.id,
            date=today - timedelta(days=3),
            minutes=90,
            description='Completed deployment after hours'
        )

        # Jane's overtime
        overtime3 = Overtime(
            user_id=user2.id,
            date=today - timedelta(days=7),
            minutes=180,
            description='Weekend maintenance work'
        )
        overtime4 = Overtime(
            user_id=user2.id,
            date=today - timedelta(days=1),
            minutes=60,
            description='Late night code review'
        )

        # Bob's overtime
        overtime5 = Overtime(
            user_id=user3.id,
            date=today - timedelta(days=4),
            minutes=150,
            description='Campaign launch preparation'
        )

        db.session.add_all([overtime1, overtime2, overtime3, overtime4, overtime5])
        db.session.commit()

        print("\nTest data seeded successfully!")
        print("\nTest Users:")
        print("  Admin: username='admin', password='admin123'")
        print("  User 1: username='john', password='password123' (Engineering)")
        print("  User 2: username='jane', password='password123' (Engineering)")
        print("  User 3: username='bob', password='password123' (Marketing)")
        print("  User 4: username='alice', password='password123' (Sales)")
        print("\nNote: Admin can manage Engineering and Marketing groups.")


if __name__ == '__main__':
    init_database()

    # Ask user if they want to seed test data
    response = input("\nDo you want to seed test data? (y/n): ")
    if response.lower() == 'y':
        seed_test_data()

    print("\nDatabase initialization complete!")
