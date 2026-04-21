from flask import Blueprint, jsonify, request, current_app
from mysql.connector import Error

from backend.db_connection import get_db

workdays_bp = Blueprint("workdays", __name__)
TASK_STATUSES = {"pending", "in progress", "completed"}
SIGNUP_STATUSES = {"registered", "attended", "cancelled"}


@workdays_bp.route("/workdays", methods=["GET"])
def get_workdays():
    """Return upcoming workdays with signup counts and spots remaining."""
    cursor = get_db().cursor(dictionary=True)
    try:
        query = """
            SELECT
                w.workday_id,
                w.site_id,
                w.event_name,
                w.event_date,
                w.description,
                w.volunteers_needed,
                COUNT(es.signup_id) AS signup_count,
                GREATEST(w.volunteers_needed - COUNT(es.signup_id), 0) AS spots_remaining
            FROM Workday w
            LEFT JOIN Event_Signup es
                ON es.workday_id = w.workday_id
                AND es.status = 'registered'
            WHERE w.event_date >= CURDATE()
            GROUP BY w.workday_id
            ORDER BY w.event_date ASC
        """
        cursor.execute(query)
        return jsonify(cursor.fetchall()), 200
    except Error as e:
        current_app.logger.error(f"Error fetching workdays: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


@workdays_bp.route("/workdays", methods=["POST"])
def create_workday():
    cursor = get_db().cursor()
    try:
        data = request.get_json() or {}
        required = [
            "site_id",
            "event_name",
            "event_date",
            "description",
            "volunteers_needed",
        ]
        missing = [field for field in required if field not in data]
        if missing:
            return (
                jsonify({"error": f"Missing required fields: {', '.join(missing)}"}),
                400,
            )

        query = """
            INSERT INTO Workday (
                site_id, event_name, event_date, description,
                volunteers_needed, start_time, end_time
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(
            query,
            (
                data["site_id"],
                data["event_name"],
                data["event_date"],
                data["description"],
                data["volunteers_needed"],
                data.get("start_time"),
                data.get("end_time"),
            ),
        )
        get_db().commit()
        return (
            jsonify({"message": "Workday created", "workday_id": cursor.lastrowid}),
            201,
        )
    except Error as e:
        current_app.logger.error(f"Error creating workday: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


@workdays_bp.route("/workdays/<int:workday_id>", methods=["DELETE"])
def delete_workday(workday_id):
    """Hard-delete a workday and all dependent records.

    Manually cascades because the FK constraints lack ON DELETE CASCADE.
    Order: Volunteer_Log → Workday_Task → Event_Signup → Workday.
    """
    cursor = get_db().cursor()
    try:
        cursor.execute("SELECT workday_id FROM Workday WHERE workday_id = %s", (workday_id,))
        if not cursor.fetchone():
            return jsonify({"error": "Workday not found"}), 404

        # Collect task IDs so we can clean up Volunteer_Log entries
        cursor.execute(
            "SELECT task_id FROM Workday_Task WHERE workday_id = %s", (workday_id,)
        )
        task_ids = [row[0] for row in cursor.fetchall()]

        if task_ids:
            placeholders = ",".join(["%s"] * len(task_ids))
            cursor.execute(
                f"DELETE FROM Volunteer_Log WHERE task_id IN ({placeholders})", task_ids
            )

        cursor.execute("DELETE FROM Workday_Task  WHERE workday_id = %s", (workday_id,))
        cursor.execute("DELETE FROM Event_Signup  WHERE workday_id = %s", (workday_id,))
        cursor.execute("DELETE FROM Workday       WHERE workday_id = %s", (workday_id,))

        get_db().commit()
        return jsonify({"message": "Workday deleted"}), 200
    except Error as e:
        current_app.logger.error(f"Error deleting workday: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


@workdays_bp.route("/workdays/<int:workday_id>/tasks", methods=["GET"])
def get_workday_tasks(workday_id):
    """Return pending/in-progress tasks for a given workday."""
    cursor = get_db().cursor(dictionary=True)
    try:
        query = """
            SELECT task_id, workday_id, task_description, location_note, urgency, status
            FROM Workday_Task
            WHERE workday_id = %s AND status IN ('pending', 'in progress')
            ORDER BY task_id ASC
        """
        cursor.execute(query, (workday_id,))
        return jsonify(cursor.fetchall()), 200
    except Error as e:
        current_app.logger.error(f"Error fetching workday tasks: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


@workdays_bp.route("/workdays/<int:workday_id>/tasks", methods=["POST"])
def add_task_to_workday(workday_id):
    cursor = get_db().cursor()
    try:
        data = request.get_json() or {}
        if "task_description" not in data:
            return jsonify({"error": "Missing required field: task_description"}), 400

        status = data.get("status", "pending")
        if status not in TASK_STATUSES:
            valid = ", ".join(sorted(TASK_STATUSES))
            return jsonify({"error": f"Invalid status. Allowed values: {valid}"}), 400

        query = """
            INSERT INTO Workday_Task (workday_id, task_description, location_note, urgency, status)
            VALUES (%s, %s, %s, %s, %s)
        """
        cursor.execute(
            query,
            (
                workday_id,
                data["task_description"],
                data.get("location_note"),
                data.get("urgency"),
                status,
            ),
        )
        get_db().commit()
        return jsonify({"message": "Task created", "task_id": cursor.lastrowid}), 201
    except Error as e:
        current_app.logger.error(f"Error creating workday task: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


@workdays_bp.route("/workdays/<int:workday_id>/tasks", methods=["PUT"])
def update_task_status(workday_id):
    """Update a task status on a workday using task_id + status in the body."""
    cursor = get_db().cursor()
    try:
        data = request.get_json() or {}
        task_id = data.get("task_id")
        status = data.get("status")
        if not task_id or not status:
            return jsonify({"error": "task_id and status are required"}), 400
        if status not in TASK_STATUSES:
            valid = ", ".join(sorted(TASK_STATUSES))
            return jsonify({"error": f"Invalid status. Allowed values: {valid}"}), 400

        query = """
            UPDATE Workday_Task
            SET status = %s
            WHERE task_id = %s AND workday_id = %s
        """
        cursor.execute(query, (status, task_id, workday_id))
        if cursor.rowcount == 0:
            return jsonify({"error": "Task not found for workday"}), 404

        get_db().commit()
        return jsonify({"message": "Task status updated"}), 200
    except Error as e:
        current_app.logger.error(f"Error updating task status: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


@workdays_bp.route("/workdays/<int:workday_id>/signups", methods=["POST"])
def create_workday_signup(workday_id):
    cursor = get_db().cursor()
    try:
        data = request.get_json() or {}
        if "user_id" not in data:
            return jsonify({"error": "Missing required field: user_id"}), 400

        signup_status = data.get("status", "registered")
        if signup_status not in SIGNUP_STATUSES:
            valid = ", ".join(sorted(SIGNUP_STATUSES))
            return jsonify({"error": f"Invalid status. Allowed values: {valid}"}), 400

        query = """
            INSERT INTO Event_Signup (user_id, workday_id, signup_date, status)
            VALUES (%s, %s, CURDATE(), %s)
        """
        cursor.execute(query, (data["user_id"], workday_id, signup_status))
        get_db().commit()
        return (
            jsonify({"message": "Signup created", "signup_id": cursor.lastrowid}),
            201,
        )
    except Error as e:
        current_app.logger.error(f"Error creating signup: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


@workdays_bp.route("/signups/<int:signup_id>", methods=["DELETE"])
def cancel_signup(signup_id):
    """Cancel a signup by marking it cancelled."""
    cursor = get_db().cursor()
    try:
        query = "UPDATE Event_Signup SET status = 'cancelled' WHERE signup_id = %s"
        cursor.execute(query, (signup_id,))
        if cursor.rowcount == 0:
            return jsonify({"error": "Signup not found"}), 404

        get_db().commit()
        return jsonify({"message": "Signup cancelled"}), 200
    except Error as e:
        current_app.logger.error(f"Error cancelling signup: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
