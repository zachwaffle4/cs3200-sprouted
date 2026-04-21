from flask import Flask
from dotenv import load_dotenv
import os
import logging

from backend.db_connection import init_app as init_db
from backend.workdays.workday_routes import workdays_bp
from backend.volunteers.volunteer_routes import volunteers_bp
from backend.plots.plot_routes import plots_bp
from backend.sites.site_routes import sites_bp
from backend.pests.pest_routes import pests_bp
from backend.surplus.surplus_routes import surplus_bp
from backend.analytics.analytics_routes import analytics_bp
from backend.applications.application_routes import applications_bp
from backend.plantings.plantings_routes import plantings_bp


def create_app():
    app = Flask(__name__)

    app.logger.setLevel(logging.DEBUG)
    app.logger.info("API startup")

    # Load environment variables from the .env file so they are
    # accessible via os.getenv() below.
    load_dotenv()

    # Secret key used by Flask for securely signing session cookies.
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")

    # Database connection settings — values come from the .env file.
    app.config["MYSQL_DATABASE_USER"] = os.getenv("DB_USER").strip()
    app.config["MYSQL_DATABASE_PASSWORD"] = os.getenv("MYSQL_ROOT_PASSWORD").strip()
    app.config["MYSQL_DATABASE_HOST"] = os.getenv("DB_HOST").strip()
    app.config["MYSQL_DATABASE_PORT"] = int(os.getenv("DB_PORT").strip())
    app.config["MYSQL_DATABASE_DB"] = os.getenv("DB_NAME").strip()

    # Register the cleanup hook for the database connection.
    app.logger.info("create_app(): initializing database connection")
    init_db(app)

    # Register the routes from each Blueprint with the app object
    # and give a url prefix to each.
    app.logger.info("create_app(): registering blueprints")
    app.register_blueprint(workdays_bp)
    app.register_blueprint(volunteers_bp)
    app.register_blueprint(plots_bp)
    app.register_blueprint(sites_bp)
    app.register_blueprint(pests_bp)
    app.register_blueprint(surplus_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(applications_bp)
    app.register_blueprint(plantings_bp)

    return app
