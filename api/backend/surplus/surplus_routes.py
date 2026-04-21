from flask import Blueprint, jsonify, request, current_app
from mysql.connector import Error

from backend.db_connection import get_db

surplus_bp = Blueprint("surplus", __name__)


@surplus_bp.route("/surplus", methods=["GET"])
def get_surplus_listings():
    """Browse available surplus listings with optional filters."""
    cursor = get_db().cursor(dictionary=True)
    try:
        crop_type = request.args.get("crop_type")
        min_quantity = request.args.get("min_quantity", type=float)

        query = """
            SELECT
                sl.listing_id,
                sl.quantity_lbs,
                sl.listed_date,
                sl.freshness_note,
                sl.status,
                c.crop_name,
                c.crop_type,
                p.plot_id,
                p.name AS plot_name,
                gs.site_id,
                gs.site_name
            FROM Surplus_Listing sl
            JOIN Crop c ON c.crop_id = sl.crop_id
            JOIN Plot p ON p.plot_id = sl.plot_id
            JOIN Garden_Site gs ON gs.site_id = p.site_id
            WHERE sl.status = 'available'
        """
        params = []
        if crop_type:
            query += " AND c.crop_type = %s"
            params.append(crop_type)
        if min_quantity is not None:
            query += " AND sl.quantity_lbs >= %s"
            params.append(min_quantity)

        query += " ORDER BY sl.listed_date DESC"
        cursor.execute(query, tuple(params))
        return jsonify(cursor.fetchall()), 200
    except Error as e:
        current_app.logger.error(f"Error fetching surplus listings: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


@surplus_bp.route("/surplus", methods=["POST"])
def create_surplus_listing():
    """Create a new surplus listing from a plot owner."""
    cursor = get_db().cursor()
    try:
        data = request.get_json() or {}
        required = ["plot_id", "crop_id", "quantity_lbs"]
        missing = [field for field in required if field not in data]
        if missing:
            return (
                jsonify({"error": f"Missing required fields: {', '.join(missing)}"}),
                400,
            )

        query = """
            INSERT INTO Surplus_Listing (plot_id, crop_id, quantity_lbs,
                                         listed_date, freshness_note, status)
            VALUES (%s, %s, %s, CURDATE(), %s, 'available')
        """
        cursor.execute(
            query,
            (
                data["plot_id"],
                data["crop_id"],
                data["quantity_lbs"],
                data.get("freshness_note"),
            ),
        )
        get_db().commit()
        return (
            jsonify(
                {"message": "Surplus listing created", "listing_id": cursor.lastrowid}
            ),
            201,
        )
    except Error as e:
        current_app.logger.error(f"Error creating surplus listing: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


@surplus_bp.route("/surplus/requests", methods=["POST"])
def create_pickup_request():
    cursor = get_db().cursor()
    try:
        data = request.get_json() or {}
        required = ["org_id", "listing_id", "preferred_pickup_date"]
        missing = [field for field in required if field not in data]
        if missing:
            return (
                jsonify({"error": f"Missing required fields: {', '.join(missing)}"}),
                400,
            )

        query = """
            INSERT INTO Produce_Request (
                org_id,
                listing_id,
                requested_date,
                preferred_pickup_date,
                status
            )
            VALUES (%s, %s, CURDATE(), %s, 'pending')
        """
        cursor.execute(
            query, (data["org_id"], data["listing_id"], data["preferred_pickup_date"])
        )
        get_db().commit()
        return (
            jsonify(
                {"message": "Pickup request submitted", "request_id": cursor.lastrowid}
            ),
            201,
        )
    except Error as e:
        current_app.logger.error(f"Error creating pickup request: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


@surplus_bp.route("/surplus/requests/<int:request_id>", methods=["DELETE"])
def cancel_pickup_request(request_id):
    cursor = get_db().cursor()
    try:
        query = """
            UPDATE Produce_Request
            SET status = 'denied'
            WHERE request_id = %s AND status = 'pending'
        """
        cursor.execute(query, (request_id,))
        if cursor.rowcount == 0:
            return jsonify({"error": "Pending request not found"}), 404

        get_db().commit()
        return jsonify({"message": "Pickup request cancelled"}), 200
    except Error as e:
        current_app.logger.error(f"Error cancelling pickup request: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()


@surplus_bp.route("/surplus/requests", methods=["GET"])
def get_pickup_requests():
    """Return all pickup requests with crop and site info."""
    cursor = get_db().cursor(dictionary=True)
    try:
        query = """
            SELECT
                pr.request_id,
                pr.org_id,
                pr.listing_id,
                pr.requested_date,
                pr.preferred_pickup_date,
                pr.status,
                c.crop_name,
                c.crop_type,
                sl.quantity_lbs,
                p.name AS plot_name,
                gs.site_name
            FROM Produce_Request pr
            JOIN Surplus_Listing sl ON sl.listing_id = pr.listing_id
            JOIN Crop c ON c.crop_id = sl.crop_id
            JOIN Plot p ON p.plot_id = sl.plot_id
            JOIN Garden_Site gs ON gs.site_id = p.site_id
            ORDER BY pr.requested_date DESC
        """
        cursor.execute(query)
        return jsonify(cursor.fetchall()), 200
    except Error as e:
        current_app.logger.error(f"Error fetching pickup requests: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
