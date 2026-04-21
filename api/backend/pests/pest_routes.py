from flask import Blueprint, jsonify, request, current_app
from mysql.connector import Error

from backend.db_connection import get_db

pests_bp = Blueprint("pests", __name__)
PEST_STATUSES = {"open", "in progress", "resolved"}


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
