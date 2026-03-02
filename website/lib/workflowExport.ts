// lib/workflowExport.ts
// Serialisation utilities and cycle-detection for the workflow graph.
// WHY: Keeping export logic separate from UI components makes it independently
// testable and lets router.py integration evolve without touching React code.

import { Node, Edge } from 'reactflow';
import { WorkflowExport, WorkflowNode, WorkflowEdge } from '../types/workflow';

const SCHEMA_VERSION = '1.0.0';

// buildExportPayload: converts React Flow node/edge arrays into the
// WorkflowExport schema that OpenPango router.py understands.
function buildExportPayload(nodes: Node[], edges: Edge[]): WorkflowExport {
  const exportNodes: WorkflowNode[] = nodes.map((n) => ({
    id: n.id,
    skillType: n.data.skillType,
    label: n.data.label,
    config: n.data.config ?? {},
    position: n.position,
  }));

  const exportEdges: WorkflowEdge[] = edges.map((e) => ({
    id: e.id,
    source: e.source,
    target: e.target,
    sourceHandle: e.sourceHandle ?? null,
    targetHandle: e.targetHandle ?? null,
  }));

  return {
    version: SCHEMA_VERSION,
    nodes: exportNodes,
    edges: exportEdges,
  };
}

// exportToJSON: returns a pretty-printed JSON string.
export function exportToJSON(nodes: Node[], edges: Edge[]): string {
  return JSON.stringify(buildExportPayload(nodes, edges), null, 2);
}

// exportToYAML: returns a minimal hand-rolled YAML string.
// WHY: Avoiding a full yaml library dependency keeps the bundle lean.
// The output is intentionally simple — router.py uses PyYAML which accepts
// standard YAML 1.1 that this subset is compatible with.
export function exportToYAML(nodes: Node[], edges: Edge[]): string {
  const payload = buildExportPayload(nodes, edges);
  const lines: string[] = [`version: "${payload.version}"`, 'nodes:'];

  for (const node of payload.nodes) {
    lines.push(`  - id: "${node.id}"`);
    lines.push(`    skillType: "${node.skillType}"`);
    lines.push(`    label: "${node.label}"`);
    lines.push(`    position:`);
    lines.push(`      x: ${Math.round(node.position.x)}`);
    lines.push(`      y: ${Math.round(node.position.y)}`);
    lines.push(`    config:`);
    for (const [key, val] of Object.entries(node.config)) {
      // Escape single quotes in values
      const safe = String(val).replace(/'/g, "''");
      lines.push(`      ${key}: '${safe}'`);
    }
  }

  lines.push('edges:');
  for (const edge of payload.edges) {
    lines.push(`  - id: "${edge.id}"`);
    lines.push(`    source: "${edge.source}"`);
    lines.push(`    target: "${edge.target}"`);
    if (edge.sourceHandle) lines.push(`    sourceHandle: "${edge.sourceHandle}"`);
    if (edge.targetHandle) lines.push(`    targetHandle: "${edge.targetHandle}"`);
  }

  return lines.join('\n');
}

// detectCycles: returns true if the directed graph formed by edges contains
// a cycle. Uses iterative DFS with three-colour marking.
// WHY: OpenPango executes skills sequentially in topological order;
// a cycle would cause an infinite loop at runtime.
export function detectCycles(nodes: Node[], edges: Edge[]): boolean {
  // Build adjacency list
  const adj: Map<string, string[]> = new Map();
  for (const node of nodes) {
    adj.set(node.id, []);
  }
  for (const edge of edges) {
    const neighbours = adj.get(edge.source);
    if (neighbours) neighbours.push(edge.target);
  }

  // 0 = white (unvisited), 1 = grey (in stack), 2 = black (done)
  const colour: Map<string, number> = new Map();
  for (const node of nodes) colour.set(node.id, 0);

  const stack: Array<{ id: string; childIndex: number }> = [];

  for (const node of nodes) {
    if (colour.get(node.id) !== 0) continue;

    stack.push({ id: node.id, childIndex: 0 });
    colour.set(node.id, 1);

    while (stack.length > 0) {
      const top = stack[stack.length - 1];
      const children = adj.get(top.id) ?? [];

      if (top.childIndex < children.length) {
        const child = children[top.childIndex];
        top.childIndex++;

        if (colour.get(child) === 1) {
          // Back edge found → cycle
          return true;
        }
        if (colour.get(child) === 0) {
          colour.set(child, 1);
          stack.push({ id: child, childIndex: 0 });
        }
      } else {
        colour.set(top.id, 2);
        stack.pop();
      }
    }
  }

  return false;
}

// importFromJSON: parses a previously exported JSON string back into
// React Flow nodes and edges so the graph can be restored.
export function importFromJSON(json: string): { nodes: Node[]; edges: Edge[] } {
  const payload: WorkflowExport = JSON.parse(json);

  const nodes: Node[] = payload.nodes.map((n) => ({
    id: n.id,
    type: 'skill',
    position: n.position,
    data: {
      skillType: n.skillType,
      label: n.label,
      config: n.config,
    },
  }));

  const edges: Edge[] = payload.edges.map((e) => ({
    id: e.id,
    source: e.source,
    target: e.target,
    sourceHandle: e.sourceHandle,
    targetHandle: e.targetHandle,
    animated: true,
  }));

  return { nodes, edges };
}
