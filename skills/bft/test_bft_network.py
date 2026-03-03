#!/usr/bin/env python3
"""test_bft_network.py - Tests for BFT network."""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from skills.bft.bft_network import BFTNetwork, BFTNode, Message, ConsensusState


class TestBFTNode(unittest.TestCase):
    """Test BFT Node."""
    
    def test_node_creation(self):
        node = BFTNode("node-1")
        
        self.assertEqual(node.node_id, "node-1")
        self.assertFalse(node.is_primary)
        self.assertEqual(node.view, 0)
        self.assertEqual(node.state, ConsensusState.IDLE)
    
    def test_node_reset(self):
        node = BFTNode("node-1")
        node.view = 5
        node.state = ConsensusState.COMMIT
        node.message_log.append(Message("test", "node-1", 0, 0, "digest"))
        
        node.reset()
        
        self.assertEqual(node.view, 5)  # View not reset
        self.assertEqual(node.state, ConsensusState.IDLE)
        self.assertEqual(len(node.message_log), 0)


class TestMessage(unittest.TestCase):
    """Test Message."""
    
    def test_message_creation(self):
        msg = Message(
            msg_type="pre_prepare",
            node_id="node-1",
            view=0,
            sequence=1,
            digest="abc123"
        )
        
        self.assertEqual(msg.msg_type, "pre_prepare")
        self.assertEqual(msg.node_id, "node-1")
        self.assertEqual(msg.view, 0)
        self.assertEqual(msg.sequence, 1)
        self.assertEqual(msg.digest, "abc123")
    
    def test_message_serialization(self):
        msg = Message(
            msg_type="prepare",
            node_id="node-1",
            view=0,
            sequence=1,
            digest="abc123",
            payload={"key": "value"}
        )
        
        data = msg.to_dict()
        restored = Message.from_dict(data)
        
        self.assertEqual(restored.msg_type, msg.msg_type)
        self.assertEqual(restored.node_id, msg.node_id)
        self.assertEqual(restored.digest, msg.digest)


class TestBFTNetwork(unittest.TestCase):
    """Test BFT Network."""
    
    def setUp(self):
        self.nodes = ["node-1", "node-2", "node-3", "node-4"]
        self.network = BFTNetwork("node-1", self.nodes, f=1)
    
    def test_network_creation(self):
        self.assertEqual(self.network.node_id, "node-1")
        self.assertEqual(len(self.network.nodes), 4)
        self.assertEqual(self.network.f, 1)
    
    def test_start_stop(self):
        self.network.start()
        self.assertTrue(self.network._running)
        
        self.network.stop()
        self.assertFalse(self.network._running)
    
    def test_is_primary(self):
        # node-1 is primary in view 0
        self.assertTrue(self.network.is_primary())
        
        # After view change, different node is primary
        self.network.view_change()
        self.assertFalse(self.network.is_primary())
    
    def test_propose_as_primary(self):
        self.network.start()
        
        result = self.network.propose("task-1", {"action": "compute", "data": [1, 2, 3]})
        
        self.assertTrue(result)
        self.network.stop()
    
    def test_propose_as_non_primary(self):
        self.network.view_change()  # node-1 is no longer primary
        
        result = self.network.propose("task-1", {"action": "compute"})
        
        self.assertFalse(result)
    
    def test_add_remove_node(self):
        self.network.add_node("node-5")
        self.assertIn("node-5", self.network.nodes)
        
        self.network.remove_node("node-5")
        self.assertNotIn("node-5", self.network.nodes)
    
    def test_get_status(self):
        status = self.network.get_status()
        
        self.assertEqual(status["node_id"], "node-1")
        self.assertEqual(status["view"], 0)
        self.assertEqual(status["nodes"], 4)
    
    def test_handle_pre_prepare(self):
        msg = Message(
            msg_type="pre_prepare",
            node_id="node-1",
            view=0,
            sequence=1,
            digest="test-digest",
            payload={"task_id": "task-1", "task": {}}
        )
        
        self.network.receive_message(msg)
        
        # Should have prepare message in log
        prepare_msgs = [m for m in self.network.node.message_log if m.msg_type == "prepare"]
        self.assertEqual(len(prepare_msgs), 1)
    
    def test_compute_digest(self):
        digest1 = self.network._compute_digest("task-1", {"a": 1})
        digest2 = self.network._compute_digest("task-1", {"a": 1})
        digest3 = self.network._compute_digest("task-2", {"a": 1})
        
        self.assertEqual(digest1, digest2)  # Same input = same digest
        self.assertNotEqual(digest1, digest3)  # Different input = different digest


if __name__ == "__main__":
    unittest.main()
