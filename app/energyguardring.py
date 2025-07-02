import hashlib
import bisect

class EnergyGuardRing:
    def __init__(self, storage_nodes=None, replication_factor=None):
        self.replication_factor = replication_factor or len(storage_nodes)
        self.ring = dict()
        self.sorted_hashes = []
        self.temp_data_store = {}

        if storage_nodes:
            for node in storage_nodes:
                self.add_storage_node(node)

    def _hash(self, key):
        return int(hashlib.md5(key.encode('utf-8')).hexdigest(), 16)

    def add_storage_node(self, node):
        node_hash = self._hash(str(node.node_id))
        self.ring[node_hash] = node
        bisect.insort(self.sorted_hashes, node_hash)
        print(f"[EnergyGuard] Nodo storage {node.node_id} aggiunto all'anello.")

    def remove_storage_node(self, node):
        node_hash = self._hash(str(node.node_id))
        if node_hash in self.ring:
            del self.ring[node_hash]
            self.sorted_hashes.remove(node_hash)
            print(f"[EnergyGuard] Nodo storage {node.node_id} rimosso dall'anello.")

    def get_responsible_nodes(self, sensor_key):
        if not self.ring:
            return []

        hash_key = self._hash(sensor_key)
        idx = bisect.bisect(self.sorted_hashes, hash_key)

        selected_nodes = []
        used_ids = set()

        while len(selected_nodes) < self.replication_factor:
            if idx >= len(self.sorted_hashes):
                idx = 0
            node = self.ring[self.sorted_hashes[idx]]
            if node.node_id not in used_ids:
                selected_nodes.append(node)
                used_ids.add(node.node_id)
            idx += 1

        return selected_nodes

    # Alias used by MeasurementReplicationManager
    def get_nodes_for_key(self, key):
        """Return the list of nodes responsible for ``key``."""
        return self.get_responsible_nodes(key)

    def get_node(self, key):
        """Return the first alive node responsible for ``key``.

        If no responsible node is alive, ``None`` is returned.
        """
        for node in self.get_responsible_nodes(key):
            if node.is_alive():
                return node
        return None

    def get_next_active_node(self, key, exclude_node_id=None):
        if not self.ring:
            return None

        hash_key = self._hash(key)
        idx = bisect.bisect(self.sorted_hashes, hash_key)

        for i in range(len(self.sorted_hashes)):
            next_idx = (idx + i) % len(self.sorted_hashes)
            next_node = self.ring[self.sorted_hashes[next_idx]]
            if next_node.is_alive() and next_node.node_id != exclude_node_id:
                return next_node

        return None

    def redistribute_measurements(self, failed_node):
        next_node = self.get_next_active_node(f'{failed_node.node_id}:0', exclude_node_id=failed_node.node_id)
        if next_node:
            print(f"[EnergyGuard] Ridistribuzione delle misurazioni del nodo {failed_node.node_id} verso {next_node.node_id}.")
            for key, value in failed_node.get_all_data():
                if not next_node.key_exists(key):
                    next_node.write(key, value)
                    self.temp_data_store[key] = (next_node.node_id, value)

    def recover_node(self, recovered_node):
        print(f"[EnergyGuard] Recupero del nodo {recovered_node.node_id} iniziato.")

        keys_to_recover = [
            key for key, (temp_node_id, _) in self.temp_data_store.items()
            if temp_node_id != recovered_node.node_id
        ]

        for key in keys_to_recover:
            temp_node_id, value = self.temp_data_store[key]
            temp_node = self.get_node_by_id(temp_node_id)
            natural_nodes = self.get_responsible_nodes(key)

            if temp_node and temp_node_id != recovered_node.node_id:
                if temp_node not in natural_nodes:
                    temp_node.delete(key)

                if not recovered_node.key_exists(key):
                    recovered_node.write(key, value)

                del self.temp_data_store[key]

        print(f"[EnergyGuard] Recupero del nodo {recovered_node.node_id} completato.")

    def get_node_by_id(self, node_id):
        for node in self.ring.values():
            if node.node_id == node_id:
                return node
        return None
