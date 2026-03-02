/**
 * A2A Communication Protocol Integration Tests
 */

const { execSync, spawn } = require('child_process');
const path = require('path');
const fs = require('fs');

const A2A_DIR = path.join(__dirname, '../skills/a2a');
const REGISTRY_PATH = path.join(process.env.HOME, '.opеnclaw', 'workspace', 'agent_registry.json');

function runPython(script, args = []) {
  const result = execSync(`python3 ${path.join(A2A_DIR, script)} ${args.join(' ')}`, {
    encoding: 'utf-8',
    timeout: 10000
  });
  return JSON.parse(result);
}

describe('A2A Communication Protocol', () => {
  
  beforeEach(() => {
    if (fs.existsSync(REGISTRY_PATH)) {
      fs.unlinkSync(REGISTRY_PATH);
    }
  });
  
  describe('Agent Registry', () => {
    
    test('should register an agent', () => {
      const result = runPython('agent_registry.py', [
        'register',
        '--name', 'TestAgent',
        '--capabilities', 'coding', 'research'
      ]);
      
      expect(result.status).toBe('registered');
      expect(result.name).toBe('TestAgent');
      expect(result.capabilities).toContain('coding');
    });
    
    test('should discover agents by capability', () => {
      runPython('agent_registry.py', ['register', '--name', 'Coder1', '--capabilities', 'coding']);
      runPython('agent_registry.py', ['register', '--name', 'Researcher1', '--capabilities', 'research']);
      
      const result = runPython('agent_registry.py', ['discover', '--capability', 'coding']);
      
      expect(result.count).toBe(1);
      expect(result.agents[0].name).toBe('Coder1');
    });
    
    test('should list all agents', () => {
      runPython('agent_registry.py', ['register', '--name', 'Agent1']);
      runPython('agent_registry.py', ['register', '--name', 'Agent2']);
      
      const result = runPython('agent_registry.py', ['list']);
      
      expect(result.count).toBe(2);
    });
    
    test('should update agent status', () => {
      runPython('agent_registry.py', ['register', '--id', 'test-agent-1']);
      const result = runPython('agent_registry.py', ['status', 'test-agent-1', 'busy']);
      
      expect(result.status).toBe('updated');
    });
    
    test('should handle heartbeat', () => {
      runPython('agent_registry.py', ['register', '--id', 'heartbeat-agent']);
      const result = runPython('agent_registry.py', ['heartbeat', 'heartbeat-agent']);
      
      expect(result.status).toBe('ok');
    });
    
    test('should unregister an agent', () => {
      runPython('agent_registry.py', ['register', '--id', 'unregister-test']);
      const result = runPython('agent_registry.py', ['unregister', 'unregister-test']);
      
      expect(result.status).toBe('unregistered');
    });
    
  });
  
  describe('Message Bus', () => {
    
    test('should create message bus server', () => {
      const socketPath = '/tmp/test_a2a_bus_' + Date.now() + '.sock';
      const result = execSync(
        `python3 -c "
import sys
sys.path.insert(0, '${A2A_DIR}')
from message_bus import MessageBus
import json
bus = MessageBus('${socketPath}')
bus.start_server()
print('Server started')
bus.stop()
"`,
        { encoding: 'utf-8', timeout: 5000 }
      );
      
      expect(result).toContain('started');
    }, 10000);
    
  });
  
  describe('Two Agent Communication', () => {
    
    test('should allow two agents to discover each other', () => {
      runPython('agent_registry.py', [
        'register',
        '--name', 'Agent1',
        '--capabilities', 'coding'
      ]);
      
      runPython('agent_registry.py', [
        'register',
        '--name', 'Agent2',
        '--capabilities', 'research'
      ]);
      
      const discover = runPython('agent_registry.py', ['discover', '--capability', 'research']);
      
      expect(discover.count).toBe(1);
      expect(discover.agents[0].name).toBe('Agent2');
    });
    
  });
  
});
