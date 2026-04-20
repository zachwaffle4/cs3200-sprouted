from flask import Blueprint, jsonify, request, current_app
from mysql.connector import Error

from backend.db_connection import get_db

analytics_bp = Blueprint("analytics", __name__)


def _validate_org_id():
    org_id = request.args.get("org_id", type=int)
    if org_id is None:
        return None, (jsonify({"error": "org_id query parameter is required"}), 400)
    return org_id, None


@analytics_bp.route("/analytics/donations-by-month", methods=["GET"])
def donations_by_month():
    cursor = get_db().cursor(dictionary=True)
    try:
        org_id, error_response = _validate_org_id()
        if error_response:
            return error_response

        start_date = request.args.get("start_date")
        end_date = request.args.get("end_date")

        query = """
            SELECT
                DATE_FORMAT(pu.pickup_date, '%Y-%m') AS month,
                c.crop_type,
                ROUND(SUM(pu.qty_received_lbs), 2) AS total_lbs
            FROM Produce_Request pr
            JOIN Pickup pu ON pu.request_id = pr.request_id
            JOIN Surplus_Listing sl ON sl.listing_id = pr.listing_id
            JOIN Crop c ON c.crop_id = sl.crop_id
            WHERE pr.org_id = %s
        """
        params = [org_id]

        if start_date:
            query += " AND pu.pickup_date >= %s"
            params.append(start_date)
        if end_date:
            query += " AND pu.pickup_date <= %s"
            params.append(end_date)

        query += " GROUP BY DATE_FORMAT(pu.pickup_date, '%Y-%m'), c.crop_type ORDER BY month ASC"

        cursor.execute(query, tuple(params))
        return jsonify(cursor.fetchall()), 200
    except Error as e:
        current_app.logger.error(f"Error fetching donation analytics: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


@analytics_bp.route("/analytics/top-sites", methods=["GET"])
def top_sites():
    cursor = get_db().cursor(dictionary=True)
    try:
        org_id, error_response = _validate_org_id()
        if error_response:
            return error_response

        start_date = request.args.get("start_date")
        end_date = request.args.get("end_date")

        query = """
            SELECT
                gs.site_id,
                gs.site_name,
                ROUND(SUM(pu.qty_received_lbs), 2) AS total_contributed_lbs
            FROM Produce_Request pr
            JOIN Pickup pu ON pu.request_id = pr.request_id
            JOIN Surplus_Listing sl ON sl.listing_id = pr.listing_id
            JOIN Plot p ON p.plot_id = sl.plot_id
            JOIN Garden_Site gs ON gs.site_id = p.site_id
            WHERE pr.org_id = %s
        """
        params = [org_id]

        if start_date:
            query += " AND pu.pickup_date >= %s"
            params.append(start_date)
        if end_date:
            query += " AND pu.pickup_date <= %s"
            params.append(end_date)

        query += (
            " GROUP BY gs.site_id, gs.site_name ORDER BY total_contributed_lbs DESC"
        )

        cursor.execute(query, tuple(params))
        return jsonify(cursor.fetchall()), 200
    except Error as e:
        current_app.logger.error(f"Error fetching top sites analytics: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
