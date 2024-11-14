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
    """Retrieve player's inventory"""
    try:
        # Get database connection
        mysql = current_app.extensions.get('mysql')
        logging.info("Got mysql extension")
        
        if not mysql:
            return jsonify({"error": "Database connection not initialized"}), 500
            
        conn = mysql.connect()
        logging.info("Connected to database") 
        
        cursor = conn.cursor()
        logging.info("Created cursor")

        # Get username from session
        username = session.get('username')
        logging.info(f"Got username from session: {username}")
        
        if not username:
            cursor.close()
            conn.close()
            return jsonify({"error": "Not logged in"}), 403

        # Get items from inventory with pagination
        items_per_page = 10
        page_number = connexion.request.args.get('page', default=1, type=int)
        offset = (page_number - 1) * items_per_page if page_number else 0
        
        # Query joins inventories with gachas_types to get all item info
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
            LIMIT %s OFFSET %s
        ''', (username, items_per_page, offset))
        
        inventory_items = []
        for row in cursor.fetchall():
            item = InventoryItem(
                item_id=InventoryItemId(owner_id=row[1], item_id=row[0]),
                gacha_uuid=row[2],
                obtained_date=row[3],
                owners_no=row[4],
                price_paid=row[5]
            )
            inventory_items.append(item)

        cursor.close()
        conn.close()

        return jsonify([item.to_dict() for item in inventory_items]), 200

    except Exception as e:
        logging.error(f"Error in get_inventory: {str(e)}\n{traceback.format_exc()}")
        if cursor:
            cursor.close()
        if conn:
            conn.close()
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500


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


def remove_inventory_item(item_id):
    """Removes an item from player's inventory"""
    cursor = None
    conn = None
    try:
        mysql = current_app.extensions.get('mysql')
        if not mysql:
            return jsonify({"error": "Database connection not initialized"}), 500
            
        conn = mysql.connect()
        cursor = conn.cursor()
        username = session.get('username')
        if not username:
            return jsonify({"error": "Not logged in"}), 403

        # Detailed logging of input
        logging.info(f"Received item_id type: {type(item_id)}")
        logging.info(f"Received item_id content: {item_id}")

        # Parse item_id from request body 
        if isinstance(item_id, dict):
            # According to the OpenAPI spec, the request body should have this structure:
            # {
            #   "item_id": {
            #     "item_id": "uuid-here",
            #     "owner_id": "owner-uuid-here"
            #   }
            # }
            item_data = item_id.get('item_id', {})
            item_uuid = item_data.get('item_id')
            owner_uuid = item_data.get('owner_id')
            logging.info(f"Extracted from dict - item_uuid: {item_uuid}, owner_uuid: {owner_uuid}")
        else:
            # Handle InventoryItemId object
            logging.info("Handling as object") 
            try:
                item_uuid = item_id.item_id
                owner_uuid = item_id.owner_id
                logging.info(f"Extracted from object - item_uuid: {item_uuid}, owner_uuid: {owner_uuid}")
            except AttributeError as e:
                logging.error(f"AttributeError: {str(e)}")
                return jsonify({"error": "Invalid item_id format - missing required fields"}), 400

        if not item_uuid or not owner_uuid:
            logging.error(f"Missing required fields - item_uuid: {item_uuid}, owner_uuid: {owner_uuid}")
            return jsonify({"error": "Invalid item_id format - both item_id and owner_id required"}), 400

        cursor.execute('''
            DELETE i FROM inventories i
            JOIN profiles p ON i.owner_uuid = p.uuid
            WHERE p.username = %s
            AND i.item_uuid = UUID_TO_BIN(%s)
            AND i.owner_uuid = UUID_TO_BIN(%s)
        ''', (username, item_uuid, owner_uuid))

        if cursor.rowcount == 0:
            return jsonify({"error": "Item not found or does not belong to you"}), 404

        conn.commit()
        return jsonify({"message": "Item removed successfully"}), 200

    except Exception as e:
        logging.error(f"Error in remove_inventory_item: {str(e)}\n{traceback.format_exc()}")
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
