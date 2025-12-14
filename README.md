<div align="center">
  <img src="app/static/img/logos/fifa-hub.svg" alt="FIFAHub Logo" width="300">
  
  # FIFAHub
  
  **A FIFA Player Dataset Repository**
</div>

## About FIFAHub

FIFAHub is a platform for sharing and exploring FIFA video game player datasets. It allows users to upload, validate, and browse CSV datasets containing player statistics from EA Sports FC / FIFA games.

### Key Features

- **Dataset Upload**: Upload FIFA player datasets with automatic schema validation
- **Explore & Search**: Browse and search through available datasets
- **Statistics**: View player statistics, ratings, and attributes
- **Communities**: Organize datasets into communities

---

## Dataset Requirements

FIFAHub only accepts CSV datasets that follow the official FIFA player data schema. Your CSV file **must contain the following columns**:

| Column | Description | Example |
|--------|-------------|---------|
| `ID` | Unique player identifier | `158023` |
| `Name` | Player name | `L. Messi` |
| `Age` | Player age | `36` |
| `Nationality` | Player nationality | `Argentina` |
| `Overall` | Overall rating (0-99) | `90` |
| `Potential` | Potential rating (0-99) | `90` |
| `Club` | Current club | `Inter Miami` |
| `Value` | Market value | `€16M` |
| `Wage` | Weekly wage | `€150K` |
| `Preferred Foot` | Left or Right | `Left` |
| `Weak Foot` | Weak foot rating (1-5) | `4` |
| `Skill Moves` | Skill moves rating (1-5) | `4` |
| `Position` | Playing position | `RW` |
| `Height` | Player height | `170cm` |
| `Weight` | Player weight | `72kg` |

> **Note**: Additional columns (like Pace, Shooting, Dribbling, etc.) are allowed and will be preserved. Only the columns above are required.

### Example CSV

```csv
ID,Name,Age,Nationality,Overall,Potential,Club,Value,Wage,Preferred Foot,Weak Foot,Skill Moves,Position,Height,Weight
158023,L. Messi,36,Argentina,90,90,Inter Miami,16000000,150000,Left,4,4,RW,170,72
231747,K. Mbappé,24,France,91,95,Real Madrid,180000000,230000,Right,4,5,ST,178,73
```

---

## Documentation

Additional documentation is available in the [`docs/`](docs/) folder:

- [**CI/CD Workflows**](docs/README.md) - GitHub Actions pipelines and deployment process
- [**Contributing Guide**](docs/CONTRIBUTING.md) - How to contribute to FIFAHub

---

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

## Important Environment Variables

| Variable | Description |
|----------|-------------|
| `SECRET_KEY` | Encryption key for 2FA (required) |
| `MARIADB_HOSTNAME` | `db` for Docker, `localhost` for Vagrant |
| `MARIADB_PASSWORD` | Database password |

Email configuration (SMTP) is optional for development.

---

## Production

For production deployments, check the `docker/` folder which contains additional configurations with Nginx and SSL.

---

## Technology Stack

- **Backend**: Python 3.12, Flask
- **Database**: MariaDB
- **Frontend**: Jinja2 Templates, Bootstrap 5
- **Testing**: pytest
- **CI/CD**: GitHub Actions
- **Deployment**: Docker, Render

---

## License

This project is based on [UVLHub](https://github.com/diverso-lab/uvlhub) by DiversoLab.
