"""
Seed the Sprouted community-garden database with realistic fake data.
Uses the Faker library and mysql-connector-python.
"""

import os
from dotenv import load_dotenv
from typing import List
import random
from datetime import timedelta
from faker import Faker
import mysql.connector

fake = Faker()
Faker.seed(42)
random.seed(42)

load_dotenv(os.path.join(os.path.dirname(__file__), '../api/.env'))

roles = ["volunteer", "admin", "coordinator", "gardener"]
orgTypes = ["Food Bank", "Shelter", "School", "Restaurant", "Community Center"]
wateringFreq = ["daily", "every other day", "twice a week", "weekly"]
wateringTime = ["morning", "evening", "afternoon"]
wateringMethod = ["drip", "sprinkler", "hand watering", "soaker hose"]
severities = ["low", "medium", "high", "critical"]
urgencies = ["low", "medium", "high"]
taskStatus = ["pending", "in progress", "completed"]

cropData = [
("Tomato", "Vegetable"), ("Basil", "Herb"), ("Lettuce", "Vegetable"),
("Carrot", "Vegetable"), ("Pepper", "Vegetable"), ("Kale", "Vegetable"),
("Cilantro", "Herb"), ("Squash", "Vegetable"), ("Cucumber", "Vegetable"),
("Strawberry", "Fruit"), ("Mint", "Herb"), ("Zucchini", "Vegetable"),
("Spinach", "Vegetable"), ("Radish", "Vegetable"), ("Green Bean", "Vegetable"),
("Rosemary", "Herb"), ("Blueberry", "Fruit"), ("Corn", "Vegetable"),
("Pumpkin", "Vegetable"), ("Thyme", "Herb")
]

numSites = 100
numCrops = len(cropData)
numUser = 100
numOrgs = 100
numPlots = 100

plot_names = ["Bed A", "Bed B", "Bed C", "Bed D", "North Plot", "South Plot",
            "Herb Spiral", "Raised Bed 1", "Raised Bed 2", "Greenhouse Row"]

numWorkDays = 100
numSchedules = 100
numHarvests = 100
numPestReports = 100
numAssignments = 100
numYieldPairs = 30
numListings = 100
numRequests = 100
numPickups = 1

numTasks = 100
task_descriptions = [
    "Weed the raised beds", "Spread mulch along pathways",
    "Set up irrigation lines", "Plant seedlings in Bed A",
    "Harvest ripe tomatoes", "Repair fence on north side",
    "Turn compost bins", "Clear debris after storm",
    "Install new row covers", "Label all crop rows",
]

numSignUps = 100
numLogs = 100
numApplications = 15

def mysqlConnector () -> None: 
    global MySQL
    global db 
    db = mysql.connector.connect(
        host = "localhost",
        port = os.environ.get("DB_PORT", "3200"),
        user = os.environ.get("DB_USER", "root"),
        password = os.environ.get("MYSQL_ROOT_PASSWORD", ""),
        database = os.environ.get("DB_NAME", "Sprouted"),
    )
    MySQL = db.cursor()

def seedSites (numSites: int) -> None:
    for _ in range(numSites):
        MySQL.execute(
            "INSERT INTO Garden_Site (site_name, street, city, state, zip) VALUES (%s,%s,%s,%s,%s)",
            (
                fake.company() + " Community Garden",
                fake.street_address(),
                fake.city(),
                fake.state_abbr(),
                fake.zipcode(),
            ),
        )
    db.commit()

def seedCropData (cropData : List[tuple]) -> None:
    for name, ctype in cropData:
        MySQL.execute(
            "INSERT INTO Crop (crop_name, crop_type) VALUES (%s,%s)",
            (name, ctype),
        )
    db.commit()

def seedUsers (numUser: int) -> None:
    for _ in range(numUser):
        MySQL.execute(
            "INSERT INTO User (role, email, phone, first_name, last_name) VALUES (%s,%s,%s,%s,%s)",
            (
                random.choice(roles),
                fake.unique.email(),
                fake.phone_number()[:20],
                fake.first_name(),
                fake.last_name(),
            ),
        )
    db.commit()

def seedOrgs (numOrgs: int) -> None :
    for _ in range(numOrgs):
        MySQL.execute(
            """INSERT INTO Organization
            (org_name, org_type, contact_name, contact_email, contact_phone, address)
            VALUES (%s,%s,%s,%s,%s,%s)""",
            (
                fake.company(),
                random.choice(orgTypes),
                fake.name(),
                fake.email(),
                fake.phone_number()[:20],
                fake.address().replace("\n", ", "),
            ),
        )
    db.commit()

def seedPlots (numPlots : int) -> None:
    for _ in range(numPlots):
        MySQL.execute(
            "INSERT INTO Plot (name, site_id) VALUES (%s,%s)",
            (
                random.choice(plot_names) + f" #{fake.random_int(1, 99)}",
                random.randint(1, numSites),
            ),
        )
    db.commit()

def seedWorkDays (numWorkDays: int) -> None: 
    for _ in range(numWorkDays):
        event_date = fake.date_between(start_date="-60d", end_date="+30d")
        start_hour = random.randint(7, 12)
        MySQL.execute(
            """INSERT INTO Workday
            (site_id, event_name, event_date, description, volunteers_needed, start_time, end_time)
            VALUES (%s,%s,%s,%s,%s,%s,%s)""",
            (
                random.randint(1, numSites),
                fake.bs().title() + " Workday",
                event_date,
                fake.sentence(nb_words=10),
                random.randint(3, 20),
                f"{start_hour:02d}:00:00",
                f"{start_hour + random.randint(2, 5):02d}:00:00",
            ),
        )
    db.commit()

def seedSchedules (numSchedules: int) -> None: 
    for _ in range(numSchedules):
        MySQL.execute(
            """INSERT INTO Watering_Schedule
            (plot_id, crop_id, frequency, time_of_day, method, notes)
            VALUES (%s,%s,%s,%s,%s,%s)""",
            (
                random.randint(1, numPlots),
                random.randint(1, numCrops),
                random.choice(wateringFreq),
                random.choice(wateringTime),
                random.choice(wateringMethod),
                fake.sentence() if random.random() > 0.4 else None,
            ),
        )
    db.commit()

def seedHarvest (numHarvests : int) -> None:
    for _ in range(numHarvests):
        MySQL.execute(
            """INSERT INTO Harvest (plot_id, crop_id, harvest_date, quantity_lbs)
            VALUES (%s,%s,%s,%s)""",
            (
                random.randint(1, numPlots),
                random.randint(1, numCrops),
                fake.date_between(start_date="-90d", end_date="today"),
                round(random.uniform(0.5, 50.0), 2),
            ),
        )
    db.commit()

def seedPestReports (numPestReports : int) -> None:
    for _ in range(numPestReports):
        MySQL.execute(
            """INSERT INTO Pest_Report
            (plot_id, crop_id, user_id, description, severity, date_reported, status)
            VALUES (%s,%s,%s,%s,%s,%s,%s)""",
            (
                random.randint(1, numPlots),
                random.randint(1, numCrops),
                random.randint(1, numUser),
                fake.sentence(nb_words=8),
                random.choice(severities),
                fake.date_between(start_date="-60d", end_date="today"),
                random.choice(["open", "in progress", "resolved"]),
            ),
        )
    db.commit()

def seedAssignments (numAssignments : int) -> None:
    for _ in range(numAssignments):
        assigned = fake.date_between(start_date="-120d", end_date="today")
        end = assigned + timedelta(days=random.randint(30, 180)) if random.random() > 0.3 else None
        MySQL.execute(
            """INSERT INTO Plot_Assignment (plot_id, user_id, assigned_date, end_date)
            VALUES (%s,%s,%s,%s)""",
            (
                random.randint(1, numPlots),
                random.randint(1, numUser),
                assigned,
                end,
            ),
        )
    db.commit()

def seedYieldPairs(pairs: int) -> None:
    yield_pairs = set()
    while len(yield_pairs) < pairs:
        yield_pairs.add((random.randint(1, numPlots), random.randint(1, numCrops)))

    for plot_id, crop_id in yield_pairs:
        MySQL.execute(
            "INSERT INTO Yield (plot_id, crop_id, total_quantity) VALUES (%s,%s,%s)",
            (plot_id, crop_id, round(random.uniform(5, 200), 2)),
        )
    db.commit()

def seedListing (numListings : int) -> None: 
    for _ in range(numListings):
        MySQL.execute(
            """INSERT INTO Surplus_Listing
            (plot_id, crop_id, quantity_lbs, listed_date, freshness_note, status)
            VALUES (%s,%s,%s,%s,%s,%s)""",
            (
                random.randint(1, numPlots),
                random.randint(1, numCrops),
                round(random.uniform(1, 30), 2),
                fake.date_between(start_date="-30d", end_date="today"),
                random.choice(["Picked this morning", "Harvested yesterday",
                            "Very fresh", "Good condition", None]),
                random.choice(["available", "claimed", "expired"]),
            ),
        )
    db.commit()

def seedProduceRequests (numRequests : int) -> None:
    for _ in range(numRequests):
        req_date = fake.date_between(start_date="-20d", end_date="today")
        MySQL.execute(
            """INSERT INTO Produce_Request
            (org_id, listing_id, requested_date, preferred_pickup_date, status)
            VALUES (%s,%s,%s,%s,%s)""",
            (
                random.randint(1, numOrgs),
                random.randint(1, numListings),
                req_date,
                req_date + timedelta(days=random.randint(1, 5)),
                random.choice(["pending", "approved", "denied", "completed"]),
            ),
        )
    db.commit()

def seedPickups (numPickups : int) -> None:
    used_requests = random.sample(range(1, numRequests + 1), k=min(numPickups, numRequests))
    for req_id in used_requests:
        MySQL.execute(
            """INSERT INTO Pickup
            (request_id, pickup_date, qty_received_lbs, quality_rating, notes)
            VALUES (%s,%s,%s,%s,%s)""",
            (
                req_id,
                fake.date_between(start_date="-15d", end_date="today"),
                round(random.uniform(1, 25), 2),
                random.randint(1, 5),
                fake.sentence() if random.random() > 0.5 else None,
            ),
        )
    db.commit()

def seedTasks (numTasks : int) -> None:
    for _ in range(numTasks):
        MySQL.execute(
            """INSERT INTO Workday_Task
            (workday_id, task_description, location_note, urgency, status)
            VALUES (%s,%s,%s,%s,%s)""",
            (
                random.randint(1, numWorkDays),
                random.choice(task_descriptions),
                fake.sentence(nb_words=4) if random.random() > 0.3 else None,
                random.choice(urgencies),
                random.choice(taskStatus),
            ),
        )
    db.commit()

def seedSignUps (numSignUps : int) -> None:
    for _ in range(numSignUps):
        MySQL.execute(
            """INSERT INTO Event_Signup (user_id, workday_id, signup_date, status)
            VALUES (%s,%s,%s,%s)""",
            (
                random.randint(1, numUser),
                random.randint(1, numWorkDays),
                fake.date_between(start_date="-30d", end_date="today"),
                random.choice(["registered", "attended", "cancelled"]),
            ),
        )
    db.commit()

def seedApplications(numApplications: int) -> None:
    statuses = ["pending", "pending", "pending", "waitlisted", "waitlisted", "approved", "rejected"]
    for _ in range(numApplications):
        MySQL.execute(
            """INSERT INTO Plot_Application (user_id, plot_id, requested_date, status)
            VALUES (%s, %s, %s, %s)""",
            (
                random.randint(1, numUser),
                random.randint(1, numPlots) if random.random() > 0.4 else None,
                fake.date_between(start_date="-30d", end_date="today"),
                random.choice(statuses),
            ),
        )
    db.commit()


def seedLogs (numLogs : int) -> None:
    for _ in range(numLogs):
        MySQL.execute(
            """INSERT INTO Volunteer_Log (user_id, task_id, work_date, hours_logged, notes)
            VALUES (%s,%s,%s,%s,%s)""",
            (
                random.randint(1, numUser),
                random.randint(1, numTasks),
                fake.date_between(start_date="-60d", end_date="today"),
                round(random.uniform(0.5, 8.0), 2),
                fake.sentence() if random.random() > 0.5 else None,
            ),
        )
    db.commit()

def fetchAll (table: str) -> None:
    MySQL.execute(f"SELECT * FROM {table}")
    rows = MySQL.fetchall()
    print(f"Retrieving data for the table {table}")
    if rows == []:
        raise ValueError("Empty Value") 
    else:
        for row in rows:
            print(row)

def retrieveAll () -> None:
    tables = [
        "Garden_Site",
        "Crop",
        "User",
        "Organization",
        "Plot",
        "Workday",
        "Watering_Schedule",
        "Harvest",
        "Pest_Report",
        "Plot_Assignment",
        "Yield",
        "Surplus_Listing",
        "Produce_Request",
        "Pickup",
        "Workday_Task",
        "Event_Signup",
        "Volunteer_Log",
        "Plot_Application",
    ]
    for table in tables:
        print()
        fetchAll(table)

def main ():
    mysqlConnector()

    print(MySQL)
    seedSites(numSites)
    seedCropData(cropData)
    seedUsers(numUser)
    seedOrgs(numOrgs)
    seedPlots(numPlots)
    seedWorkDays(numWorkDays)
    seedSchedules(numSchedules)
    seedHarvest(numHarvests)
    seedPestReports(numPestReports)
    seedAssignments(numAssignments)
    seedYieldPairs(numYieldPairs)
    seedListing(numListings)
    seedProduceRequests(numRequests)
    seedPickups(numPickups)
    seedTasks(numTasks)
    seedSignUps(numSignUps)
    seedLogs(numLogs)
    retrieveAll()

    MySQL.close()
    db.close()

if __name__ == "__main__":
    main()
