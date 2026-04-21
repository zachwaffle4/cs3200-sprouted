# 🌱 Sprouted — Community Garden Management Platform

Sprouted is a full-stack web application for managing community garden operations. It supports four distinct user roles — Garden Admin, Plot Owner, Volunteer, and Food Bank Partner — each with a dedicated set of features for plot management, harvest tracking, volunteer coordination, and surplus produce distribution.

---

## Team Members

| Name |
|---|
| Emanuel Galindo Garcia |
| Jackson Zheng |
| Shloka Nathan |
| Zach Harel |
| Ayaan Imtiaz |

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Python · Streamlit |
| Backend | Python · Flask (REST API) |
| Database | MySQL 9 |
| Infrastructure | Docker · Docker Compose |

---

## Project Structure

```
cs3200-sprouted/
├── app/                    # Streamlit frontend
│   └── src/
│       ├── Home.py         # Landing page / role selector
│       ├── pages/          # Role-specific pages
│       └── modules/nav.py  # Sidebar navigation (RBAC)
├── api/                    # Flask REST API
│   ├── backend/            # Route blueprints and DB connection
│   ├── .env.template       # Environment variable template
│   └── requirements.txt
├── database-files/
│   ├── sprouted-def.sql    # Schema definition (auto-run on first start)
│   └── seed.py             # Seed script (auto-run on API startup)
├── docker-compose.yaml
└── README.md
```

---

## Getting Started

### Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running
- [Git](https://git-scm.com/) for cloning the repository

### 1 — Clone the Repository

```bash
git clone https://github.com/zachwaffle4/cs3200-sprouted.git
cd cs3200-sprouted
```

### 2 — Create the `.env` File

The API and database containers both require a shared secrets file at **`api/.env`**.

Copy the template and fill in your values:

```bash
cp api/.env.template api/.env
```

Then open `api/.env` and set your passwords:

```env
SECRET_KEY=your_flask_secret_key_here
DB_USER=root
DB_HOST=db
DB_PORT=3306
DB_NAME=sprouted
MYSQL_ROOT_PASSWORD=your_strong_password_here
```

> **Important:** `DB_HOST` must remain `db` — that is the Docker service hostname for the MySQL container. Do not change it to `localhost`.

### 3 — Start All Containers

```bash
docker compose up -d
```

This single command:
1. Builds the Streamlit app image and the Flask API image
2. Starts the MySQL database and runs `sprouted-def.sql` to initialize the schema
3. Waits for MySQL to be ready, then runs `seed.py` to populate the database
4. Starts the Flask API server
5. Starts the Streamlit frontend

### 4 — Open the Application

| Service | URL |
|---|---|
| **Streamlit App** | http://localhost:8501 |
| **Flask REST API** | http://localhost:4000 |
| **MySQL** (external) | `localhost:3200` |

---

## User Roles & Features

Sprouted uses role-based access control. Select a persona from the home screen to enter the app.

### 🛠 Garden Admin — *Derek Washington*
Manages the entire garden site.
- **Dashboard** — Site overview, pending plot applications, upcoming workdays, water budget, open pest reports
- **Plot Manager** — Assign/vacate plots, manage the waitlist queue
- **Workdays Manager** — Schedule community workdays, add tasks, manage volunteer events

### 🌿 Plot Owner — *Maria*
Manages their individual garden plot.
- **My Plot** — View plot details, crop schedules, and harvest history
- **Log Activity** — Record plantings and harvests
- **Report Pest** — Submit pest and disease reports
- **List Surplus** — Post surplus produce for donation

### 🙋 Volunteer — *Clark*
Signs up for and logs community work.
- **Open Tasks** — Browse and sign up for workday tasks
- **My Hours** — View personal volunteer hour logs
- **Event Detail** — See details for a specific workday event

### 🏦 Food Bank Partner — *Lucia*
Requests surplus produce for their organization.
- **Dashboard** — Overview of available produce and recent activity
- **Browse Surplus** — View all available surplus listings and submit requests
- **My Requests** — Track the status of submitted produce requests

---

## Managing the Containers

| Command | Description |
|---|---|
| `docker compose up -d` | Start all containers in the background |
| `docker compose down` | Stop and remove all containers |
| `docker compose down -v` | Stop containers **and delete all data volumes** |
| `docker compose restart` | Restart all running containers |
| `docker compose logs -f api` | Stream logs from the API container |
| `docker compose logs -f app` | Stream logs from the Streamlit container |

### Resetting the Database

If you update `sprouted-def.sql` or `seed.py`, you must recreate the database container to apply changes:

```bash
docker compose down db -v && docker compose up -d
```

> The `-v` flag deletes the MySQL data volume so the schema and seed scripts run fresh on restart.

---

## Development Notes

- **Hot reload** is enabled for both the Flask API and the Streamlit app. Save a file and changes apply immediately.
- In the Streamlit browser tab, click **Always Rerun** when prompted to enable automatic refresh on code changes.
- The database schema is defined in `database-files/sprouted-def.sql` and executed **automatically** when the MySQL container is first created.
- Seed data is generated by `database-files/seed.py` using [Faker](https://faker.readthedocs.io/) and runs **automatically** each time the API container starts.
