import os
import sys
import unittest
import time

# Aggiungi il percorso del progetto alla variabile sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.models import MeasurementReplicationManager

class TestPerformanceFull(unittest.TestCase):
    results = {}

    def setUp(self):
        self.range_to_test = 5
        self.nodes_db = 3
        self.replication_factor = 2
        self.replication_manager_full = MeasurementReplicationManager(
            num_nodes=self.nodes_db,
            strategy='full',
            replication_factor=self.replication_factor
        )

    def tearDown(self):
        for i in range(self.range_to_test):
            self.replication_manager_full.delete_measurement(f'key_{i}')

    def test_write_performance_full(self):
        start_time = time.time()
        for i in range(self.range_to_test):
            self.replication_manager_full.ingest_measurement(f'key_{i}', f'value_{i}')
        end_time = time.time()
        TestPerformanceFull.results['Write performance (full)'] = end_time - start_time

    def test_read_performance_full(self):
        for i in range(self.range_to_test):
            self.replication_manager_full.ingest_measurement(f'key_{i}', f'value_{i}')
        start_time = time.time()
        for i in range(self.range_to_test):
            self.replication_manager_full.retrieve_measurement(f'key_{i}')
        end_time = time.time()
        TestPerformanceFull.results['Read performance (full)'] = end_time - start_time

    def test_fail_recover_performance_full(self):
        for i in range(self.range_to_test):
            self.replication_manager_full.ingest_measurement(f'key_{i}', f'value_{i}')
        start_time = time.time()
        for node_id in range(self.nodes_db):
            self.replication_manager_full.fail_node(node_id)
        fail_end_time = time.time()
        TestPerformanceFull.results['Fail nodes performance (full)'] = fail_end_time - start_time

        start_time = time.time()
        for node_id in range(self.nodes_db):
            self.replication_manager_full.recover_node(node_id)
        recover_end_time = time.time()
        TestPerformanceFull.results['Recover nodes performance (full)'] = recover_end_time - start_time

    @classmethod
    def tearDownClass(cls):
        print("\n\n--- Performance Results Full Strategy ---")
        for test, duration in cls.results.items():
            print(f'{test}: {duration:.4f} seconds')


class TestPerformanceConsistent(unittest.TestCase):
    results = {}

    def setUp(self):
        self.range_to_test = 10
        self.nodes_db = 3
        self.replication_factor = 2
        self.replication_manager_consistent = MeasurementReplicationManager(
            num_nodes=self.nodes_db,
            strategy='consistent',
            replication_factor=self.replication_factor
        )

    def tearDown(self):
        for i in range(self.range_to_test):
            self.replication_manager_consistent.delete_measurement(f'key_{i}')

    def test_write_performance_consistent(self):
        start_time = time.time()
        for i in range(self.range_to_test):
            self.replication_manager_consistent.ingest_measurement(f'key_{i}', f'value_{i}')
        end_time = time.time()
        TestPerformanceConsistent.results['Write performance (consistent)'] = end_time - start_time

    def test_read_performance_consistent(self):
        for i in range(self.range_to_test):
            self.replication_manager_consistent.ingest_measurement(f'key_{i}', f'value_{i}')
        start_time = time.time()
        for i in range(self.range_to_test):
            self.replication_manager_consistent.retrieve_measurement(f'key_{i}')
        end_time = time.time()
        TestPerformanceConsistent.results['Read performance (consistent)'] = end_time - start_time

    def test_fail_recover_performance_consistent(self):
        for i in range(self.range_to_test):
            self.replication_manager_consistent.ingest_measurement(f'key_{i}', f'value_{i}')
        start_time = time.time()
        for node_id in range(self.nodes_db):
            self.replication_manager_consistent.fail_node(node_id)
        fail_end_time = time.time()
        TestPerformanceConsistent.results['Fail nodes performance (consistent)'] = fail_end_time - start_time

        start_time = time.time()
        for node_id in range(self.nodes_db):
            self.replication_manager_consistent.recover_node(node_id)
        recover_end_time = time.time()
        TestPerformanceConsistent.results['Recover nodes performance (consistent)'] = recover_end_time - start_time

    @classmethod
    def tearDownClass(cls):
        print("\n\n--- Performance Results Consistent Strategy ---")
        for test, duration in cls.results.items():
            print(f'{test}: {duration:.4f} seconds')


if __name__ == '__main__':
    unittest.main()
