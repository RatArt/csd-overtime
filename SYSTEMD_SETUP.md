# Systemd User Service Setup

This guide will help you set up the Overtime Management application as a systemd user service that starts automatically on boot.

## Prerequisites

- Gunicorn installed in virtual environment
- Application working correctly

## Step 1: Install Gunicorn

```bash
cd /home/berant/overtime
. venv/bin/activate
pip install gunicorn
pip freeze > requirements.txt
```

## Step 2: Create Gunicorn Configuration File

Create a file `gunicorn_config.py` in the project root:

```python
# Gunicorn configuration file
import os

# Server socket
bind = "0.0.0.0:5001"

# Worker processes
workers = 4
worker_class = "sync"
worker_connections = 1000
timeout = 120
keepalive = 5

# Logging
accesslog = "/home/berant/overtime/logs/gunicorn_access.log"
errorlog = "/home/berant/overtime/logs/gunicorn_error.log"
loglevel = "info"

# Process naming
proc_name = "overtime-app"

# Server mechanics
daemon = False
pidfile = None
user = None
group = None
tmp_upload_dir = None

# SSL (if needed in future)
# keyfile = None
# certfile = None
```

## Step 3: Create Systemd Service File

Create the systemd user service directory if it doesn't exist:

```bash
mkdir -p ~/.config/systemd/user
```

Create the service file `~/.config/systemd/user/overtime.service`:

```ini
[Unit]
Description=Overtime Management Flask Application
After=network.target

[Service]
Type=simple
WorkingDirectory=/home/berant/overtime
Environment="PATH=/home/berant/overtime/venv/bin"
ExecStart=/home/berant/overtime/venv/bin/gunicorn -c /home/berant/overtime/gunicorn_config.py app:app
Restart=always
RestartSec=10

# Logging
StandardOutput=append:/home/berant/overtime/logs/systemd_output.log
StandardError=append:/home/berant/overtime/logs/systemd_error.log

[Install]
WantedBy=default.target
```

## Step 4: Enable Lingering (Important!)

This allows user services to run even when you're not logged in:

```bash
loginctl enable-linger $USER
```

## Step 5: Reload Systemd and Enable Service

```bash
# Reload systemd to recognize the new service
systemctl --user daemon-reload

# Enable service to start on boot
systemctl --user enable overtime.service

# Start the service now
systemctl --user start overtime.service
```

## Step 6: Verify Service is Running

```bash
# Check service status
systemctl --user status overtime.service

# View recent logs
journalctl --user -u overtime.service -n 50

# Follow logs in real-time
journalctl --user -u overtime.service -f
```

## Managing the Service

### Start the service
```bash
systemctl --user start overtime.service
```

### Stop the service
```bash
systemctl --user stop overtime.service
```

### Restart the service
```bash
systemctl --user restart overtime.service
```

### Check service status
```bash
systemctl --user status overtime.service
```

### View logs
```bash
# Last 50 lines
journalctl --user -u overtime.service -n 50

# Follow logs
journalctl --user -u overtime.service -f

# Logs since today
journalctl --user -u overtime.service --since today
```

### Disable service (prevent auto-start on boot)
```bash
systemctl --user disable overtime.service
```

## Troubleshooting

### Service won't start
1. Check the logs:
   ```bash
   journalctl --user -u overtime.service -n 100
   ```

2. Test gunicorn manually:
   ```bash
   cd /home/berant/overtime
   . venv/bin/activate
   gunicorn -c gunicorn_config.py app:app
   ```

3. Check file permissions:
   ```bash
   ls -la /home/berant/overtime/
   ```

### Service starts but application doesn't work
1. Check application logs:
   ```bash
   tail -f /home/berant/overtime/logs/app.log
   tail -f /home/berant/overtime/logs/gunicorn_error.log
   ```

2. Check database connection in `.env` file

3. Test database connectivity:
   ```bash
   cd /home/berant/overtime
   . venv/bin/activate
   python -c "from app import app, db; app.app_context().push(); print('DB OK')"
   ```

### Service stops after logout
- Make sure lingering is enabled:
  ```bash
  loginctl show-user $USER | grep Linger
  ```
- Should show: `Linger=yes`

### Port already in use
- Check what's using the port:
  ```bash
  lsof -i :5001
  ```
- Kill the process or change the port in `gunicorn_config.py`

## Production Considerations

### Update .env for Production
```bash
nano /home/berant/overtime/.env
```

Change:
- `SECRET_KEY` to a strong random value
- `FLASK_ENV=production`

### Generate a strong SECRET_KEY
```bash
python -c 'import secrets; print(secrets.token_hex(32))'
```

### Firewall Configuration
If you want to access the app from other machines:

```bash
# Allow port 5001
sudo ufw allow 5001/tcp

# Or for specific IP
sudo ufw allow from 192.168.1.0/24 to any port 5001
```

### Nginx Reverse Proxy (Optional)
For production, consider setting up Nginx as a reverse proxy in front of Gunicorn.

## Updating the Application

When you make changes to the code:

```bash
cd /home/berant/overtime
git pull  # if using git
systemctl --user restart overtime.service
```

## Complete Setup Script

Here's a quick script to set everything up:

```bash
#!/bin/bash
cd /home/berant/overtime

# Install gunicorn
. venv/bin/activate
pip install gunicorn
pip freeze > requirements.txt

# Create systemd directory
mkdir -p ~/.config/systemd/user

# Enable lingering
loginctl enable-linger $USER

# Create service file (you'll need to create the gunicorn_config.py manually)
echo "Remember to create gunicorn_config.py and the service file!"

# Reload and start
systemctl --user daemon-reload
systemctl --user enable overtime.service
systemctl --user start overtime.service

echo "Service setup complete! Check status with: systemctl --user status overtime.service"
```

## Monitoring

### Check if service is running
```bash
systemctl --user is-active overtime.service
```

### Check if service is enabled
```bash
systemctl --user is-enabled overtime.service
```

### View all user services
```bash
systemctl --user list-units --type=service
```
