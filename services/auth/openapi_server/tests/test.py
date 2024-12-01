import connexion
from flask import jsonify
from unittest.mock import patch, MagicMock
from openapi_server.controllers.auth_controller import login

def create_app():
    connexion_app = connexion.App(__name__, specification_dir='../openapi/')
    app = connexion_app.app
    app.testing = True
    return app



def test_login_invalid_request_json():
    """
    Test login: Invalid request JSON.
    """
    # Inizializza l'app utilizzando la funzione create_app
    app = create_app()

    # Mock per la richiesta non valida
    invalid_login_request = {
        "username": "test_user",
        # Password mancante per simulare una richiesta non valida
    }

    # Mock per la risposta di requests.get
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "username": "LeoPanta01_",
        "password": "Th1s_c4n_b3_a_good_passw0rd...maybe"
    }
    mock_response.status_code = 200

    # Contesto di test della richiesta
    with app.test_request_context('/auth/login', method='POST', json=invalid_login_request):
        with patch('connexion.request') as mock_connexion_request:
            mock_connexion_request.get_json.return_value = ""
            mock_connexion_request.is_json = False

            # Chiama la funzione da testare
            message, code = login()

            # Verifica delle asserzioni
            assert message.json == {"message": "Invalid request."}
            assert code == 400