from flask import request, jsonify
from functools import wraps
from .models import MeasurementReplicationManager

replication_manager = None  # sarà inizializzato una volta sola

# Definisce i valori di configurazione predefiniti
nodes_db = 3
port = 5000
API_TOKEN = "your_api_token_here"

# Decorator per richiedere un token API valido
def require_api_token(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if request.headers.get('Authorization') != f"Bearer {API_TOKEN}":
            return jsonify({'error': 'Unauthorized', 'message': 'Invalid API token'}), 403
        return f(*args, **kwargs)
    return decorated_function

# Funzione per registrare le routes con l'app Flask
def register_routes(app, config):
    global nodes_db, port, API_TOKEN, replication_manager

    nodes_db = config.get('nodes_db')
    port = config.get('port')
    API_TOKEN = config.get('API_TOKEN')

    if replication_manager is None:
        replication_manager = MeasurementReplicationManager(num_nodes=nodes_db, port=port)

    
    # Endpoint di default per verificare lo stato del servizio
    @app.route('/')
    def index():
        return jsonify({'status': 'EnergyGuard API running'})

     # Endpoint per salvare una misurazione energetica
    @app.route('/ingest', methods=['POST'])
    @require_api_token
    def ingest_measurement():
        data = request.json
        required = {'sensor_id', 'timestamp', 'value'}
        if not data or not required.issubset(data):
            return jsonify({'error': 'Invalid input',
                            'message': 'sensor_id, timestamp and value are required'}), 400
        try:
            sensor_id = data['sensor_id']
            timestamp = data['timestamp']
            value = data['value']
            key = f"{sensor_id}:{timestamp}"
            replication_manager.store_measurement(key, value)
            return jsonify({'status': 'success',
                            'message': f'Measurement {key} stored successfully'})
        except Exception as e:
            return jsonify({'error': 'Internal server error', 'message': str(e)}), 500

    # Endpoint per impostare la soglia di un sensore
    @app.route('/set_threshold', methods=['POST'])
    @require_api_token
    def set_threshold():
        data = request.json
        if not data or 'sensor_id' not in data or 'threshold' not in data:
            return jsonify({'error': 'Invalid input',
                            'message': 'sensor_id and threshold are required'}), 400
        try:
            sensor_id = data['sensor_id']
            threshold = float(data['threshold'])
            replication_manager.alert_manager.set_threshold(sensor_id, threshold)
            return jsonify({'status': 'success', 'message': f'Threshold for sensor {sensor_id} set to {threshold}'})
        except Exception as e:
            return jsonify({'error': 'Internal server error', 'message': str(e)}), 500

    # Endpoint per leggere una misurazione energetica
    @app.route('/measurement/<sensor_key>', methods=['GET'])
    @require_api_token
    def get_measurement(sensor_key):
        try:
            result = replication_manager.retrieve_measurement(sensor_key)
            if result['value'] is not None:
                return jsonify({'key': sensor_key, 'value': result['value'], 'message': result['message'], 'status': 'success'})
            else:
                return jsonify({'error': 'Measurement not found', 'message': result['message']}), 404
        except Exception as e:
            return jsonify({'error': 'Internal server error', 'message': str(e)}), 500

    # Endpoint per eliminare una misurazione
    @app.route('/delete/<sensor_key>', methods=['DELETE'])
    @require_api_token
    def delete_measurement(sensor_key):
        try:
            if not replication_manager.measurement_exists(sensor_key):
                return jsonify({'error': 'Measurement not found', 'message': 'Measurement does not exist'}), 404
            replication_manager.delete_measurement(sensor_key)
            return jsonify({'status': 'success', 'message': f'Measurement {sensor_key} deleted successfully'})
        except Exception as e:
            return jsonify({'error': 'Internal server error', 'message': str(e)}), 500

    # Endpoint per simulare il fallimento di un nodo
    @app.route('/fail_node/<int:node_id>', methods=['POST'])
    @require_api_token
    def simulate_failure(node_id):
        try:
            replication_manager.fail_node(node_id)
            return jsonify({'status': 'success', 'message': f'Node {node_id} marked as failed'})
        except Exception as e:
            return jsonify({'error': 'Internal server error', 'message': str(e)}), 500

    # Endpoint per recuperare un nodo dopo un fallimento
    @app.route('/recover_node/<int:node_id>', methods=['POST'])
    @require_api_token
    def recover_node(node_id):
        try:
            replication_manager.recover_node(node_id)
            return jsonify({'status': 'success', 'message': f'Node {node_id} recovered'})
        except Exception as e:
            return jsonify({'error': 'Internal server error', 'message': str(e)}), 500

    # Endpoint per ottenere lo stato dei nodi
    @app.route('/nodes_status', methods=['GET'])
    @require_api_token
    def get_node_status():
        try:
           return jsonify({'status': 'success', 'nodes': replication_manager.get_storage_status()})
        except Exception as e:
            return jsonify({'error': 'Internal server error', 'message': str(e)}), 500

    # Endpoint per impostare la strategia di replica
    @app.route('/configure_replication', methods=['POST'])
    @require_api_token
    def configure_replication():
        data = request.json
        if 'strategy' not in data:
            return jsonify({'error': 'Invalid input', 'message': 'Replication strategy is required'}), 400
        strategy = data.get('strategy')
        replication_factor = data.get('replication_factor')
        try:
            replication_manager.set_replication_strategy(strategy, replication_factor)
            return jsonify({'status': 'success', 'message': f'Strategy set to {strategy} with factor {replication_factor}'})
        except Exception as e:
            return jsonify({'error': 'Internal server error', 'message': str(e)}), 500

    # Endpoint per visualizzare i nodi responsabili di una chiave specifica
    @app.route('/replica_nodes/<sensor_key>', methods=['GET'])
    @require_api_token
    def replica_nodes(sensor_key):
        try:
            nodes = replication_manager.get_responsible_nodes(sensor_key)
            if nodes:
                nodes_info = [
                    {
                        'node_id': n.node_id,
                        'status': 'alive' if n.is_alive() else 'dead',
                        'port': n.port
                    }
                    for n in nodes
                ]
                return jsonify({'status': 'success', 'nodes': nodes_info})
            else:
                return jsonify({'error': 'Strategy error', 'message': 'Consistent hashing is not active'}), 400
        except Exception as e:
            return jsonify({'error': 'Internal server error', 'message': str(e)}), 500
    
    @app.route('/alerts', methods=['GET'])
    @require_api_token
    def get_alerts():
        try:
            alerts = replication_manager.alert_manager.get_alerts()
            return jsonify({'status': 'success', 'alerts': alerts})
        except Exception as e:
            return jsonify({'error': 'Internal server error', 'message': str(e)}), 500

    @app.route('/measurements', methods=['GET'])
    @require_api_token
    def get_all_measurements_route():
        try:
            measurements = replication_manager.get_all_measurements()
            return jsonify({'status': 'success', 'measurements': measurements})
        except Exception as e:
            return jsonify({'error': 'Internal server error', 'message': str(e)}), 500

    @app.route('/sensor/<sensor_id>/history', methods=['GET'])
    @require_api_token
    def get_sensor_history(sensor_id):
        try:
            prefix = f"{sensor_id}:"
            all_measurements = replication_manager.get_all_measurements()
            filtered = {k: v for k, v in all_measurements.items() if k.startswith(prefix)}
            return jsonify({'status': 'success', 'measurements': filtered})
        except Exception as e:
            return jsonify({'error': 'Internal server error', 'message': str(e)}), 500