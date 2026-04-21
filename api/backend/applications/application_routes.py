from flask import Blueprint, jsonify, request, current_app
from mysql.connector import Error

from backend.db_connection import get_db

applications_bp = Blueprint("applications", __name__)
APPLICATION_STATUSES = {"pending", "approved", "waitlisted", "rejected"}


@applications_bp.route("/applications", methods=["GET"])
def get_applications():
    """Return applications, optionally filtered by ?status=<value>."""
    status_filter = request.args.get("status")
    cursor = get_db().cursor(dictionary=True)
    try:
        if status_filter:
            query = """
                SELECT pa.application_id,
                       pa.user_id,
                       CONCAT(u.first_name, ' ', u.last_name) AS name,
                       pa.plot_id,
                       p.name AS plot_name,
                       pa.requested_date,
                       pa.status
                FROM Plot_Application pa
                JOIN  User u ON u.user_id  = pa.user_id
                LEFT JOIN Plot p ON p.plot_id = pa.plot_id
                WHERE pa.status = %s
                ORDER BY pa.requested_date ASC
            """
            cursor.execute(query, (status_filter,))
        else:
            query = """
                SELECT pa.application_id,
                       pa.user_id,
                       CONCAT(u.first_name, ' ', u.last_name) AS name,
                       pa.plot_id,
                       p.name AS plot_name,
                       pa.requested_date,
                       pa.status
                FROM Plot_Application pa
                JOIN  User u ON u.user_id  = pa.user_id
                LEFT JOIN Plot p ON p.plot_id = pa.plot_id
                ORDER BY pa.requested_date ASC
            """
            cursor.execute(query)
        return jsonify(cursor.fetchall()), 200
    except Error as e:
        current_app.logger.error(f"Error fetching applications: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


@applications_bp.route("/applications/<int:application_id>", methods=["PUT"])
def update_application(application_id):
    """Update the status of a plot application (approved / waitlisted / rejected)."""
    cursor = get_db().cursor()
    try:
        data = request.get_json() or {}
        status = data.get("status")
        if not status:
            return jsonify({"error": "Missing required field: status"}), 400
        if status not in APPLICATION_STATUSES:
            valid = ", ".join(sorted(APPLICATION_STATUSES))
            return jsonify({"error": f"Invalid status. Allowed: {valid}"}), 400

        cursor.execute(
            "UPDATE Plot_Application SET status = %s WHERE application_id = %s",
            (status, application_id),
        )
        if cursor.rowcount == 0:
            return jsonify({"error": "Application not found"}), 404
        get_db().commit()
        return jsonify({"message": "Application status updated"}), 200
    except Error as e:
        current_app.logger.error(f"Error updating application: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


@applications_bp.route("/waitlist", methods=["GET"])
def get_waitlist():
    """Return all waitlisted plot applications ordered by request date."""
    cursor = get_db().cursor(dictionary=True)
    try:
        query = """
            SELECT pa.application_id,
                   pa.user_id,
                   CONCAT(u.first_name, ' ', u.last_name) AS name,
                   pa.plot_id,
                   p.name AS plot_name,
                   pa.requested_date
            FROM Plot_Application pa
            JOIN  User u ON u.user_id  = pa.user_id
            LEFT JOIN Plot p ON p.plot_id = pa.plot_id
            WHERE pa.status = 'waitlisted'
            ORDER BY pa.requested_date ASC
        """
        cursor.execute(query)
        return jsonify(cursor.fetchall()), 200
    except Error as e:
        current_app.logger.error(f"Error fetching waitlist: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


@applications_bp.route("/waitlist/<int:application_id>/promote", methods=["PUT"])
def promote_from_waitlist(application_id):
    """Promote a waitlisted applicant: create a Plot_Assignment and mark approved.

    If no specific plot was requested, the first vacant plot is used.
    """
    cursor = get_db().cursor(dictionary=True)
    try:
        cursor.execute(
            "SELECT * FROM Plot_Application WHERE application_id = %s AND status = 'waitlisted'",
            (application_id,),
        )
        app = cursor.fetchone()
        if not app:
            return jsonify({"error": "Waitlisted application not found"}), 404

        plot_id = app["plot_id"]
        user_id = app["user_id"]

        # If no specific plot was requested, find any currently vacant one
        if not plot_id:
            cursor.execute("""
                SELECT p.plot_id
                FROM Plot p
                LEFT JOIN Plot_Assignment pa
                    ON pa.plot_id = p.plot_id AND pa.end_date IS NULL
                WHERE pa.assignment_id IS NULL
                LIMIT 1
            """)
            row = cursor.fetchone()
            if not row:
                return (
                    jsonify({"error": "No vacant plots available for promotion"}),
                    409,
                )
            plot_id = row["plot_id"]

        # Guard: make sure the target plot is still vacant
        cursor.execute(
            "SELECT assignment_id FROM Plot_Assignment WHERE plot_id = %s AND end_date IS NULL",
            (plot_id,),
        )
        if cursor.fetchone():
            return jsonify({"error": "Target plot is no longer vacant"}), 409

        # Switch to plain cursor for write operations
        cursor.close()
        cursor = get_db().cursor()

        cursor.execute(
            "INSERT INTO Plot_Assignment (plot_id, user_id, assigned_date) VALUES (%s, %s, CURDATE())",
            (plot_id, user_id),
        )
        assignment_id = cursor.lastrowid

        cursor.execute(
            "UPDATE Plot_Application SET status = 'approved' WHERE application_id = %s",
            (application_id,),
        )
        get_db().commit()
        return (
            jsonify(
                {
                    "message": "Applicant promoted to plot owner",
                    "assignment_id": assignment_id,
                    "plot_id": plot_id,
                }
            ),
            200,
        )
    except Error as e:
        current_app.logger.error(f"Error promoting from waitlist: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
