"""
User management script for Overtime Management System.

This script allows creating, editing, and managing users.
"""
from app import app
from models import db, User, Group, AdminGroup

def list_users():
    """List all users."""
    with app.app_context():
        users = User.query.all()
        print("\n=== All Users ===")
        for user in users:
            admin_groups = []
            if user.is_admin():
                admin_groups = [ag.group.name for ag in user.managed_groups]
            print(f"ID: {user.id}, Username: {user.username}, Type: {user.user_type}, "
                  f"Group: {user.group.name}, Managed Groups: {admin_groups if admin_groups else 'N/A'}")

def list_groups():
    """List all groups."""
    with app.app_context():
        groups = Group.query.all()
        print("\n=== All Groups ===")
        for group in groups:
            print(f"ID: {group.id}, Name: {group.name}")

def create_user():
    """Create a new user."""
    with app.app_context():
        print("\n=== Create New User ===")
        username = input("Username: ")
        password = input("Password: ")
        user_type = input("User type (admin/common) [common]: ").lower() or 'common'

        if user_type not in ['admin', 'common']:
            print("Invalid user type. Must be 'admin' or 'common'")
            return

        # Show available groups
        groups = Group.query.all()
        print("\nAvailable groups:")
        for group in groups:
            print(f"  {group.id}: {group.name}")

        group_id = int(input("Group ID: "))

        # Check if group exists
        group = Group.query.get(group_id)
        if not group:
            print(f"Group with ID {group_id} not found")
            return

        # Create user
        user = User(
            username=username,
            user_type=user_type,
            group_id=group_id
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        print(f"\nUser '{username}' created successfully with ID {user.id}")

        # If admin, assign managed groups
        if user_type == 'admin':
            print("\nAssign groups this admin can manage:")
            print("Enter group IDs separated by comma (e.g., 1,2,3)")
            managed_group_ids = input("Managed group IDs: ")

            if managed_group_ids.strip():
                for gid in managed_group_ids.split(','):
                    gid = int(gid.strip())
                    if Group.query.get(gid):
                        admin_group = AdminGroup(admin_id=user.id, group_id=gid)
                        db.session.add(admin_group)
                    else:
                        print(f"Warning: Group ID {gid} not found, skipping")

                db.session.commit()
                print("Admin groups assigned successfully")

def change_password():
    """Change user password."""
    with app.app_context():
        print("\n=== Change User Password ===")
        username = input("Username: ")
        user = User.query.filter_by(username=username).first()

        if not user:
            print(f"User '{username}' not found")
            return

        new_password = input("New password: ")
        user.set_password(new_password)
        db.session.commit()

        print(f"Password changed successfully for user '{username}'")

def make_admin():
    """Convert a common user to admin."""
    with app.app_context():
        print("\n=== Make User Admin ===")
        username = input("Username: ")
        user = User.query.filter_by(username=username).first()

        if not user:
            print(f"User '{username}' not found")
            return

        if user.is_admin():
            print(f"User '{username}' is already an admin")
            return

        user.user_type = 'admin'
        db.session.commit()

        print(f"User '{username}' is now an admin")

        # Assign managed groups
        groups = Group.query.all()
        print("\nAvailable groups:")
        for group in groups:
            print(f"  {group.id}: {group.name}")

        print("\nAssign groups this admin can manage:")
        print("Enter group IDs separated by comma (e.g., 1,2,3)")
        managed_group_ids = input("Managed group IDs: ")

        if managed_group_ids.strip():
            for gid in managed_group_ids.split(','):
                gid = int(gid.strip())
                if Group.query.get(gid):
                    admin_group = AdminGroup(admin_id=user.id, group_id=gid)
                    db.session.add(admin_group)
                else:
                    print(f"Warning: Group ID {gid} not found, skipping")

            db.session.commit()
            print("Admin groups assigned successfully")

def create_group():
    """Create a new group."""
    with app.app_context():
        print("\n=== Create New Group ===")
        name = input("Group name: ")

        # Check if group already exists
        if Group.query.filter_by(name=name).first():
            print(f"Group '{name}' already exists")
            return

        group = Group(name=name)
        db.session.add(group)
        db.session.commit()

        print(f"Group '{name}' created successfully with ID {group.id}")

def change_username():
    """Change a user's username."""
    with app.app_context():
        print("\n=== Change Username ===")
        old_username = input("Current username: ")
        user = User.query.filter_by(username=old_username).first()

        if not user:
            print(f"User '{old_username}' not found")
            return

        new_username = input("New username: ")

        # Check if new username already exists
        if User.query.filter_by(username=new_username).first():
            print(f"Username '{new_username}' already exists")
            return

        user.username = new_username
        db.session.commit()

        print(f"Username changed from '{old_username}' to '{new_username}' successfully")

def change_user_group():
    """Change a user's group."""
    with app.app_context():
        print("\n=== Change User Group ===")
        username = input("Username: ")
        user = User.query.filter_by(username=username).first()

        if not user:
            print(f"User '{username}' not found")
            return

        print(f"\nCurrent group: {user.group.name}")

        # Show available groups
        groups = Group.query.all()
        print("\nAvailable groups:")
        for group in groups:
            print(f"  {group.id}: {group.name}")

        group_id = int(input("\nNew group ID: "))

        # Check if group exists
        group = Group.query.get(group_id)
        if not group:
            print(f"Group with ID {group_id} not found")
            return

        user.group_id = group_id
        db.session.commit()

        print(f"User '{username}' moved to group '{group.name}' successfully")

def manage_admin_groups():
    """Manage which groups an admin can manage."""
    with app.app_context():
        print("\n=== Manage Admin Groups ===")
        username = input("Admin username: ")
        user = User.query.filter_by(username=username).first()

        if not user:
            print(f"User '{username}' not found")
            return

        if not user.is_admin():
            print(f"User '{username}' is not an admin")
            return

        # Show current managed groups
        current_groups = [ag.group.name for ag in user.managed_groups]
        print(f"\nCurrent managed groups: {', '.join(current_groups) if current_groups else 'None'}")

        # Show available groups
        groups = Group.query.all()
        print("\nAvailable groups:")
        for group in groups:
            print(f"  {group.id}: {group.name}")

        print("\nEnter group IDs separated by comma (e.g., 1,2,3)")
        print("Leave empty to remove all managed groups")
        managed_group_ids = input("Managed group IDs: ")

        # Remove all current admin groups
        for ag in user.managed_groups:
            db.session.delete(ag)

        # Add new admin groups
        if managed_group_ids.strip():
            for gid in managed_group_ids.split(','):
                gid = int(gid.strip())
                if Group.query.get(gid):
                    admin_group = AdminGroup(admin_id=user.id, group_id=gid)
                    db.session.add(admin_group)
                else:
                    print(f"Warning: Group ID {gid} not found, skipping")

        db.session.commit()
        print("Admin groups updated successfully")

def delete_user():
    """Delete a user."""
    with app.app_context():
        print("\n=== Delete User ===")
        username = input("Username: ")
        user = User.query.filter_by(username=username).first()

        if not user:
            print(f"User '{username}' not found")
            return

        confirm = input(f"Are you sure you want to delete user '{username}'? (yes/no): ")
        if confirm.lower() != 'yes':
            print("Deletion cancelled")
            return

        db.session.delete(user)
        db.session.commit()

        print(f"User '{username}' deleted successfully")

def main():
    """Main menu."""
    while True:
        print("\n" + "="*50)
        print("User Management System")
        print("="*50)
        print("1. List all users")
        print("2. List all groups")
        print("3. Create new user")
        print("4. Create new group")
        print("5. Change user password")
        print("6. Change username")
        print("7. Change user group")
        print("8. Make user admin")
        print("9. Manage admin groups")
        print("10. Delete user")
        print("0. Exit")
        print("="*50)

        choice = input("\nEnter your choice: ")

        try:
            if choice == '1':
                list_users()
            elif choice == '2':
                list_groups()
            elif choice == '3':
                create_user()
            elif choice == '4':
                create_group()
            elif choice == '5':
                change_password()
            elif choice == '6':
                change_username()
            elif choice == '7':
                change_user_group()
            elif choice == '8':
                make_admin()
            elif choice == '9':
                manage_admin_groups()
            elif choice == '10':
                delete_user()
            elif choice == '0':
                print("\nGoodbye!")
                break
            else:
                print("\nInvalid choice. Please try again.")
        except Exception as e:
            print(f"\nError: {str(e)}")

if __name__ == '__main__':
    main()
