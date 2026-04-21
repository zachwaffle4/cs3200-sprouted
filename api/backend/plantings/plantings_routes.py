from flask import Blueprint, jsonify, request, current_app
from mysql.connector import Error

from backend.db_connection import get_db

plantings_bp = Blueprint("plantings", __name__)


@plantings_bp.route("/users/<int:user_id>/plots", methods=["GET"])
def get_user_plots(user_id):
    """Return plots currently assigned to a user."""
    cursor = get_db().cursor(dictionary=True)
    try:
        query = """
                SELECT p.plot_id, p.name AS plot_name, p.site_id, gs.site_name,
                       pa.assignment_id, pa.assigned_date
                FROM Plot_Assignment pa
                         JOIN Plot p ON p.plot_id = pa.plot_id
                         JOIN Garden_Site gs ON gs.site_id = p.site_id
                WHERE pa.user_id = %s AND pa.end_date IS NULL
                ORDER BY pa.assigned_date DESC \
                """
        cursor.execute(query, (user_id,))
        return jsonify(cursor.fetchall()), 200
    except Error as e:
        current_app.logger.error(f"Error fetching user plots: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


@plantings_bp.route("/plots/<int:plot_id>/harvests", methods=["GET"])
def get_plot_harvests(plot_id):
    """Return all harvest/planting entries for a plot, newest first."""
    cursor = get_db().cursor(dictionary=True)
    try:
        query = """
                SELECT h.harvest_id, h.plot_id, h.crop_id, c.crop_name, c.crop_type,
                       h.harvest_date, h.quantity_lbs
                FROM Harvest h
                         JOIN Crop c ON c.crop_id = h.crop_id
                WHERE h.plot_id = %s
                ORDER BY h.harvest_date DESC, h.harvest_id DESC \
                """
        cursor.execute(query, (plot_id,))
        return jsonify(cursor.fetchall()), 200
    except Error as e:
        current_app.logger.error(f"Error fetching plot harvests: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


@plantings_bp.route("/plots/<int:plot_id>/harvests", methods=["POST"])
def log_harvest(plot_id):
    """Log a harvest or a new planting (quantity_lbs=0 means a planting)."""
    cursor = get_db().cursor()
    try:
        data = request.get_json() or {}
        required = ["crop_id", "harvest_date"]
        missing = [field for field in required if field not in data]
        if missing:
            return (
                jsonify({"error": f"Missing required fields: {', '.join(missing)}"}),
                400,
            )

        query = """
                INSERT INTO Harvest (plot_id, crop_id, harvest_date, quantity_lbs)
                VALUES (%s, %s, %s, %s) \
                """
        cursor.execute(
            query,
            (
                plot_id,
                data["crop_id"],
                data["harvest_date"],
                data.get("quantity_lbs", 0),
            ),
        )
        get_db().commit()
        return (
            jsonify({"message": "Harvest logged", "harvest_id": cursor.lastrowid}),
            201,
        )
    except Error as e:
        current_app.logger.error(f"Error logging harvest: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


@plantings_bp.route("/harvests/<int:harvest_id>", methods=["DELETE"])
def delete_harvest(harvest_id):
    """Remove a harvest entry."""
    cursor = get_db().cursor()
    try:
        cursor.execute("DELETE FROM Harvest WHERE harvest_id = %s", (harvest_id,))
        if cursor.rowcount == 0:
            return jsonify({"error": "Harvest not found"}), 404
        get_db().commit()
        return jsonify({"message": "Harvest deleted"}), 200
    except Error as e:
        current_app.logger.error(f"Error deleting harvest: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


@plantings_bp.route("/users/<int:user_id>/season-summary", methods=["GET"])
def get_season_summary(user_id):
    """Return season totals, active plantings, and recent harvests for a user."""
    cursor = get_db().cursor(dictionary=True)
    try:
        # Totals across active plots
        cursor.execute(
            """
            SELECT
                COALESCE(SUM(h.quantity_lbs), 0) AS total_yield_lbs,
                COUNT(DISTINCT h.crop_id) AS distinct_crops,
                SUM(CASE WHEN h.quantity_lbs = 0 THEN 1 ELSE 0 END) AS active_plantings,
                SUM(CASE WHEN h.quantity_lbs > 0 THEN 1 ELSE 0 END) AS harvests_recorded
            FROM Plot_Assignment pa
                     LEFT JOIN Harvest h ON h.plot_id = pa.plot_id
            WHERE pa.user_id = %s AND pa.end_date IS NULL
            """,
            (user_id,),
        )
        totals = cursor.fetchone() or {}

        # Active plantings (quantity_lbs = 0 is used as a planting marker)
        cursor.execute(
            """
            SELECT h.harvest_id, p.name AS plot_name, c.crop_name, c.crop_type,
                   h.harvest_date AS expected_harvest_date
            FROM Plot_Assignment pa
                     JOIN Harvest h ON h.plot_id = pa.plot_id
                     JOIN Crop c ON c.crop_id = h.crop_id
                     JOIN Plot p ON p.plot_id = h.plot_id
            WHERE pa.user_id = %s AND pa.end_date IS NULL
              AND h.quantity_lbs = 0
            ORDER BY h.harvest_date ASC
            """,
            (user_id,),
        )
        active_plantings = cursor.fetchall()

        # Recent harvests (quantity_lbs > 0)
        cursor.execute(
            """
            SELECT h.harvest_id, p.name AS plot_name, c.crop_name,
                   h.harvest_date, h.quantity_lbs
            FROM Plot_Assignment pa
                     JOIN Harvest h ON h.plot_id = pa.plot_id
                     JOIN Crop c ON c.crop_id = h.crop_id
                     JOIN Plot p ON p.plot_id = h.plot_id
            WHERE pa.user_id = %s AND pa.end_date IS NULL
              AND h.quantity_lbs > 0
            ORDER BY h.harvest_date DESC
                LIMIT 10
            """,
            (user_id,),
        )
        recent_harvests = cursor.fetchall()

        return (
            jsonify({
                "totals": totals,
                "active_plantings": active_plantings,
                "recent_harvests": recent_harvests,
            }),
            200,
        )
    except Error as e:
        current_app.logger.error(f"Error fetching season summary: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()