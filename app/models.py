import sqlite3
import os
from .energyguardring import EnergyGuardRing

class StorageNode:
    def __init__(self, node_id, port):
        self.node_id = node_id
        self.port = port
        self.name_db = f'storage_{node_id}.db'
        self.db_path = os.path.join('data', self.name_db)
        self.alive = True
        self._create_data_directory()
        self._initialize_db()

    def _create_data_directory(self):
        if not os.path.exists('data'):
            os.makedirs('data')

    def _initialize_db(self):
        if not os.path.exists(self.db_path):
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''CREATE TABLE IF NOT EXISTS measurements (key TEXT PRIMARY KEY, value TEXT)''')
            conn.commit()
            conn.close()

    def write(self, key, value):
        if self.alive:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''INSERT OR REPLACE INTO measurements (key, value) VALUES (?, ?)''', (key, value))
            conn.commit()
            conn.close()

    def read(self, key):
        if self.alive:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''SELECT value FROM measurements WHERE key=?''', (key,))
            result = cursor.fetchone()
            conn.close()
            return result[0] if result else None

    def delete(self, key):
        if self.alive:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''DELETE FROM measurements WHERE key=?''', (key,))
            conn.commit()
            conn.close()

    def key_exists(self, key):
        if self.alive:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''SELECT 1 FROM measurements WHERE key=?''', (key,))
            exists = cursor.fetchone() is not None
            conn.close()
            return exists

    def fail(self):
        self.alive = False

    def recover(self, active_nodes, strategy='full'):
        if not self.alive:
            self.alive = True
            if strategy == 'full':
                self.sync_with_active_nodes(active_nodes)

    def is_alive(self):
        return self.alive

    def sync_with_active_nodes(self, active_nodes):
        all_keys = set()
        for node in active_nodes:
            if node.is_alive() and node.node_id != self.node_id:
                conn = sqlite3.connect(node.db_path)
                cursor = conn.cursor()
                cursor.execute('''SELECT key, value FROM measurements''')
                rows = cursor.fetchall()
                conn.close()
                for key, value in rows:
                    self.write(key, value)
                    all_keys.add(key)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''SELECT key FROM measurements''')
        self_keys = cursor.fetchall()
        conn.close()

        for (key,) in self_keys:
            if key not in all_keys:
                self.delete(key)

    def get_all_keys(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''SELECT key, value FROM measurements''')
        rows = cursor.fetchall()
        conn.close()
        return rows


class MeasurementReplicationManager:
    def __init__(self, num_nodes=3, port=5000, strategy='full', replication_factor=None):
        self.num_nodes = num_nodes
        self.strategy = strategy
        self.nodes = [StorageNode(i, port + i) for i in range(num_nodes)]
        self.hash_ring = None
        self.alert_manager = AlertManager()

        if strategy == 'consistent':
            self.hash_ring = EnergyGuardRing(self.nodes, replicas=replication_factor)

    def set_replication_strategy(self, strategy, replication_factor=None):
        self.strategy = strategy
        if strategy == 'consistent':
            self.hash_ring = EnergyGuardRing(self.nodes, replicas=replication_factor)
        else:
            self.hash_ring = None

    def store_measurement(self, key, value):
        if self.strategy == 'full':
            for node in self.nodes:
                if node.is_alive():
                    node.write(key, value)
        elif self.strategy == 'consistent':
            for node in self.hash_ring.get_nodes_for_key(key):
                if node.is_alive():
                    node.write(key, value)

        # --- Controllo anomalie ---
        try:
            sensor_id, timestamp = key.split(":")
            self.alert_manager.check_for_anomaly(sensor_id, value, timestamp)
        except ValueError:
            pass


    def retrieve_measurement(self, key):
        if self.strategy == 'full':
            for node in self.nodes:
                if node.is_alive():
                    result = node.read(key)
                    if result is not None:
                        return {'value': result, 'message': f'Retrieved from node {node.node_id}'}
        elif self.strategy == 'consistent':
            node = self.hash_ring.get_node(key)
            if node and node.is_alive():
                result = node.read(key)
                if result is not None:
                    return {'value': result, 'message': f'Retrieved from node {node.node_id}'}
        return {'value': None, 'message': 'Measurement not found or all nodes are down'}

    def delete_measurement(self, key):
        for node in self.nodes:
            node.delete(key)

    def measurement_exists(self, key):
        for node in self.nodes:
            if node.is_alive() and node.key_exists(key):
                return True
        return False

    def fail_node(self, node_id):
        if 0 <= node_id < len(self.nodes):
            node = self.nodes[node_id]
            node.fail()
            if self.strategy == 'consistent':
                self.hash_ring.redistribute_measurements(node)

    def recover_node(self, node_id):
        if 0 <= node_id < len(self.nodes):
            node = self.nodes[node_id]
            node.recover(self.nodes, self.strategy)
            if self.strategy == 'consistent':
                print(f"Recovering node {node_id}...")
                self.hash_ring.recover_node(node)

    def get_storage_status(self):
        return [
            {
                'node_id': node.node_id,
                'status': 'alive' if node.is_alive() else 'dead',
                'port': node.port
            }
            for node in self.nodes
        ]

    def get_responsible_nodes(self, key):
        if self.strategy == 'consistent' and self.hash_ring:
            return self.hash_ring.get_nodes_for_key(key)
        else:
            return None
        
class AlertManager:
    def __init__(self):
        self.thresholds = {}  # {sensor_id: soglia}
        self.alerts = []      # Lista delle allerte generate

    def set_threshold(self, sensor_id, threshold):
        self.thresholds[sensor_id] = float(threshold)

    def check_for_anomaly(self, sensor_id, value, timestamp):
        try:
            threshold = self.thresholds.get(sensor_id)
            if threshold is not None and float(value) > threshold:
                alert = {
                    'sensor_id': sensor_id,
                    'value': float(value),
                    'threshold': threshold,
                    'timestamp': timestamp,
                    'message': 'Anomaly detected: value exceeds threshold'
                }
                self.alerts.append(alert)
                print(f"[ALERT] {alert}")
        except ValueError:
            pass  # Ignora valori non numerici

    def get_alerts(self):
        return self.alerts

