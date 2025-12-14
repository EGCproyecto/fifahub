<div align="center">
  <img src="app/static/img/logos/fifa-hub.svg" alt="FIFAHub Logo" width="300">
  
  # FIFAHub
</div>

## Requirements

**For Docker:**
- Docker Engine and Docker Compose installed

**For Vagrant:**
- Vagrant + VirtualBox
- Ansible on your host machine

---

## Development with Docker

1. Copy the configuration file:
   ```bash
   cp .env.docker.example .env
   ```

2. Edit `.env` and change at least `SECRET_KEY` to a random string (required for 2FA).

3. Start the containers:
   ```bash
   docker compose up --build -d
   ```

4. Access http://localhost:5000

To view logs:
```bash
docker compose logs -f web
```

To stop everything:
```bash
docker compose down
```

If you have database authentication issues, delete the volumes and start fresh:
```bash
docker compose down -v
docker compose up --build -d
```

> **Note on ports:** If port 3306 is in use (by a local MySQL/MariaDB installation), the container uses 3307 by default. The Flask app uses port 5000.

---

## Development with Vagrant

1. Copy the configuration file:
   ```bash
   cp .env.vagrant.example .env
   ```

2. Edit `.env` with your values. Make sure to set a `SECRET_KEY`.

3. Start the virtual machine:
   ```bash
   cd vagrant
   vagrant up
   ```

4. Access http://localhost:5000

To SSH into the VM:
```bash
vagrant ssh
```

To stop the VM:
```bash
vagrant halt
```

---

## Important environment variables

| Variable | Description |
|----------|-------------|
| `SECRET_KEY` | Encryption key for 2FA (required) |
| `MARIADB_HOSTNAME` | `db` for Docker, `localhost` for Vagrant |
| `MARIADB_PASSWORD` | Database password |

Email configuration (SMTP) is optional for development.

---

## Production

For production deployments, check the `docker/` folder which contains additional configurations with Nginx and SSL.
