# Overtime Management System

A Flask-based web application for tracking and managing employee overtime hours.

## Features

### User Features
- Secure login system with Flask-Login
- Personal dashboard to add and view overtime records
- Track overtime by date, duration (minutes), and description
- View total overtime hours accumulated

### Admin Features
- Admin panel to view overtime records for managed groups
- Filter overtime records by:
  - Group
  - Date range
- View detailed overtime records for individual users
- Delete overtime records for users in managed groups
- Comprehensive logging of all activities

### Logging
The application logs the following events:
- User login attempts (successful and failed)
- Overtime record creation (with full details)
- Overtime record deletion by admins (with full audit trail)

Logs are stored in `logs/app.log` by default.

## Project Structure

```
overtime/
├── app.py                  # Main Flask application
├── models.py               # Database models (User, Group, AdminGroup, Overtime)
├── init_db.py              # Database initialization script
├── .env                    # Environment configuration (excluded from git)
├── requirements.txt        # Python dependencies
├── logs/                   # Application logs directory
│   └── app.log
├── templates/              # HTML templates
│   ├── base.html          # Base template with navigation
│   ├── login.html         # Login page
│   ├── dashboard.html     # User dashboard
│   ├── admin.html         # Admin panel
│   └── admin_user_details.html  # Detailed user overtime view
├── static/                 # Static files (CSS, JS, images)
└── venv/                   # Python virtual environment

```

## Database Schema

### User
- `id`: Primary key
- `username`: Unique username
- `password_hash`: Hashed password
- `user_type`: 'admin' or 'common'
- `group_id`: Foreign key to Group

### Group
- `id`: Primary key
- `name`: Group name (e.g., Engineering, Marketing)

### AdminGroup
- `id`: Primary key
- `admin_id`: Foreign key to User (admin)
- `group_id`: Foreign key to Group
- Maps which groups each admin can manage

### Overtime
- `id`: Primary key
- `user_id`: Foreign key to User
- `date`: Date of overtime work
- `minutes`: Duration in minutes
- `description`: Work description
- `created_at`: Record creation timestamp

## Setup Instructions

### Prerequisites
- Python 3.8 or higher
- MariaDB/MySQL database server
- pip and venv

### Installation

1. Clone or download the project

2. Create and activate virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Linux/Mac
# or
venv\Scripts\activate  # On Windows
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment variables in `.env`:
```env
SECRET_KEY=your-secret-key-change-this-in-production
FLASK_ENV=development

DB_HOST=your-database-host
DB_USER=your-database-user
DB_PASSWORD=your-database-password
DB_NAME=your-database-name
DB_PORT=3306

LOG_FILE=logs/app.log
LOG_LEVEL=INFO
```

5. Initialize the database:
```bash
python init_db.py
```

When prompted, type 'y' to seed test data with sample users and overtime records.

6. Run the application:
```bash
python app.py
```

The application will be available at `http://localhost:5000`

## Test Accounts

If you seeded test data, you can login with:

**Admin Account:**
- Username: `admin`
- Password: `admin123`
- Can manage: Engineering and Marketing groups

**User Accounts:**
- Username: `john`, Password: `password123` (Engineering)
- Username: `jane`, Password: `password123` (Engineering)
- Username: `bob`, Password: `password123` (Marketing)
- Username: `alice`, Password: `password123` (Sales)

## Usage Guide

### For Regular Users

1. **Login**: Navigate to the login page and enter your credentials
2. **Add Overtime**: On your dashboard, fill in the form with:
   - Date of overtime work
   - Duration in minutes
   - Description of work done
3. **View Records**: See all your overtime entries in a table below the form
4. **Track Total**: View your total accumulated overtime hours

### For Administrators

1. **Login** with admin credentials
2. **Access Admin Panel**: Click "Admin Panel" in the navigation
3. **Filter Records**: Use filters to view overtime by:
   - Specific group
   - Date range
4. **View User Details**: Click "View Details" to see individual user's overtime records
5. **Delete Records**: On the user details page, click "Delete" to remove overtime entries (requires confirmation)

## Security Features

- Password hashing with Werkzeug's security utilities
- Session-based authentication with Flask-Login
- Role-based access control (admin vs common users)
- Group-based permissions (admins can only manage assigned groups)
- Comprehensive audit logging for security events

## Configuration

### Environment Variables

- `SECRET_KEY`: Flask secret key for session management
- `FLASK_ENV`: Application environment (development/production)
- `DB_HOST`: Database server hostname
- `DB_USER`: Database username
- `DB_PASSWORD`: Database password
- `DB_NAME`: Database name
- `DB_PORT`: Database port (default: 3306)
- `LOG_FILE`: Path to log file
- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

## Development

To run in development mode with auto-reload:
```bash
export FLASK_ENV=development
python app.py
```

## Production Deployment

For production deployment:

1. Change `SECRET_KEY` to a strong random value
2. Set `FLASK_ENV=production`
3. Use a production WSGI server (e.g., Gunicorn, uWSGI)
4. Configure proper database backups
5. Set up log rotation
6. Enable HTTPS
7. Configure firewall rules

Example with Gunicorn:
```bash
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

## Troubleshooting

### Database Connection Issues
- Verify database credentials in `.env`
- Ensure database server is running and accessible
- Check firewall rules allow connection to database port

### Login Issues
- Check logs in `logs/app.log` for error details
- Verify user exists in database
- Ensure password was set correctly during user creation

### Permission Issues
- Verify admin user has entries in `admin_groups` table
- Check user's `user_type` is set to 'admin'
- Ensure admin is assigned to the correct groups

## License

This project is provided as-is for educational and internal use.

## Support

For issues or questions, please check the logs and database configuration first. The logging system provides detailed information about all operations for troubleshooting.
