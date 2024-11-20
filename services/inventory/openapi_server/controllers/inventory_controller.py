import traceback
import connexion
from typing import Dict
from typing import Tuple
from typing import Union
from flask import current_app, session, jsonify
import logging
import requests

from openapi_server.models.inventory_item import InventoryItem  # noqa: E501
from openapi_server import util
from pybreaker import CircuitBreaker, CircuitBreakerError

# Circuit breaker instance for inventory operations
circuit_breaker = CircuitBreaker(fail_max=5, reset_timeout=5, exclude=[requests.HTTPError])

def health_check():  # noqa: E501
    return jsonify({"message": "Service operational."}), 200

@circuit_breaker
def get_inventory():  # noqa: E501
    user_uuid = session.get("uuid")
    if not user_uuid:
        return jsonify({"error": "Not logged in"}), 403
    
    try:
        mysql = current_app.extensions.get('mysql')

        # Pagination parameters
        items_per_page = 10
        page_number = connexion.request.args.get('page_number', default=1, type=int)
        offset = (page - 1) * items_per_page

        try:
            conn = mysql.connect()
            cursor = conn.cursor()

            # # /db_manager/inventory/get_user_inventory_items
            cursor.execute('''
                SELECT 
                    BIN_TO_UUID(item_uuid),
                    BIN_TO_UUID(owner_uuid),
                    BIN_TO_UUID(stand_uuid),
                    obtained_at
                FROM inventories
                WHERE owner_uuid = UUID_TO_BIN(%s)
                LIMIT %s OFFSET %s
            ''', (user_uuid, items_per_page, page_number))
            
            inventory_items = []
            for row in cursor.fetchall():
                item = InventoryItem(
                    item_id=row[0],
                    owner_id=row[1],
                    gacha_uuid=row[2],
                    obtained_date=row[3]
                )
                inventory_items.append(item)
            
            return jsonify(inventory_items), 200

        except Exception as e:
            logging.error(f"Database error: {str(e)}")
            return jsonify({"error": "Database error"}), 500

    except Exception as e:
        logging.error(f"Server error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@circuit_breaker
def get_inventory_item_info(inventory_item_id):  # noqa: E501
    try:
        # Get database connection
        mysql = current_app.extensions.get('mysql')
            
        conn = mysql.connect()
        cursor = conn.cursor()

        # Get username from session
        user_uuid = session.get('uuid')
        if not user_uuid:
            return jsonify({"error": "Not logged in"}), 403

        # Query to get inventory item details, ensuring the item belongs to the logged in user
        # /db_manager/inventory/get_user_item_info
        cursor.execute('''
            SELECT 
                BIN_TO_UUID(item_uuid) as item_id,
                BIN_TO_UUID(owner_uuid) as owner_id,
                BIN_TO_UUID(stand_uuid) as gacha_uuid,
                obtained_at,
                owners_no,
                currency_spent
            FROM inventories
            WHERE owner_uuid = UUID_TO_BIN(%s) 
            AND item_uuid = UUID_TO_BIN(%s)
        ''', (user_uuid, inventory_item_id))

        row = cursor.fetchone()
        if not row:
            return jsonify({"error": "Item not found in player's inventory."}), 404

        # Create InventoryItem object with the fetched data
        item = InventoryItem(
            item_id=row[0],
            owner_id=row[1],
            gacha_uuid=row[2],
            obtained_date=row[3],
            owners_no=row[4],
            price_paid=row[5]
        )


        # Return single item wrapped in a list as per API spec
        return jsonify([item.to_dict()]), 200

    except Exception as e:
        logging.error(f"Error in get_inventory_item_info: {str(e)}\n{traceback.format_exc()}")
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500

@circuit_breaker
def remove_inventory_item():
    try:
        # Get item_id from request args
        item_id = connexion.request.args.get('inventory_item_id')
        if not item_id:
            return jsonify({"error": "Missing inventory_item_id parameter"}), 400

        mysql = current_app.extensions.get('mysql')
        if not mysql:
            return jsonify({"error": "Database connection not initialized"}), 500
            
        user_uuid = session.get('uuid')
        if not user_uuid:
            return jsonify({"error": "Not logged in"}), 403

        conn = mysql.connect()
        cursor = conn.cursor()

        # Then check if item is not in any active auction
        # /db_manager/inventory/remove_user_item
        cursor.execute('''
            SELECT 1 FROM auctions 
            WHERE item_uuid = UUID_TO_BIN(%s)
            AND end_time > NOW()
        ''', (item_id,))

        if cursor.fetchone():
            return jsonify({"error": "Cannot remove item that is in an active auction."}), 409

        # Delete the item
        cursor.execute('''
            DELETE FROM inventories 
            WHERE item_uuid = UUID_TO_BIN(%s)
            AND owner_uuid = UUID_TO_BIN(%s)
        ''', (item_id, user_uuid))

        if cursor.rowcount == 0:
            conn.rollback()
            return jsonify({"error": "Failed to remove item"}), 500

        conn.commit()
        return jsonify({"message": "Item successfully removed"}), 200
    
    except Exception as e:
        if conn:
            conn.rollback()
        logging.error(f"Error in remove_inventory_item: {str(e)}\n{traceback.format_exc()}")
        return jsonify({"error": "Internal server error"}), 500