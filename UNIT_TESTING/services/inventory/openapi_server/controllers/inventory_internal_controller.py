# inventory_internal_controller.py (MOCKED)

import connexion
import datetime
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
from openapi_server.models.check_owner_of_team_request import CheckOwnerOfTeamRequest
from openapi_server.models.exists_inventory200_response import ExistsInventory200Response
from openapi_server.models.inventory_item import InventoryItem


MOCK_INVENTORY_DATA = {
    'f7e6d5c4-b3a2-9180-7654-321098fedcba': {
        'item_uuid': 'f7e6d5c4-b3a2-9180-7654-321098fedcba',
        'owner_uuid': 'e3b0c442-98fc-1c14-b39f-92d1282048c0',
        'stand_uuid': '1b2f7b4e-5e1f-4112-a7c5-b7559dbb8c76',
        'obtained_at': datetime.datetime(2024, 1, 1),
        'owners_no': 1,
        'currency_spent': 3000
    },
    'e6d5c4b3-a291-8076-5432-109876fedcba': {
        'item_uuid': 'e6d5c4b3-a291-8076-5432-109876fedcba',
        'owner_uuid': '87f3b5d1-5e8e-4fa4-909b-3cd29f4b1f09',
        'stand_uuid': '9d4b9fa9-6c72-44f5-9ac6-e6b548cfc632',
        'obtained_at': datetime.datetime(2024, 1, 2),
        'owners_no': 1,
        'currency_spent': 3000
    },
    'd5c4b3a2-9180-7654-3210-9876fedcba98': {
        'item_uuid': 'd5c4b3a2-9180-7654-3210-9876fedcba98',
        'owner_uuid': 'a4f0c592-12af-4bde-aacd-94cd0f27c57e',
        'stand_uuid': 'b6e7f8c9-7f28-4b4f-8fbe-523f6c8b0c85',
        'obtained_at': datetime.datetime(2024, 1, 3),
        'owners_no': 1,
        'currency_spent': 2500
    },
    'c7b6a5d4-e3f2-1098-7654-fedcba987654': {
        'item_uuid': 'c7b6a5d4-e3f2-1098-7654-fedcba987654',
        'owner_uuid': '4f2e8bb5-38e1-4537-9cfa-11425c3b4284',
        'stand_uuid': '1b2f7b4e-5e1f-4112-a7c5-b7559dbb8c76',
        'obtained_at': datetime.datetime(2024, 1, 1),
        'owners_no': 1,
        'currency_spent': 5000
    },
    'b7a6c5d4-e3f2-1098-7654-fedcba987655': {
        'item_uuid': 'b7a6c5d4-e3f2-1098-7654-fedcba987655',
        'owner_uuid': '4f2e8bb5-38e1-4537-9cfa-11425c3b4284',
        'stand_uuid': '9d4b9fa9-6c72-44f5-9ac6-e6b548cfc632',
        'obtained_at': datetime.datetime(2024, 1, 2),
        'owners_no': 1,
        'currency_spent': 5000
    },
    'a7b6c5d4-e3f2-1098-7654-fedcba987656': {
        'item_uuid': 'a7b6c5d4-e3f2-1098-7654-fedcba987656',
        'owner_uuid': '4f2e8bb5-38e1-4537-9cfa-11425c3b4284',
        'stand_uuid': 'b6e7f8c9-7f28-4b4f-8fbe-523f6c8b0c85',
        'obtained_at': datetime.datetime(2024, 1, 3),
        'owners_no': 1,
        'currency_spent': 3000
    },
    '97b6c5d4-e3f2-1098-7654-fedcba987657': {
        'item_uuid': '97b6c5d4-e3f2-1098-7654-fedcba987657',
        'owner_uuid': '4f2e8bb5-38e1-4537-9cfa-11425c3b4284',
        'stand_uuid': '8f2b9d4e-3b3e-4c5d-a1c6-b7e3a5d6c1c7',
        'obtained_at': datetime.datetime(2024, 1, 4),
        'owners_no': 1,
        'currency_spent': 3000
    },
    '87b6c5d4-e3f2-1098-7654-fedcba987658': {
        'item_uuid': '87b6c5d4-e3f2-1098-7654-fedcba987658',
        'owner_uuid': '4f2e8bb5-38e1-4537-9cfa-11425c3b4284',
        'stand_uuid': 'c1d2e3f4-5a6b-7c8d-9e0f-1a2b3c4d5e6f',
        'obtained_at': datetime.datetime(2024, 1, 5),
        'owners_no': 1,
        'currency_spent': 2000
    },
    '77b6c5d4-e3f2-1098-7654-fedcba987659': {
        'item_uuid': '77b6c5d4-e3f2-1098-7654-fedcba987659',
        'owner_uuid': '4f2e8bb5-38e1-4537-9cfa-11425c3b4284',
        'stand_uuid': 'd4e5f6a7-b8c9-0d1e-2f3a-4b5c6d7e8f9a',
        'obtained_at': datetime.datetime(2024, 1, 6),
        'owners_no': 1,
        'currency_spent': 1000
    },
    '67b6c5d4-e3f2-1098-7654-fedcba987660': {
        'item_uuid': '67b6c5d4-e3f2-1098-7654-fedcba987660',
        'owner_uuid': '4f2e8bb5-38e1-4537-9cfa-11425c3b4284',
        'stand_uuid': 'e7f8a9b0-c1d2-3e4f-5a6b-7c8d9e0f1a2b',
        'obtained_at': datetime.datetime(2024, 1, 7),
        'owners_no': 1,
        'currency_spent': 2000
    },
    '57b6c5d4-e3f2-1098-7654-fedcba987661': {
        'item_uuid': '57b6c5d4-e3f2-1098-7654-fedcba987661',
        'owner_uuid': 'a1a2a3a4-b5b6-c7c8-d9d0-e1e2e3e4e5e6',
        'stand_uuid': 'c3d4e5f6-a7b8-9012-3456-7890abcdef12',
        'obtained_at': datetime.datetime(2024, 1, 8),
        'owners_no': 1,
        'currency_spent': 5000
    },
    '47b6c5d4-e3f2-1098-7654-fedcba987662': {
        'item_uuid': '47b6c5d4-e3f2-1098-7654-fedcba987662',
        'owner_uuid': 'a1a2a3a4-b5b6-c7c8-d9d0-e1e2e3e4e5e6',
        'stand_uuid': 'a1b2c3d4-e5f6-7890-1234-567890abcdef',
        'obtained_at': datetime.datetime(2024, 1, 9),
        'owners_no': 1,
        'currency_spent': 5000
    },
    '37b6c5d4-e3f2-1098-7654-fedcba987663': {
        'item_uuid': '37b6c5d4-e3f2-1098-7654-fedcba987663',
        'owner_uuid': 'a1a2a3a4-b5b6-c7c8-d9d0-e1e2e3e4e5e6',
        'stand_uuid': 'b2c3d4e5-f6a7-8901-2345-67890abcdef1',
        'obtained_at': datetime.datetime(2024, 1, 10),
        'owners_no': 1,
        'currency_spent': 3000
    },
    '27b6c5d4-e3f2-1098-7654-fedcba987664': {
        'item_uuid': '27b6c5d4-e3f2-1098-7654-fedcba987664',
        'owner_uuid': 'a1a2a3a4-b5b6-c7c8-d9d0-e1e2e3e4e5e6',
        'stand_uuid': 'e5f6a7b8-c9d0-1234-5678-90abcdef1234',
        'obtained_at': datetime.datetime(2024, 1, 11),
        'owners_no': 1,
        'currency_spent': 3000
    },
    '17b6c5d4-e3f2-1098-7654-fedcba987665': {
        'item_uuid': '17b6c5d4-e3f2-1098-7654-fedcba987665',
        'owner_uuid': 'a1a2a3a4-b5b6-c7c8-d9d0-e1e2e3e4e5e6',
        'stand_uuid': 'f6a7b8c9-d0e1-2345-6789-0abcdef12345',
        'obtained_at': datetime.datetime(2024, 1, 12),
        'owners_no': 1,
        'currency_spent': 2000
    },
    '07b6c5d4-e3f2-1098-7654-fedcba987666': {
        'item_uuid': '07b6c5d4-e3f2-1098-7654-fedcba987666',
        'owner_uuid': 'a1a2a3a4-b5b6-c7c8-d9d0-e1e2e3e4e5e6',
        'stand_uuid': 'c9d0e1f2-a3b4-5678-9012-cdef12345678',
        'obtained_at': datetime.datetime(2024, 1, 13),
        'owners_no': 1,
        'currency_spent': 1000
    },
    'f6b6c5d4-e3f2-1098-7654-fedcba987667': {
        'item_uuid': 'f6b6c5d4-e3f2-1098-7654-fedcba987667',
        'owner_uuid': 'a1a2a3a4-b5b6-c7c8-d9d0-e1e2e3e4e5e6',
        'stand_uuid': 'a7b8c9d0-e1f2-3456-7890-abcdef123456',
        'obtained_at': datetime.datetime(2024, 1, 14),
        'owners_no': 1,
        'currency_spent': 2000
    }
}


circuit_breaker = CircuitBreaker(fail_max=1000, reset_timeout=5, exclude=[OperationalError, DataError, DatabaseError, IntegrityError, InterfaceError, InternalError, ProgrammingError])


def check_owner_of_team(check_owner_of_team_request=None, session=None, user_uuid=None):
    """Checks if a team is actually owned by the user."""

    if not connexion.request.is_json:
        return jsonify({"message": "Invalid request."}), 400

    try:
        check_owner_of_team_request = CheckOwnerOfTeamRequest.from_dict(connexion.request.get_json())
        

        @circuit_breaker
        def verify_team_ownership():
            global MOCK_INVENTORY_DATA
            
            team_uuids = check_owner_of_team_request.team
            #Check if all items in the team belong to the user
            for item_uuid in team_uuids:
                if item_uuid not in MOCK_INVENTORY_DATA or MOCK_INVENTORY_DATA[item_uuid]['owner_uuid'] != user_uuid:
                    return False, 404


            return True, 200

        ownership_verified, status_code = verify_team_ownership()

        if not ownership_verified:
            if status_code == 404:
            
                return jsonify({"error": "Items not found in user inventory."}), 404

        return jsonify({"message": "Items verified."}), 200

    except (OperationalError, DataError, ProgrammingError, IntegrityError, InternalError, InterfaceError, DatabaseError) as e:
        return jsonify({"error": str(e)}), 503  # Return JSON error with status code
    except CircuitBreakerError:
        return jsonify({"error": "Circuit Breaker Open"}), 503  # Return JSON error with status code

def delete_by_stand_uuid(session=None, uuid=None):
    """Deletes items which are a certain stand."""

    if not uuid:
        return jsonify({"error": "Invalid request."}), 404

    try:
        @circuit_breaker
        def delete_stand_items():
            global MOCK_INVENTORY_DATA
            deleted_items = 0
            items_to_delete = []

            for item_uuid, item_data in MOCK_INVENTORY_DATA.items():
                if item_data['stand_uuid'] == uuid:
                    items_to_delete.append(item_uuid)
                    deleted_items += 1

            # Remove the items from the mock data
            for item_uuid in items_to_delete:
                del MOCK_INVENTORY_DATA[item_uuid]

            return deleted_items > 0, 200


        items_deleted, status_code = delete_stand_items()

        if not items_deleted:
            return jsonify({"error": "Items not found."}), 404

        return jsonify({"message": "Items deleted."}), 200

    except (OperationalError, DataError, ProgrammingError, IntegrityError, InternalError, InterfaceError, DatabaseError) as e:
        return jsonify({"error": str(e)}), 503
    except CircuitBreakerError:
        return jsonify({"error": "Circuit Breaker Open"}), 503

def delete_user_inventory(uuid=None, session=None):
    """Deletes items owned by user."""
    if not uuid or not isinstance(uuid, str):
        return jsonify({"error": "Invalid user UUID"}), 400  # Return 400 for invalid input


    try:
        @circuit_breaker
        def delete_user_items():
            global MOCK_INVENTORY_DATA
            deleted_count = 0
            items_to_delete = []

            for item_uuid, item_data in list(MOCK_INVENTORY_DATA.items()): #Use list() for safe iteration during deletion
                if item_data['owner_uuid'] == uuid:
                    items_to_delete.append(item_uuid)
                    deleted_count += 1

            for item_uuid in items_to_delete:
                del MOCK_INVENTORY_DATA[item_uuid]

            return deleted_count > 0, 200  # Return True if any items were deleted

        items_deleted, status_code = delete_user_items()

        if not items_deleted:
            return jsonify({"error": "No items found for this user."}), 404 #Return 404 if no items were found

        return "", 200

    except (OperationalError, DataError, DatabaseError, IntegrityError,
            InterfaceError, InternalError, ProgrammingError) as e:
        return jsonify({"error": str(e)}), 503
    except CircuitBreakerError:
        return jsonify({"error": "Circuit Breaker Open"}), 503

def exists_inventory(uuid=None, session=None):
    """Returns true if an item exists, false otherwise."""
    if not uuid or not isinstance(uuid, str):
        return "", 400

    try:
        @circuit_breaker
        def check_item_exists():
            global MOCK_INVENTORY_DATA
            return uuid in MOCK_INVENTORY_DATA, 200

        exists, status_code = check_item_exists()
        response = ExistsInventory200Response(exists=exists)

        return jsonify(response), status_code

    except (OperationalError, DataError, DatabaseError, IntegrityError,
            InterfaceError, InternalError, ProgrammingError) as e:
        return jsonify({"error": str(e)}), 503
    except CircuitBreakerError:
        return jsonify({"error": "Circuit Breaker Open"}), 503

def get_gachas_types_of_user(session=None, user_uuid=None):
    """Get gacha types of items owned by user."""

    if not user_uuid or not isinstance(user_uuid, str):
            return "", 400

    try:
        @circuit_breaker
        def get_user_gacha_types():
            global MOCK_INVENTORY_DATA
            gacha_types = set()  # Use a set to automatically handle duplicates

            for item_data in MOCK_INVENTORY_DATA.values():
                if item_data.get('owner_uuid') == user_uuid: # Use get() to handle potential missing key
                    gacha_types.add(item_data.get('stand_uuid')) #Use get() to handle potential missing key

            return list(gacha_types), 200  # Convert set back to list

        gacha_types, status_code = get_user_gacha_types()
        return jsonify(gacha_types), status_code

    except (OperationalError, DataError, DatabaseError, IntegrityError,
            InterfaceError, InternalError, ProgrammingError) as e:
        return jsonify({"error": str(e)}), 503
    except CircuitBreakerError:
        return jsonify({"error": "Circuit Breaker Open"}), 503

def get_inventory_by_owner_uuid(session=None, uuid=None):
    """Returns inventory items owned by user with UUID requested."""
    if not uuid or not isinstance(uuid, str):
        return "", 400
    
    try:
        @circuit_breaker
        def get_user_inventory_items():
            global MOCK_INVENTORY_DATA
            inventory_items = []
            for item_data in MOCK_INVENTORY_DATA.values():
                if item_data['owner_uuid'] == uuid:
                    inventory_items.append(item_data['item_uuid'])
            return inventory_items, 200


        inventory_items, status_code = get_user_inventory_items()
        return jsonify(inventory_items), status_code

    except (OperationalError, DataError, DatabaseError, IntegrityError,
            InterfaceError, InternalError, ProgrammingError) as e:
        return jsonify({"error": str(e)}), 503
    except CircuitBreakerError:
        return jsonify({"error": "Circuit Breaker Open"}), 503

def get_inventory_items_by_owner_uuid(session=None, uuid=None, page_number=None):
    """Returns inventory items owned by user with UUID requested, paginated."""
    if not uuid or not isinstance(uuid, str):
        return "", 400

    try:
        page_number = int(page_number) if page_number is not None else 1
        if page_number < 1:
            page_number = 1
    except (TypeError, ValueError):
        page_number = 1

    try:
        @circuit_breaker
        def get_user_inventory_items():
            global MOCK_INVENTORY_DATA
            items_per_page = 10
            offset = (page_number - 1) * items_per_page
            inventory_items = []

            #Filter and paginate the data
            filtered_items = [item_data for item_data in MOCK_INVENTORY_DATA.values() if item_data['owner_uuid'] == uuid]
            paginated_items = filtered_items[offset:offset + items_per_page]


            for item_data in paginated_items:
                item = {
                    "item_id": item_data['item_uuid'],
                    "owner_id": item_data['owner_uuid'],
                    "gacha_uuid": item_data['stand_uuid'],
                    "obtained_date": item_data['obtained_at'].strftime("%Y-%m-%d %H:%M:%S"),
                    "owners_no": item_data['owners_no'],
                    "price_paid": item_data['currency_spent']
                }
                inventory_items.append(item)

            return inventory_items, 200 


        inventory_items, status_code = get_user_inventory_items()
        return inventory_items, status_code

    except (OperationalError, DataError, DatabaseError, IntegrityError,
            InterfaceError, InternalError, ProgrammingError) as e:
        return jsonify({"error": str(e)}), 503
    except CircuitBreakerError:
        return jsonify({"error": "Circuit Breaker Open"}), 503
    except IndexError: #Handle potential IndexError if offset is out of bounds
        return jsonify({"error": "Invalid page number"}), 400

def get_item_by_uuid(session=None, uuid=None):
    """Returns item with requested uuid."""
    if not uuid or not isinstance(uuid, str):
        return "", 400

    try:
        @circuit_breaker
        def get_item_info():
            global MOCK_INVENTORY_DATA
            item_data = MOCK_INVENTORY_DATA.get(uuid)
            if not item_data:
                return "", 404

            inventory_item = {
                "owner_id": item_data['owner_uuid'],
                "item_id": item_data['item_uuid'],
                "gacha_uuid": item_data['stand_uuid'],
                "obtained_date": item_data['obtained_at'].strftime("%Y-%m-%d %H:%M:%S"),
                "owners_no": item_data['owners_no'],
                "price_paid": item_data['currency_spent']
            }
            
            return inventory_item, 200

        inventory_item, status_code = get_item_info()
        if status_code == 404:
            return "", 404
        return inventory_item, status_code

    except (OperationalError, DataError, DatabaseError, IntegrityError,
            InterfaceError, InternalError, ProgrammingError) as e:
        return jsonify({"error": str(e)}), 503
    except CircuitBreakerError:
        return jsonify({"error": "Circuit Breaker Open"}), 503

def get_items_by_stand_uuid(session=None, uuid=None):
    """Returns list of items which are a specific stand."""
    if not uuid or not isinstance(uuid, str):
        return "", 400

    try:
        @circuit_breaker
        def get_stand_items():
            global MOCK_INVENTORY_DATA
            inventory_items = []
            for item_data in MOCK_INVENTORY_DATA.values():
                if item_data['stand_uuid'] == uuid:
                    item = {
                        "item_id": item_data['item_uuid'],
                        "owner_id": item_data['owner_uuid'],
                        "gacha_uuid": item_data['stand_uuid'],
                        "obtained_date": item_data['obtained_at'].strftime("%Y-%m-%d %H:%M:%S"),
                        "owners_no": item_data['owners_no'],
                        "price_paid": item_data['currency_spent']
                    }
                    inventory_items.append(item)
            return inventory_items, 200


        inventory_items, status_code = get_stand_items()
        return jsonify(inventory_items), status_code

    except (OperationalError, DataError, DatabaseError, IntegrityError,
            InterfaceError, InternalError, ProgrammingError) as e:
        return jsonify({"error": str(e)}), 503
    except CircuitBreakerError:
        return jsonify({"error": "Circuit Breaker Open"}), 503

def get_stand_uuid_by_item_uuid(session=None, uuid=None):
    """Returns stand UUID for a given item UUID."""
    if not uuid or not isinstance(uuid, str):
        return "", 400

    try:
        @circuit_breaker
        def get_stand_uuid():
            global MOCK_INVENTORY_DATA
            item_data = MOCK_INVENTORY_DATA.get(uuid)
            if not item_data:
                return None, 404
            return item_data['stand_uuid'], 200

        stand_uuid, status_code = get_stand_uuid()
        if status_code == 404:
            return "", 404
        return jsonify({"stand_uuid": stand_uuid}), status_code

    except (OperationalError, DataError, DatabaseError, IntegrityError,
            InterfaceError, InternalError, ProgrammingError) as e:
        return jsonify({"error": str(e)}), 503
    except CircuitBreakerError:
        return jsonify({"error": "Circuit Breaker Open"}), 503

def insert_item(inventory_item=None, session=None):
    """insert_item

    Assigns a certain item.
    """
    if not connexion.request.is_json:
        return "", 400

    try:
        
        @circuit_breaker
        def insert_item_into_mock():
            global MOCK_INVENTORY_DATA
            inventory_item_data = InventoryItem.from_dict(connexion.request.get_json())
            item_uuid = inventory_item_data.item_id

            if item_uuid in MOCK_INVENTORY_DATA:
                raise IntegrityError

            MOCK_INVENTORY_DATA[item_uuid] = {
                'item_uuid': item_uuid,
                'owner_uuid': inventory_item_data.owner_id,
                'stand_uuid': inventory_item_data.gacha_uuid,
                'obtained_at': inventory_item_data.obtained_date,
                'owners_no': inventory_item_data.owners_no,
                'currency_spent': inventory_item_data.price_paid
            }
            return True, 200

        success, status_code = insert_item_into_mock()
        
        if not success:
            return jsonify({"error": "Failed to insert item"}), 503


        return "", 200

    except (OperationalError, DataError, DatabaseError, IntegrityError,
            InterfaceError, InternalError, ProgrammingError) as e:
        return jsonify({"error": str(e)}), 503
    except CircuitBreakerError:
        return jsonify({"error": "Circuit Breaker Open"}), 503
    except Exception as e: # Catch other unexpected exceptions during processing
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500

def remove_item(session=None, item_uuid=None, owner_uuid=None):
    """Removes an item from the inventory."""
    if not item_uuid or not owner_uuid:
        return "", 400

    try:
        @circuit_breaker
        def delete_inventory_item():
            global MOCK_INVENTORY_DATA
            item_key = item_uuid

            if item_key not in MOCK_INVENTORY_DATA or MOCK_INVENTORY_DATA[item_key]['owner_uuid'] != owner_uuid:
                return False, 404 # Item not found or not owned by the user

            del MOCK_INVENTORY_DATA[item_key]
            return True, 200

        success, status_code = delete_inventory_item()

        if not success:
            return "", status_code 

        return "", 200

    except (OperationalError, DataError, DatabaseError, IntegrityError,
            InterfaceError, InternalError, ProgrammingError) as e:
        return jsonify({"error": str(e)}), 503
    except CircuitBreakerError:
        return jsonify({"error": "Circuit Breaker Open"}), 503

def update_item_ownership(session=None, new_owner_uuid=None, item_uuid=None, price_paid=None):
    """Updates the ownership of an item."""
    if not new_owner_uuid or not item_uuid:
        return "", 400

    try:

        @circuit_breaker
        def update_item_owner():
            global MOCK_INVENTORY_DATA
            if item_uuid not in MOCK_INVENTORY_DATA:
                return False, 404

            MOCK_INVENTORY_DATA[item_uuid]['owner_uuid'] = new_owner_uuid
            MOCK_INVENTORY_DATA[item_uuid]['currency_spent'] = price_paid
            MOCK_INVENTORY_DATA[item_uuid]['owners_no'] += 1
            return True, 200


        success, status_code = update_item_owner()

        if not success:
            return "", status_code

        return "", 200

    except (OperationalError, DataError, DatabaseError, IntegrityError,
            InterfaceError, InternalError, ProgrammingError) as e:
        return jsonify({"error": str(e)}), 503
    except CircuitBreakerError:
        return jsonify({"error": "Circuit Breaker Open"}), 503
    except ValueError:
        return jsonify({"error": "Invalid price_paid value"}), 400 #Handle ValueError for price_paid