from flask import Blueprint, jsonify, request, current_app
from mysql.connector import Error

from backend.db_connection import get_db

volunteers_bp = Blueprint("volunteers", __name__)


@volunteers_bp.route("/volunteers/<int:user_id>/log", methods=["GET"])
def get_volunteer_log(user_id):
    """Return a volunteer's work log with task and workday context."""
    cursor = get_db().cursor(dictionary=True)
    try:
        query = """
            SELECT
                vl.log_id,
                vl.user_id,
                vl.work_date,
                vl.hours_logged,
                vl.notes,
                wt.task_description,
                w.event_name,
                w.event_date
            FROM Volunteer_Log vl
            LEFT JOIN Workday_Task wt ON wt.task_id = vl.task_id
            LEFT JOIN Workday w ON w.workday_id = wt.workday_id
            WHERE vl.user_id = %s
            ORDER BY vl.work_date DESC, vl.log_id DESC
        """
        cursor.execute(query, (user_id,))
        return jsonify(cursor.fetchall()), 200
    except Error as e:
        current_app.logger.error(f"Error fetching volunteer log: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


@volunteers_bp.route("/volunteers/<int:user_id>/log", methods=["POST"])
def create_volunteer_log(user_id):
    """Log volunteer hours; if task_id is provided, enforce completed-task logging."""
    cursor = get_db().cursor()
    try:
        data = request.get_json() or {}
        required = ["work_date", "hours_logged"]
        missing = [field for field in required if field not in data]
        if missing:
            return (
                jsonify({"error": f"Missing required fields: {', '.join(missing)}"}),
                400,
            )

        task_id = data.get("task_id")
        if task_id is not None:
            cursor.execute(
                "SELECT status FROM Workday_Task WHERE task_id = %s", (task_id,)
            )
            row = cursor.fetchone()
            if row is None:
                return jsonify({"error": "task_id not found"}), 404
            if row[0] != "completed":
                return jsonify({"error": "Can only log hours for completed tasks"}), 400

        query = """
            INSERT INTO Volunteer_Log (user_id, task_id, work_date, hours_logged, notes)
            VALUES (%s, %s, %s, %s, %s)
        """
        cursor.execute(
            query,
            (
                user_id,
                task_id,
                data["work_date"],
                data["hours_logged"],
                data.get("notes"),
            ),
        )
        get_db().commit()
        return (
            jsonify({"message": "Volunteer log created", "log_id": cursor.lastrowid}),
            201,
        )
    except Error as e:
        current_app.logger.error(f"Error creating volunteer log: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
