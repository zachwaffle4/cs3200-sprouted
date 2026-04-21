from flask import Blueprint, jsonify, request, current_app
from mysql.connector import Error

from backend.db_connection import get_db

plots_bp = Blueprint("plots", __name__)


@plots_bp.route("/plots", methods=["GET"])
def get_plots():
    """Return all plots with current assignment state and occupancy."""
    cursor = get_db().cursor(dictionary=True)
    try:
        query = """
            SELECT
                p.plot_id,
                p.name AS plot_name,
                p.site_id,
                gs.site_name,
                pa.assignment_id AS active_assignment_id,
                pa.user_id AS assigned_user_id,
                CASE WHEN pa.assignment_id IS NULL THEN 'vacant' ELSE 'assigned' END AS occupancy_status
            FROM Plot p
            JOIN Garden_Site gs ON gs.site_id = p.site_id
            LEFT JOIN Plot_Assignment pa
                ON pa.plot_id = p.plot_id
                AND pa.end_date IS NULL
            ORDER BY p.plot_id
        """
        cursor.execute(query)
        return jsonify(cursor.fetchall()), 200
    except Error as e:
        current_app.logger.error(f"Error fetching plots: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


@plots_bp.route("/plots/<int:plot_id>/assignments", methods=["GET"])
def get_plot_assignments(plot_id):
    """Return the current active assignment for a plot."""
    cursor = get_db().cursor(dictionary=True)
    try:
        query = """
            SELECT assignment_id, plot_id, user_id, assigned_date, end_date
            FROM Plot_Assignment
            WHERE plot_id = %s AND end_date IS NULL
            ORDER BY assigned_date DESC
        """
        cursor.execute(query, (plot_id,))
        return jsonify(cursor.fetchall()), 200
    except Error as e:
        current_app.logger.error(f"Error fetching plot assignments: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


@plots_bp.route("/plots/<int:plot_id>/assignments", methods=["POST"])
def assign_plot(plot_id):
    cursor = get_db().cursor()
    try:
        data = request.get_json() or {}
        if "user_id" not in data:
            return jsonify({"error": "Missing required field: user_id"}), 400

        # Keep one active assignment per plot unless caller explicitly closes prior assignment.
        cursor.execute(
            "SELECT assignment_id FROM Plot_Assignment WHERE plot_id = %s AND end_date IS NULL",
            (plot_id,),
        )
        if cursor.fetchone() is not None:
            return jsonify({"error": "Plot already has an active assignment"}), 409

        query = """
            INSERT INTO Plot_Assignment (plot_id, user_id, assigned_date)
            VALUES (%s, %s, COALESCE(%s, CURDATE()))
        """
        cursor.execute(query, (plot_id, data["user_id"], data.get("assigned_date")))

        get_db().commit()
        return (
            jsonify(
                {"message": "Assignment created", "assignment_id": cursor.lastrowid}
            ),
            201,
        )
    except Error as e:
        current_app.logger.error(f"Error creating plot assignment: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


@plots_bp.route("/assignments/<int:assignment_id>", methods=["DELETE"])
def deactivate_assignment(assignment_id):
    cursor = get_db().cursor()
    try:
        end_date = (request.get_json() or {}).get("end_date")
        query = """
            UPDATE Plot_Assignment
            SET end_date = COALESCE(%s, CURDATE())
            WHERE assignment_id = %s AND end_date IS NULL
        """
        cursor.execute(query, (end_date, assignment_id))
        if cursor.rowcount == 0:
            return jsonify({"error": "Active assignment not found"}), 404

        get_db().commit()
        return jsonify({"message": "Assignment marked inactive"}), 200
    except Error as e:
        current_app.logger.error(f"Error deactivating assignment: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
