from flask import Blueprint, jsonify, request, current_app
from mysql.connector import Error

from backend.db_connection import get_db

pests_bp = Blueprint("pests", __name__)
PEST_STATUSES = {"open", "in progress", "resolved"}
PEST_SEVERITIES = {"low", "medium", "high", "critical"}


@pests_bp.route("/pest-reports", methods=["GET"])
def get_pest_reports():
    """Return open and in-progress pest reports sorted by severity."""
    cursor = get_db().cursor(dictionary=True)
    try:
        query = """
			SELECT report_id, plot_id, crop_id, user_id, description, severity, date_reported, status
			FROM Pest_Report
            WHERE status IN ('open', 'in progress')
			ORDER BY FIELD(LOWER(severity), 'critical', 'high', 'medium', 'low'), date_reported DESC
		"""
        cursor.execute(query)
        return jsonify(cursor.fetchall()), 200
    except Error as e:
        current_app.logger.error(f"Error fetching pest reports: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


@pests_bp.route("/pest-reports", methods=["POST"])
def create_pest_report():
    """Submit a new pest or disease report from a plot owner."""
    cursor = get_db().cursor()
    try:
        data = request.get_json() or {}
        required = ["plot_id", "user_id", "description", "severity"]
        missing = [field for field in required if field not in data]
        if missing:
            return (
                jsonify({"error": f"Missing required fields: {', '.join(missing)}"}),
                400,
            )

        severity = data["severity"]
        if severity not in PEST_SEVERITIES:
            valid = ", ".join(sorted(PEST_SEVERITIES))
            return jsonify({"error": f"Invalid severity. Allowed: {valid}"}), 400

        query = """
            INSERT INTO Pest_Report (plot_id, crop_id, user_id, description,
                                     severity, date_reported, status)
            VALUES (%s, %s, %s, %s, %s, CURDATE(), 'open')
        """
        cursor.execute(
            query,
            (
                data["plot_id"],
                data.get("crop_id"),
                data["user_id"],
                data["description"],
                severity,
            ),
        )
        get_db().commit()
        return (
            jsonify(
                {"message": "Pest report submitted", "report_id": cursor.lastrowid}
            ),
            201,
        )
    except Error as e:
        current_app.logger.error(f"Error creating pest report: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


@pests_bp.route("/pest-reports/<int:report_id>", methods=["PUT"])
def update_pest_report_status(report_id):
    cursor = get_db().cursor()
    try:
        data = request.get_json() or {}
        status = data.get("status")
        if not status:
            return jsonify({"error": "Missing required field: status"}), 400
        if status not in PEST_STATUSES:
            valid = ", ".join(sorted(PEST_STATUSES))
            return jsonify({"error": f"Invalid status. Allowed values: {valid}"}), 400

        query = "UPDATE Pest_Report SET status = %s WHERE report_id = %s"
        cursor.execute(query, (status, report_id))
        if cursor.rowcount == 0:
            return jsonify({"error": "Pest report not found"}), 404

        get_db().commit()
        return jsonify({"message": "Pest report status updated"}), 200
    except Error as e:
        current_app.logger.error(f"Error updating pest report: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
