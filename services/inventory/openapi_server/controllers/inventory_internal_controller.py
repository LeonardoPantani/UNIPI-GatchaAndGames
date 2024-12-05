import connexion
from flask import jsonify
from mysql.connector.errors import (
    DatabaseError,
    DataError,
    IntegrityError,
    InterfaceError,
    InternalError,
    OperationalError,
    ProgrammingError,
)
from pybreaker import CircuitBreaker, CircuitBreakerError

from openapi_server.helpers.authorization import verify_login
from openapi_server.helpers.db import get_db
from openapi_server.helpers.logging import send_log
from openapi_server.models.check_owner_of_team_request import (
    CheckOwnerOfTeamRequest,
)
from openapi_server.models.exists_inventory200_response import (
    ExistsInventory200Response,
)
from openapi_server.models.inventory_item import InventoryItem

SERVICE_TYPE="inventory"
circuit_breaker = CircuitBreaker(fail_max=5, reset_timeout=5)

def check_owner_of_team(check_owner_of_team_request=None, session=None, user_uuid=None):
    """Checks if a team is actually owned by the user."""
   
    if not connexion.request.is_json:
        return jsonify({"message": "Invalid request."}), 400
    
    check_owner_of_team_request = CheckOwnerOfTeamRequest.from_dict(connexion.request.get_json())

    try:
        @circuit_breaker
        def verify_team_ownership():
            connection = get_db()
            cursor = connection.cursor()
            
            team_uuids = tuple(check_owner_of_team_request.team)
            expected_count = len(team_uuids)
            
            # Query to check if all items in team belong to user
            query = """
            SELECT COUNT(DISTINCT item_uuid) 
            FROM inventories 
            WHERE BIN_TO_UUID(owner_uuid) = %s 
            AND BIN_TO_UUID(item_uuid) IN ({})
            HAVING COUNT(DISTINCT item_uuid) = %s
            """.format(','.join(['%s'] * len(team_uuids)))

            cursor.execute(query, (user_uuid, *team_uuids, expected_count))
            result = cursor.fetchone()
            
            cursor.close()
            return result is not None and result[0] == expected_count

        items_owned = verify_team_ownership()
        
        if not items_owned:
            return jsonify({"error": "Items not found in user inventory."}), 404
            
        return jsonify({"message": "Items verified."}), 200

    except (OperationalError, DataError, ProgrammingError, IntegrityError, InternalError, InterfaceError, DatabaseError) as e:
        send_log(f"Query: {type(e).__name__} ({e})", level="error", service_type=SERVICE_TYPE)
        return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503
    except CircuitBreakerError:
        send_log(f"Inventory_Internal: Circuit breaker is open.", level="warning", service_type=SERVICE_TYPE)
        return "", 503


def delete_by_stand_uuid(session=None, uuid=None):
    """Deletes items which are a certain stand."""

    if not uuid:
        return jsonify({"error": "Invalid request."}), 404

    try:
        @circuit_breaker
        def delete_stand_items():
            connection = get_db()
            cursor = connection.cursor()
            
            # Query to delete items with specified stand_uuid
            query = """
            DELETE FROM inventories 
            WHERE BIN_TO_UUID(stand_uuid) = %s
            """
            
            cursor.execute(query, (uuid,))
            connection.commit()
            affected_rows = cursor.rowcount
            
            cursor.close()
            return affected_rows > 0

        items_deleted = delete_stand_items()
        
        if not items_deleted:
            return jsonify({"error": "Items not found."}), 404
            
        return jsonify({"message": "Items deleted."}), 200

    except (OperationalError, DataError, ProgrammingError, IntegrityError, InternalError, InterfaceError, DatabaseError) as e:
        send_log(f"Query: {type(e).__name__} ({e})", level="error", service_type=SERVICE_TYPE)
        return jsonify({"error": "Service temporarily unavailable. Please try again later."}), 503
    except CircuitBreakerError:
        send_log(f"Inventory_Internal: Circuit breaker is open.", level="warning", service_type=SERVICE_TYPE)
        return "", 503


def delete_user_inventory(uuid=None, session=None):
    """Deletes items owned by user."""
    if not uuid or not isinstance(uuid, str):
        return "", 400  # Invalid request

    try:
        @circuit_breaker
        def delete_user_items():
            connection = get_db()
            cursor = connection.cursor()
            
            query = """
            DELETE FROM inventories 
            WHERE BIN_TO_UUID(owner_uuid) = %s
            """
            
            cursor.execute(query, (uuid,))
            connection.commit()
            affected_rows = cursor.rowcount
            
            cursor.close()
            return affected_rows > 0

        items_deleted = delete_user_items()
            
        return "", 200

    except (OperationalError, DataError, DatabaseError, IntegrityError, 
            InterfaceError, InternalError, ProgrammingError) as e:
        send_log(f"Query: {type(e).__name__} ({e})", level="error", service_type=SERVICE_TYPE)
        return "", 503
    except CircuitBreakerError:
        send_log(f"Inventory_Internal: Circuit breaker is open.", level="warning", service_type=SERVICE_TYPE)
        return "", 503


def exists_inventory(uuid=None, session=None):
    """Returns true if an item exists, false otherwise.

    """
    if not uuid or not isinstance(uuid, str):
        return "", 400  # Invalid request

    try:
        @circuit_breaker
        def check_item_exists():
            connection = get_db()
            cursor = connection.cursor()
            
            query = """
            SELECT COUNT(*) 
            FROM inventories 
            WHERE BIN_TO_UUID(item_uuid) = %s
            """
            
            cursor.execute(query, (uuid,))
            result = cursor.fetchone()
            
            cursor.close()
            return result[0] > 0

        exists = check_item_exists()
        response = ExistsInventory200Response(exists=exists)
        
        return jsonify(response), 200

    except (OperationalError, DataError, DatabaseError, IntegrityError, 
            InterfaceError, InternalError, ProgrammingError) as e:
        send_log(f"Query: {type(e).__name__} ({e})", level="error", service_type=SERVICE_TYPE)
        return "", 503
    except CircuitBreakerError:
        send_log(f"Inventory_Internal: Circuit breaker is open.", level="warning", service_type=SERVICE_TYPE)
        return "", 503


def get_gachas_types_of_user(session=None, user_uuid=None):
    """Get gacha types of items owned by user."""
    if not user_uuid or not isinstance(user_uuid, str):
        return "", 400

    try:
        @circuit_breaker
        def get_user_gacha_types():
            connection = get_db()
            cursor = connection.cursor()
            
            query = """
            SELECT DISTINCT BIN_TO_UUID(stand_uuid) 
            FROM inventories 
            WHERE BIN_TO_UUID(owner_uuid) = %s
            """
            
            cursor.execute(query, (user_uuid,))
            results = cursor.fetchall()
            
            cursor.close()
            return [result[0] for result in results] if results else []

        gacha_types = get_user_gacha_types()
            
        return jsonify(gacha_types), 200

    except (OperationalError, DataError, DatabaseError, IntegrityError, 
            InterfaceError, InternalError, ProgrammingError) as e:
        send_log(f"Query: {type(e).__name__} ({e})", level="error", service_type=SERVICE_TYPE)
        return "", 503
    except CircuitBreakerError:
        send_log(f"Inventory_Internal: Circuit breaker is open.", level="warning", service_type=SERVICE_TYPE)
        return "", 503


def get_inventory_by_owner_uuid(session=None, uuid=None):
    """Returns inventory items owned by user with UUID requested.
    
    :param session: Session cookie 
    :type session: str
    :param uuid: User UUID
    :type uuid: str
    :rtype: List[str]
    """
    if not uuid or not isinstance(uuid, str):
        return "", 400

    try:
        @circuit_breaker
        def get_user_inventory_items():
            connection = get_db()
            cursor = connection.cursor()
            
            query = """
            SELECT BIN_TO_UUID(item_uuid)
            FROM inventories 
            WHERE BIN_TO_UUID(owner_uuid) = %s
            """
            
            cursor.execute(query, (uuid,))
            results = cursor.fetchall()
            
            cursor.close()
            return [result[0] for result in results] if results else []

        inventory_items = get_user_inventory_items()
            
        return jsonify(inventory_items), 200

    except (OperationalError, DataError, DatabaseError, IntegrityError, 
            InterfaceError, InternalError, ProgrammingError) as e:
        send_log(f"Query: {type(e).__name__} ({e})", level="error", service_type=SERVICE_TYPE)
        return "", 503
    except CircuitBreakerError:
        send_log(f"Inventory_Internal: Circuit breaker is open.", level="warning", service_type=SERVICE_TYPE)
        return "", 503


def get_inventory_items_by_owner_uuid(session=None, uuid=None, page_number=None):
    """Returns inventory items owned by user with UUID requested, paginated.
    
    :param session: Session cookie 
    :type session: str
    :param uuid: User UUID
    :type uuid: str
    :param page_number: Page number of the list
    :type page_number: int
    :rtype: List[InventoryItem]
    """
    if not uuid or not isinstance(uuid, str):
        return "", 400

    # Validazione del page_number
    try:
        page_number = int(page_number) if page_number is not None else 1
        if page_number < 1:
            page_number = 1
    except (TypeError, ValueError):
        page_number = 1

    try:
        @circuit_breaker
        def get_user_inventory_items():
            connection = get_db()
            cursor = connection.cursor()
            
            items_per_page = 10  
            offset = (page_number - 1) * items_per_page
            print(items_per_page,offset)
            
            query = """
            SELECT BIN_TO_UUID(item_uuid), BIN_TO_UUID(owner_uuid), BIN_TO_UUID(stand_uuid), 
                   obtained_at, owners_no, currency_spent
            FROM inventories 
            WHERE BIN_TO_UUID(owner_uuid) = %s
            LIMIT %s OFFSET %s
            """
            
            cursor.execute(query, (uuid, items_per_page, offset))
            results = cursor.fetchall()
            
            cursor.close()
            return results

        results = get_user_inventory_items()
        inventory_items = []
        for row in results:
            item = {
                "item_id": row[0],
                "owner_id": row[1],
                "gacha_uuid": row[2],
                "obtained_date": row[3].strftime("%Y-%m-%d %H:%M:%S"), 
                "owners_no": row[4],
                "price_paid": row[5]
            }
            inventory_items.append(item)
        
        return jsonify(inventory_items), 200

    except (OperationalError, DataError, DatabaseError, IntegrityError, 
            InterfaceError, InternalError, ProgrammingError) as e:
        send_log(f"Query: {type(e).__name__} ({e})", level="error", service_type=SERVICE_TYPE)
        return "", 503
    except CircuitBreakerError:
        send_log(f"Inventory_Internal: Circuit breaker is open.", level="warning", service_type=SERVICE_TYPE)
        return "", 503


def get_item_by_uuid(session=None, uuid=None):
    """Returns item with requested uuid.
    
    """
    if not uuid or not isinstance(uuid, str):
        return "", 400
        
    try:
        @circuit_breaker
        def get_item_info():
            connection = get_db()
            cursor = connection.cursor()
            
            query = """
            SELECT BIN_TO_UUID(owner_uuid), BIN_TO_UUID(item_uuid), 
                   BIN_TO_UUID(stand_uuid), obtained_at, owners_no, currency_spent
            FROM inventories 
            WHERE BIN_TO_UUID(item_uuid) = %s
            """
            
            cursor.execute(query, (uuid,))
            result = cursor.fetchone()
            
            cursor.close()
            return result

        item = get_item_info()
        if not item:
            return "", 404
            
        inventory_item = {
            "owner_id": item[0],
            "item_id": item[1], 
            "gacha_uuid": item[2],
            "obtained_date": item[3].strftime("%Y-%m-%d %H:%M:%S"),
            "owners_no": item[4],
            "price_paid": item[5]
        }
        
        return jsonify(inventory_item), 200
        
    except (OperationalError, DataError, DatabaseError, IntegrityError, 
            InterfaceError, InternalError, ProgrammingError) as e:
        send_log(f"Query: {type(e).__name__} ({e})", level="error", service_type=SERVICE_TYPE)
        return "", 503
    except CircuitBreakerError:
        send_log(f"Inventory_Internal: Circuit breaker is open.", level="warning", service_type=SERVICE_TYPE)
        return "", 503


def get_items_by_stand_uuid(session=None, uuid=None):
    """Returns list of items which are a specific stand.
    
    :param session: Session cookie
    :type session: str
    :param uuid: Stand UUID
    :type uuid: str
    :rtype: List[InventoryItem]
    """
    if not uuid or not isinstance(uuid, str):
        return "", 400

    try:
        @circuit_breaker
        def get_stand_items():
            connection = get_db()
            cursor = connection.cursor()
            
            query = """
            SELECT BIN_TO_UUID(item_uuid), BIN_TO_UUID(owner_uuid), BIN_TO_UUID(stand_uuid), 
                   obtained_at, owners_no, currency_spent
            FROM inventories 
            WHERE BIN_TO_UUID(stand_uuid) = %s
            """
            
            cursor.execute(query, (uuid,))
            results = cursor.fetchall()
            
            cursor.close()
            return results

        results = get_stand_items()
        inventory_items = []
        for row in results:
            item = {
                "item_id": row[0],
                "owner_id": row[1],
                "gacha_uuid": row[2],
                "obtained_date": row[3].strftime("%Y-%m-%d %H:%M:%S"), 
                "owners_no": row[4],
                "price_paid": row[5]
            }
            inventory_items.append(item)
        
        return jsonify(inventory_items), 200

    except (OperationalError, DataError, DatabaseError, IntegrityError, 
            InterfaceError, InternalError, ProgrammingError) as e:
        send_log(f"Query: {type(e).__name__} ({e})", level="error", service_type=SERVICE_TYPE)
        return "", 503
    except CircuitBreakerError:
        send_log(f"Inventory_Internal: Circuit breaker is open.", level="warning", service_type=SERVICE_TYPE)
        return "", 503


def get_stand_uuid_by_item_uuid(session=None, uuid=None):
    """Returns item with requested uuid.
    
    :param session: Session cookie
    :type session: str
    :param uuid: Item UUID
    :type uuid: str
    :rtype: GetStandUuidByItemUuid200Response
    """
    if not uuid or not isinstance(uuid, str):
        return "", 400

    try:
        @circuit_breaker
        def get_stand_uuid():
            connection = get_db()
            cursor = connection.cursor()
            
            query = """
            SELECT BIN_TO_UUID(stand_uuid)
            FROM inventories 
            WHERE BIN_TO_UUID(item_uuid) = %s
            """
            
            cursor.execute(query, (uuid,))
            result = cursor.fetchone()
            
            cursor.close()
            return result

        result = get_stand_uuid()
        if not result:
            return "", 404
            
        stand_info = {
            "stand_uuid": result[0]
        }
        
        return jsonify(stand_info), 200

    except (OperationalError, DataError, DatabaseError, IntegrityError, 
            InterfaceError, InternalError, ProgrammingError) as e:
        send_log(f"Query: {type(e).__name__} ({e})", level="error", service_type=SERVICE_TYPE)
        return "", 503
    except CircuitBreakerError:
        send_log(f"Inventory_Internal: Circuit breaker is open.", level="warning", service_type=SERVICE_TYPE)
        return "", 503


def insert_item(inventory_item=None, session=None):
    """insert_item

    Assigns a certain item.

    :param inventory_item: 
    :type inventory_item: dict | bytes
    :param session: 
    :type session: str
    :rtype: Union[None, Tuple[None, int], Tuple[None, int, Dict[str, str]]
    """
    if not connexion.request.is_json:
        return "", 400
        
    try:
        @circuit_breaker
        def get_item_info():
            connection = get_db()
            cursor = connection.cursor()
            
            query = """
            INSERT INTO inventories (item_uuid, owner_uuid, stand_uuid, 
                                   obtained_at, owners_no, currency_spent)
            VALUES (UUID_TO_BIN(%s), UUID_TO_BIN(%s), UUID_TO_BIN(%s), 
                   %s, %s, %s)
            """
            
            inventory_item = InventoryItem.from_dict(connexion.request.get_json())
            cursor.execute(query, (
                inventory_item.item_id,
                inventory_item.owner_id,
                inventory_item.gacha_uuid,
                inventory_item.obtained_date,
                inventory_item.owners_no,
                inventory_item.price_paid
            ))
            
            connection.commit()
            cursor.close()
            return True

        get_item_info()
        return "", 200

    except (OperationalError, DataError, DatabaseError, IntegrityError, 
            InterfaceError, InternalError, ProgrammingError) as e:
        send_log(f"Query: {type(e).__name__} ({e})", level="error", service_type=SERVICE_TYPE)
        return "", 503
    except CircuitBreakerError:
        send_log(f"Inventory_Internal: Circuit breaker is open.", level="warning", service_type=SERVICE_TYPE)
        return "", 503


def remove_item(session=None, item_uuid=None, owner_uuid=None):

    if not item_uuid or not owner_uuid:
        return "", 400

    try:
        @circuit_breaker
        def delete_inventory_item():
            connection = get_db()
            cursor = connection.cursor()
            
            # First check if item exists
            query = """
            SELECT BIN_TO_UUID(item_uuid)
            FROM inventories 
            WHERE BIN_TO_UUID(item_uuid) = %s AND BIN_TO_UUID(owner_uuid) = %s
            """
            
            cursor.execute(query, (item_uuid, owner_uuid))
            if not cursor.fetchone():
                cursor.close()
                return "", 404
                
            # If exists, delete it
            query = """
            DELETE FROM inventories 
            WHERE BIN_TO_UUID(item_uuid) = %s AND BIN_TO_UUID(owner_uuid) = %s
            """
            
            cursor.execute(query, (item_uuid, owner_uuid))
            connection.commit()
            cursor.close()
            return "", 200

        response = delete_inventory_item()

        return response

    except (OperationalError, DataError, DatabaseError, IntegrityError, 
            InterfaceError, InternalError, ProgrammingError) as e:
        send_log(f"Query: {type(e).__name__} ({e})", level="error", service_type=SERVICE_TYPE)
        return "", 503
    except CircuitBreakerError:
        send_log(f"Inventory_Internal: Circuit breaker is open.", level="warning", service_type=SERVICE_TYPE)
        return "", 503


def update_item_ownership(session=None, new_owner_uuid=None, item_uuid=None, price_paid=None):
    if not new_owner_uuid or not item_uuid:
        return "", 400

    try:
        @circuit_breaker

        def check_item_exists():
            connection = get_db()
            cursor = connection.cursor()
            
            query = """
            SELECT COUNT(*)
            FROM inventories
            WHERE BIN_TO_UUID(item_uuid) = %s
            """
            
            cursor.execute(query, (item_uuid,))
            exists = cursor.fetchone()[0] > 0
            cursor.close()
            return exists
        
        def update_item_owner():
            connection = get_db()
            cursor = connection.cursor()
            
            query = """
            UPDATE inventories 
            SET owner_uuid = UUID_TO_BIN(%s),
                currency_spent = %s,
                owners_no = owners_no + 1
            WHERE BIN_TO_UUID(item_uuid) = %s
            """
            
            cursor.execute(query, (new_owner_uuid, price_paid or 0, item_uuid))
            connection.commit()
            cursor.close()
            return True
        
        if not check_item_exists():
            return "", 404

        update_item_owner()
        return "", 200

    except (OperationalError, DataError, DatabaseError, IntegrityError, 
            InterfaceError, InternalError, ProgrammingError) as e:
        send_log(f"Query: {type(e).__name__} ({e})", level="error", service_type=SERVICE_TYPE)
        return "", 503
    except CircuitBreakerError:
        send_log(f"Inventory_Internal: Circuit breaker is open.", level="warning", service_type=SERVICE_TYPE)
        return "", 503