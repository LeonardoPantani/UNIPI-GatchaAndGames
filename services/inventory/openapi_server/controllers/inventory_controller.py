import traceback
import connexion
from typing import Dict
from typing import Tuple
from typing import Union
from flask import current_app, session, jsonify
import logging

from openapi_server.models.inventory_item import InventoryItem  # noqa: E501
from openapi_server import util

def health_check():  # noqa: E501
    return jsonify({"message": "Service operational."}), 200

def get_inventory():  # noqa: E501
    """Retrieve player's inventory with pagination"""
    try:
        mysql = current_app.extensions.get('mysql')
        if not mysql:
            return jsonify({"error": "Database connection not initialized"}), 500
            
        username = session.get('username')
        if not username:
            return jsonify({"error": "Not logged in"}), 403

        # Pagination parameters
        items_per_page = 10
        page = connexion.request.args.get('page', default=1, type=int)
        offset = (page - 1) * items_per_page

        try:
            conn = mysql.connect()
            cursor = conn.cursor()

            # First get total count
            cursor.execute('''
                SELECT COUNT(*) 
                FROM inventories i
                JOIN profiles p ON i.owner_uuid = p.uuid 
                WHERE p.username = %s
            ''', (username,))
            total_items = cursor.fetchone()[0]

            # Then get paginated results
            cursor.execute('''
                SELECT 
                    BIN_TO_UUID(i.item_uuid) as item_id,
                    BIN_TO_UUID(i.owner_uuid) as owner_id,
                    BIN_TO_UUID(i.stand_uuid) as gacha_uuid,
                    i.obtained_at
                FROM inventories i
                JOIN profiles p ON i.owner_uuid = p.uuid 
                WHERE p.username = %s
                LIMIT %s OFFSET %s
            ''', (username, items_per_page, offset))
            
            inventory_items = []
            for row in cursor.fetchall():
                item = InventoryItem(
                    item_id=row[0],
                    owner_id=row[1],
                    gacha_uuid=row[2],
                    obtained_date=row[3]  # Changed from obtained_at to obtained_date
                )
                inventory_items.append(item)

            # Prepare pagination metadata
            total_pages = (total_items + items_per_page - 1) // items_per_page
            
            return jsonify({
                "items": [item.to_dict() for item in inventory_items],
                "pagination": {
                    "current_page": page,
                    "total_pages": total_pages,
                    "total_items": total_items,
                    "items_per_page": items_per_page
                }
            })

        except Exception as e:
            logging.error(f"Database error: {str(e)}")
            return jsonify({"error": "Database error"}), 500

        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    except Exception as e:
        logging.error(f"Server error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


def get_inventory_item_info(inventory_item_id):  # noqa: E501
    """Shows infos on my inventory item.

    Returns infos on my inventory item. # noqa: E501

    :param inventory_item_id: UUID of the inventory item
    :type inventory_item_id: str
    :rtype: Union[List[InventoryItem], Tuple[List[InventoryItem], int], Tuple[List[InventoryItem], int, Dict[str, str]]
    """
    try:
        # Get database connection
        mysql = current_app.extensions.get('mysql')
        if not mysql:
            return jsonify({"error": "Database connection not initialized"}), 500
            
        conn = mysql.connect()
        cursor = conn.cursor()

        # Get username from session
        username = session.get('username')
        if not username:
            cursor.close()
            conn.close() 
            return jsonify({"error": "Not logged in"}), 403

        # Query to get inventory item details, ensuring the item belongs to the logged in user
        cursor.execute('''
            SELECT 
                BIN_TO_UUID(i.item_uuid) as item_id,
                BIN_TO_UUID(i.owner_uuid) as owner_id,
                BIN_TO_UUID(i.stand_uuid) as gacha_uuid,
                i.obtained_at,
                i.owners_no,
                i.currency_spent
            FROM inventories i
            JOIN profiles p ON i.owner_uuid = p.uuid
            WHERE p.username = %s 
            AND i.item_uuid = UUID_TO_BIN(%s)
        ''', (username, inventory_item_id))

        row = cursor.fetchone()
        if not row:
            cursor.close()
            conn.close()
            return jsonify({"error": "Item not found or does not belong to you"}), 404

        # Create InventoryItem object with the fetched data
        item = InventoryItem(
            item_id=InventoryItemId(owner_id=row[1], item_id=row[0]),
            gacha_uuid=row[2],
            obtained_date=row[3],
            owners_no=row[4],
            price_paid=row[5]
        )

        cursor.close()
        conn.close()

        # Return single item wrapped in a list as per API spec
        return jsonify([item.to_dict()]), 200

    except Exception as e:
        logging.error(f"Error in get_inventory_item_info: {str(e)}\n{traceback.format_exc()}")
        if cursor:
            cursor.close()
        if conn:
            conn.close()
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500


def remove_inventory_item():
    """Removes an item from player's inventory
    
    :param item_id: UUID of the inventory item to remove
    :type item_id: str
    :rtype: Union[Dict[str, str], Tuple[Dict[str, str], int]]
    """
    cursor = None
    conn = None
    try:
        # Get item_id from request args
        item_id = connexion.request.args.get('inventory_item_id')
        if not item_id:
            return jsonify({"error": "Missing inventory_item_id parameter"}), 400

        mysql = current_app.extensions.get('mysql')
        if not mysql:
            return jsonify({"error": "Database connection not initialized"}), 500
            
        username = session.get('username')
        if not username:
            return jsonify({"error": "Not logged in"}), 403

        conn = mysql.connect()
        cursor = conn.cursor()

        # First verify item exists and belongs to user
        cursor.execute('''
            SELECT BIN_TO_UUID(i.item_uuid)
            FROM inventories i
            JOIN profiles p ON i.owner_uuid = p.uuid
            WHERE p.username = %s 
            AND i.item_uuid = UUID_TO_BIN(%s)
        ''', (username, item_id))

        if not cursor.fetchone():
            return jsonify({"error": "Item not found or does not belong to you"}), 404

        # Then check if item is not in any active auction
        cursor.execute('''
            SELECT 1 FROM auctions 
            WHERE item_uuid = UUID_TO_BIN(%s)
            AND end_time > NOW()
        ''', (item_id,))

        if cursor.fetchone():
            return jsonify({"error": "Cannot remove item that is in an active auction"}), 400

        # If all checks pass, delete the item
        cursor.execute('''
            DELETE FROM inventories 
            WHERE item_uuid = UUID_TO_BIN(%s)
            AND owner_uuid = (
                SELECT uuid FROM profiles WHERE username = %s
            )
        ''', (item_id, username))

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

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
