"""
Flask application for Overtime Management System.

This application allows users to track overtime hours and administrators
to manage and view overtime records for their teams.
"""
import os
import logging
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from dotenv import load_dotenv
from models import db, User, Group, AdminGroup, Overtime
from sqlalchemy import func

# Timezone configuration
TIMEZONE = ZoneInfo('Europe/Prague')

def get_current_time():
    """Get current time in Czech timezone."""
    return datetime.now(TIMEZONE)

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = (
    f"mysql+pymysql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@"
    f"{os.getenv('DB_HOST')}:{os.getenv('DB_PORT', 3306)}/{os.getenv('DB_NAME')}"
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Configure logging
log_file = os.getenv('LOG_FILE', 'logs/app.log')
log_level = getattr(logging, os.getenv('LOG_LEVEL', 'INFO'))
os.makedirs(os.path.dirname(log_file), exist_ok=True)

logging.basicConfig(
    level=log_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


@login_manager.user_loader
def load_user(user_id):
    """Load user by ID for Flask-Login."""
    return User.query.get(int(user_id))


@app.route('/')
def index():
    """Redirect to dashboard if logged in, otherwise to login page."""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login."""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            login_user(user)
            logger.info(f"User logged in: {username} (ID: {user.id}, Type: {user.user_type})")
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            logger.warning(f"Failed login attempt for username: {username}")
            flash('Invalid username or password', 'error')

    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    """Handle user logout."""
    username = current_user.username
    user_id = current_user.id
    logout_user()
    logger.info(f"User logged out: {username} (ID: {user_id})")
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))


@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    """Display user dashboard with overtime management."""
    if request.method == 'POST':
        date_str = request.form.get('date')
        minutes = request.form.get('minutes')
        description = request.form.get('description')

        if not date_str or not minutes or not description:
            flash('All fields are required', 'error')
        else:
            try:
                date = datetime.strptime(date_str, '%Y-%m-%d').date()
                minutes = int(minutes)

                if minutes <= 0:
                    flash('Minutes must be greater than 0', 'error')
                else:
                    overtime = Overtime(
                        user_id=current_user.id,
                        date=date,
                        minutes=minutes,
                        description=description
                    )
                    db.session.add(overtime)
                    db.session.commit()

                    logger.info(
                        f"Overtime added: User {current_user.username} (ID: {current_user.id}), "
                        f"Date: {date}, Minutes: {minutes}, Description: {description}"
                    )
                    flash('Overtime record added successfully!', 'success')
                    return redirect(url_for('dashboard'))

            except ValueError as e:
                flash('Invalid date or minutes format', 'error')
                logger.error(f"Error adding overtime for user {current_user.id}: {str(e)}")

    # Get user's overtime records
    overtime_records = Overtime.query.filter_by(user_id=current_user.id).order_by(Overtime.date.desc()).all()

    # Calculate total overtime
    total_minutes = sum(record.minutes for record in overtime_records)
    total_hours = total_minutes // 60
    total_mins = total_minutes % 60

    # Get today's date in Czech timezone
    today = get_current_time().date()

    return render_template(
        'dashboard.html',
        overtime_records=overtime_records,
        total_hours=total_hours,
        total_mins=total_mins,
        today=today
    )


@app.route('/admin')
@login_required
def admin_panel():
    """Display admin panel for viewing and managing overtime records."""
    if not current_user.is_admin():
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('dashboard'))

    # Get filter parameters
    group_id = request.args.get('group_id', type=int)
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    # Get groups this admin can manage
    managed_group_ids = current_user.get_managed_group_ids()
    managed_groups = Group.query.filter(Group.id.in_(managed_group_ids)).all() if managed_group_ids else []

    # Build query for overtime records with LEFT JOIN to include users with no overtime
    query = db.session.query(
        User.id,
        User.username,
        Group.name.label('group_name'),
        func.coalesce(func.sum(Overtime.minutes), 0).label('total_minutes')
    ).outerjoin(Overtime, User.id == Overtime.user_id)\
     .join(Group, User.group_id == Group.id)\
     .filter(User.group_id.in_(managed_group_ids))

    # Apply filters
    if group_id and group_id in managed_group_ids:
        query = query.filter(User.group_id == group_id)

    # Build subquery for date filtering
    date_filter_applied = False
    if start_date or end_date:
        # We need to filter overtime records by date, so use a different approach
        overtime_query = db.session.query(
            Overtime.user_id,
            func.sum(Overtime.minutes).label('total_minutes')
        )

        if start_date:
            try:
                start = datetime.strptime(start_date, '%Y-%m-%d').date()
                overtime_query = overtime_query.filter(Overtime.date >= start)
                date_filter_applied = True
            except ValueError:
                flash('Invalid start date format', 'error')

        if end_date:
            try:
                end = datetime.strptime(end_date, '%Y-%m-%d').date()
                overtime_query = overtime_query.filter(Overtime.date <= end)
                date_filter_applied = True
            except ValueError:
                flash('Invalid end date format', 'error')

        if date_filter_applied:
            overtime_query = overtime_query.group_by(Overtime.user_id).subquery()

            # Rebuild query with date-filtered overtime
            query = db.session.query(
                User.id,
                User.username,
                Group.name.label('group_name'),
                func.coalesce(overtime_query.c.total_minutes, 0).label('total_minutes')
            ).outerjoin(overtime_query, User.id == overtime_query.c.user_id)\
             .join(Group, User.group_id == Group.id)\
             .filter(User.group_id.in_(managed_group_ids))

            if group_id and group_id in managed_group_ids:
                query = query.filter(User.group_id == group_id)

    # Group by user and get results
    if not date_filter_applied:
        user_stats = query.group_by(User.id, User.username, Group.name).all()
    else:
        user_stats = query.all()

    # Format results
    overtime_summary = []
    for stat in user_stats:
        hours = stat.total_minutes // 60
        mins = stat.total_minutes % 60
        overtime_summary.append({
            'user_id': stat.id,
            'username': stat.username,
            'group_name': stat.group_name,
            'total_hours': hours,
            'total_mins': mins,
            'total_minutes': stat.total_minutes
        })

    return render_template(
        'admin.html',
        overtime_summary=overtime_summary,
        managed_groups=managed_groups,
        selected_group=group_id,
        start_date=start_date,
        end_date=end_date
    )


@app.route('/admin/user/<int:user_id>')
@login_required
def admin_user_details(user_id):
    """Display detailed overtime records for a specific user."""
    if not current_user.is_admin():
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('dashboard'))

    user = User.query.get_or_404(user_id)

    # Check if admin can manage this user's group
    if not current_user.can_manage_group(user.group_id):
        flash('Access denied. You cannot manage this user.', 'error')
        return redirect(url_for('admin_panel'))

    # Get overtime records
    overtime_records = Overtime.query.filter_by(user_id=user_id).order_by(Overtime.date.desc()).all()

    # Calculate total
    total_minutes = sum(record.minutes for record in overtime_records)
    total_hours = total_minutes // 60
    total_mins = total_minutes % 60

    return render_template(
        'admin_user_details.html',
        user=user,
        overtime_records=overtime_records,
        total_hours=total_hours,
        total_mins=total_mins
    )


@app.route('/admin/delete/<int:overtime_id>', methods=['POST'])
@login_required
def admin_delete_overtime(overtime_id):
    """Delete an overtime record (admin only)."""
    if not current_user.is_admin():
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('dashboard'))

    overtime = Overtime.query.get_or_404(overtime_id)
    user = User.query.get(overtime.user_id)

    # Check if admin can manage this user's group
    if not current_user.can_manage_group(user.group_id):
        flash('Access denied. You cannot delete this record.', 'error')
        return redirect(url_for('admin_panel'))

    # Log deletion
    logger.info(
        f"Overtime deleted by admin: Admin {current_user.username} (ID: {current_user.id}) "
        f"deleted record ID {overtime_id} for user {user.username} (ID: {user.id}), "
        f"Date: {overtime.date}, Minutes: {overtime.minutes}, Description: {overtime.description}"
    )

    db.session.delete(overtime)
    db.session.commit()

    flash('Overtime record deleted successfully.', 'success')
    return redirect(url_for('admin_user_details', user_id=user.id))


@app.route('/admin/users')
@login_required
def admin_users():
    """Display user management page for admins."""
    if not current_user.is_admin():
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('dashboard'))

    # Get groups this admin can manage
    managed_group_ids = current_user.get_managed_group_ids()
    managed_groups = Group.query.filter(Group.id.in_(managed_group_ids)).all() if managed_group_ids else []

    # Get all users in managed groups
    users = User.query.filter(User.group_id.in_(managed_group_ids)).all() if managed_group_ids else []

    # Get all groups for the dropdown
    all_groups = Group.query.all()

    return render_template(
        'admin_users.html',
        users=users,
        managed_groups=managed_groups,
        all_groups=all_groups
    )


@app.route('/admin/users/create', methods=['POST'])
@login_required
def admin_create_user():
    """Create a new user (admin only)."""
    if not current_user.is_admin():
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('dashboard'))

    username = request.form.get('username')
    password = request.form.get('password')
    user_type = request.form.get('user_type', 'common')
    group_id = request.form.get('group_id', type=int)

    # Validation
    if not username or not password or not group_id:
        flash('All fields are required', 'error')
        return redirect(url_for('admin_users'))

    # Check if admin can manage this group
    if not current_user.can_manage_group(group_id):
        flash('Access denied. You cannot create users in this group.', 'error')
        return redirect(url_for('admin_users'))

    # Check if username already exists
    if User.query.filter_by(username=username).first():
        flash(f'Username "{username}" already exists', 'error')
        return redirect(url_for('admin_users'))

    # Create user
    new_user = User(
        username=username,
        user_type=user_type,
        group_id=group_id
    )
    new_user.set_password(password)
    db.session.add(new_user)
    db.session.commit()

    # If admin, assign managed groups
    if user_type == 'admin':
        managed_group_ids = request.form.getlist('managed_groups')
        for gid in managed_group_ids:
            gid = int(gid)
            if current_user.can_manage_group(gid):
                admin_group = AdminGroup(admin_id=new_user.id, group_id=gid)
                db.session.add(admin_group)
        db.session.commit()

    logger.info(f"User created by admin: Admin {current_user.username} (ID: {current_user.id}) created user {username} (ID: {new_user.id})")
    flash(f'User "{username}" created successfully', 'success')
    return redirect(url_for('admin_users'))


@app.route('/admin/users/edit/<int:user_id>', methods=['POST'])
@login_required
def admin_edit_user(user_id):
    """Edit a user (admin only)."""
    if not current_user.is_admin():
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('dashboard'))

    user = User.query.get_or_404(user_id)

    # Check if admin can manage this user's group
    if not current_user.can_manage_group(user.group_id):
        flash('Access denied. You cannot edit this user.', 'error')
        return redirect(url_for('admin_users'))

    username = request.form.get('username')
    password = request.form.get('password')
    user_type = request.form.get('user_type')
    group_id = request.form.get('group_id', type=int)

    # Validation
    if not username or not user_type or not group_id:
        flash('Username, user type, and group are required', 'error')
        return redirect(url_for('admin_users'))

    # Check if admin can manage the new group
    if not current_user.can_manage_group(group_id):
        flash('Access denied. You cannot assign users to this group.', 'error')
        return redirect(url_for('admin_users'))

    # Check if username is taken by another user
    existing_user = User.query.filter_by(username=username).first()
    if existing_user and existing_user.id != user_id:
        flash(f'Username "{username}" is already taken', 'error')
        return redirect(url_for('admin_users'))

    # Update user
    old_username = user.username
    user.username = username
    user.user_type = user_type
    user.group_id = group_id

    if password:
        user.set_password(password)

    # Update admin groups if user is admin
    if user_type == 'admin':
        # Remove old admin groups
        for ag in user.managed_groups:
            db.session.delete(ag)

        # Add new admin groups
        managed_group_ids = request.form.getlist('managed_groups')
        for gid in managed_group_ids:
            gid = int(gid)
            if current_user.can_manage_group(gid):
                admin_group = AdminGroup(admin_id=user.id, group_id=gid)
                db.session.add(admin_group)

    db.session.commit()

    logger.info(f"User edited by admin: Admin {current_user.username} (ID: {current_user.id}) edited user {old_username} -> {username} (ID: {user.id})")
    flash(f'User "{username}" updated successfully', 'success')
    return redirect(url_for('admin_users'))


@app.route('/admin/users/delete/<int:user_id>', methods=['POST'])
@login_required
def admin_delete_user(user_id):
    """Delete a user (admin only)."""
    if not current_user.is_admin():
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('dashboard'))

    user = User.query.get_or_404(user_id)

    # Prevent deleting yourself
    if user.id == current_user.id:
        flash('You cannot delete yourself', 'error')
        return redirect(url_for('admin_users'))

    # Check if admin can manage this user's group
    if not current_user.can_manage_group(user.group_id):
        flash('Access denied. You cannot delete this user.', 'error')
        return redirect(url_for('admin_users'))

    username = user.username
    db.session.delete(user)
    db.session.commit()

    logger.info(f"User deleted by admin: Admin {current_user.username} (ID: {current_user.id}) deleted user {username} (ID: {user_id})")
    flash(f'User "{username}" deleted successfully', 'success')
    return redirect(url_for('admin_users'))


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5001))
    app.run(debug=True, host='0.0.0.0', port=port)
