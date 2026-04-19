from flask import Blueprint, jsonify, request, current_app
from mysql.connector import Error

from backend.db_connection import get_db

sites_bp = Blueprint("sites", __name__)


@sites_bp.route("/sites/<int:site_id>/overview", methods=["GET"])
def get_site_overview(site_id):
    cursor = get_db().cursor(dictionary=True)
    try:
        cursor.execute(
            "SELECT site_id, site_name FROM Garden_Site WHERE site_id = %s", (site_id,)
        )
        site = cursor.fetchone()
        if site is None:
            return jsonify({"error": "Site not found"}), 404

        cursor.execute(
            """
            SELECT COUNT(*) AS occupancy_count
            FROM Plot_Assignment pa
            JOIN Plot p ON p.plot_id = pa.plot_id
            WHERE p.site_id = %s AND pa.end_date IS NULL
            """,
            (site_id,),
        )
        occupancy_count = cursor.fetchone()["occupancy_count"]

        cursor.execute(
            """
            SELECT COUNT(*) AS pending_assignments
            FROM Plot p
            LEFT JOIN Plot_Assignment pa
                ON pa.plot_id = p.plot_id
                AND pa.end_date IS NULL
            WHERE p.site_id = %s
              AND pa.assignment_id IS NULL
            """,
            (site_id,),
        )
        pending_assignments = cursor.fetchone()["pending_assignments"]

        cursor.execute(
            """
            SELECT workday_id, event_name, event_date
            FROM Workday
            WHERE site_id = %s AND event_date >= CURDATE()
            ORDER BY event_date ASC
            LIMIT 5
            """,
            (site_id,),
        )
        upcoming_workdays = cursor.fetchall()

        cursor.execute(
            """
            SELECT COUNT(*) AS active_watering_schedules
            FROM Watering_Schedule ws
            JOIN Plot p ON p.plot_id = ws.plot_id
            WHERE p.site_id = %s
            """,
            (site_id,),
        )
        watering_schedule_count = cursor.fetchone()["active_watering_schedules"]

        cursor.execute(
            """
            SELECT
                ws.schedule_id,
                ws.plot_id,
                p.name AS plot_name,
                ws.crop_id,
                c.crop_name,
                ws.frequency,
                ws.time_of_day,
                ws.method,
                ws.notes
            FROM Watering_Schedule ws
            JOIN Plot p ON p.plot_id = ws.plot_id
            LEFT JOIN Crop c ON c.crop_id = ws.crop_id
            WHERE p.site_id = %s
            ORDER BY ws.schedule_id DESC
            LIMIT 5
            """,
            (site_id,),
        )
        latest_watering_schedules = cursor.fetchall()

        return (
            jsonify(
                {
                    "site": site,
                    "occupancy_count": occupancy_count,
                    "pending_assignments": pending_assignments,
                    "upcoming_workdays": upcoming_workdays,
                    "watering_schedule_count": watering_schedule_count,
                    "latest_watering_schedules": latest_watering_schedules,
                }
            ),
            200,
        )
    except Error as e:
        current_app.logger.error(f"Error fetching site overview: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


@sites_bp.route("/sites/<int:site_id>/watering-schedules", methods=["GET"])
def get_site_watering_schedules(site_id):
    """Return watering schedules for all plots in a site."""
    cursor = get_db().cursor(dictionary=True)
    try:
        query = """
            SELECT
                ws.schedule_id,
                ws.plot_id,
                p.name AS plot_name,
                ws.crop_id,
                c.crop_name,
                ws.frequency,
                ws.time_of_day,
                ws.method,
                ws.notes
            FROM Watering_Schedule ws
            JOIN Plot p ON p.plot_id = ws.plot_id
            LEFT JOIN Crop c ON c.crop_id = ws.crop_id
            WHERE p.site_id = %s
            ORDER BY ws.schedule_id DESC
        """
        cursor.execute(query, (site_id,))
        return jsonify(cursor.fetchall()), 200
    except Error as e:
        current_app.logger.error(f"Error fetching site watering schedules: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


@sites_bp.route("/sites/<int:site_id>/watering-schedules", methods=["POST"])
def create_site_watering_schedule(site_id):
    cursor = get_db().cursor()
    try:
        data = request.get_json() or {}
        required = ["plot_id", "frequency", "time_of_day", "method"]
        missing = [field for field in required if field not in data]
        if missing:
            return (
                jsonify({"error": f"Missing required fields: {', '.join(missing)}"}),
                400,
            )

        cursor.execute(
            "SELECT plot_id FROM Plot WHERE plot_id = %s AND site_id = %s",
            (data["plot_id"], site_id),
        )
        if cursor.fetchone() is None:
            return jsonify({"error": "plot_id does not belong to site"}), 400

        query = """
            INSERT INTO Watering_Schedule (plot_id, crop_id, frequency, time_of_day, method, notes)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        cursor.execute(
            query,
            (
                data["plot_id"],
                data.get("crop_id"),
                data["frequency"],
                data["time_of_day"],
                data["method"],
                data.get("notes"),
            ),
        )
        get_db().commit()
        return (
            jsonify(
                {
                    "message": "Watering schedule created",
                    "schedule_id": cursor.lastrowid,
                }
            ),
            201,
        )
    except Error as e:
        current_app.logger.error(f"Error creating site watering schedule: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
