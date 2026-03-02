// WorkflowBuilder.tsx
// Main visual workflow builder component using React Flow.
// WHY: Issue #20 requires a drag-and-drop node editor so non-developers
// can compose OpenPango agent pipelines without writing code.

'use client';

import React, { useCallback, useState, useRef } from 'react';
import ReactFlow, {
  ReactFlowProvider,
  addEdge,
  useNodesState,
  useEdgesState,
  Controls,
  MiniMap,
  Background,
  Connection,
  Edge,
  Node,
  NodeTypes,
  BackgroundVariant,
  ReactFlowInstance,
} from 'reactflow';
import 'reactflow/dist/style.css';
import SkillNode from './SkillNode';
import { SKILL_DEFINITIONS, SkillType } from '../types/workflow';
import { exportToJSON, exportToYAML, detectCycles } from '../lib/workflowExport';

// Register custom node types so React Flow renders SkillNode for all agent skills.
// WHY: React Flow requires explicit nodeTypes mapping to use custom components.
const nodeTypes: NodeTypes = {
  skill: SkillNode,
};

let nodeIdCounter = 1;
const generateId = () => `node_${nodeIdCounter++}`;

export default function WorkflowBuilder() {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [rfInstance, setRfInstance] = useState<ReactFlowInstance | null>(null);
  const [exportError, setExportError] = useState<string | null>(null);
  const [exportOutput, setExportOutput] = useState<string | null>(null);
  const [exportFormat, setExportFormat] = useState<'json' | 'yaml'>('json');
  const reactFlowWrapper = useRef<HTMLDivElement>(null);

  // onConnect: called when user draws an edge between two node ports.
  // WHY: We need to validate that the source skill output type is compatible
  // with the target skill input type before accepting the connection.
  const onConnect = useCallback(
    (params: Connection) => {
      const sourceNode = nodes.find((n) => n.id === params.source);
      const targetNode = nodes.find((n) => n.id === params.target);
      if (!sourceNode || !targetNode) return;

      const sourceDef = SKILL_DEFINITIONS[sourceNode.data.skillType as SkillType];
      const targetDef = SKILL_DEFINITIONS[targetNode.data.skillType as SkillType];

      // Validate output/input type compatibility.
      // WHY: Prevents nonsensical pipelines like Image output → Email subject input.
      if (
        sourceDef?.outputType &&
        targetDef?.inputType &&
        sourceDef.outputType !== 'any' &&
        targetDef.inputType !== 'any' &&
        sourceDef.outputType !== targetDef.inputType
      ) {
        setExportError(
          `Type mismatch: "${sourceDef.label}" outputs "${sourceDef.outputType}" but "${targetDef.label}" expects "${targetDef.inputType}".`
        );
        return;
      }

      setExportError(null);
      setEdges((eds) => addEdge({ ...params, animated: true }, eds));
    },
    [nodes, setEdges]
  );

  // onDragOver: allow drop events inside the React Flow canvas.
  const onDragOver = useCallback((event: React.DragEvent) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = 'move';
  }, []);

  // onDrop: convert the dropped skill type into a React Flow node.
  // WHY: Dragging from the sidebar palette and dropping on the canvas is the
  // primary UX for adding skills to the pipeline.
  const onDrop = useCallback(
    (event: React.DragEvent) => {
      event.preventDefault();
      if (!reactFlowWrapper.current || !rfInstance) return;

      const skillType = event.dataTransfer.getData('application/reactflow-skill') as SkillType;
      if (!skillType || !SKILL_DEFINITIONS[skillType]) return;

      const bounds = reactFlowWrapper.current.getBoundingClientRect();
      const position = rfInstance.screenToFlowPosition({
        x: event.clientX - bounds.left,
        y: event.clientY - bounds.top,
      });

      const def = SKILL_DEFINITIONS[skillType];
      const newNode: Node = {
        id: generateId(),
        type: 'skill',
        position,
        data: {
          skillType,
          label: def.label,
          config: { ...def.defaultConfig },
          inputType: def.inputType,
          outputType: def.outputType,
          color: def.color,
        },
      };

      setNodes((nds) => nds.concat(newNode));
    },
    [rfInstance, setNodes]
  );

  // handleExport: validate graph then serialise to JSON or YAML.
  // WHY: The exported file must be parseable by OpenPango router.py.
  const handleExport = useCallback(() => {
    setExportError(null);
    setExportOutput(null);

    if (nodes.length === 0) {
      setExportError('Add at least one skill node before exporting.');
      return;
    }

    // Cycle detection — infinite loops must be rejected before execution.
    if (detectCycles(nodes, edges)) {
      setExportError('Circular dependency detected. Remove the cycle before exporting.');
      return;
    }

    const output =
      exportFormat === 'yaml' ? exportToYAML(nodes, edges) : exportToJSON(nodes, edges);
    setExportOutput(output);
  }, [nodes, edges, exportFormat]);

  const handleClear = useCallback(() => {
    setNodes([]);
    setEdges([]);
    setExportOutput(null);
    setExportError(null);
  }, [setNodes, setEdges]);

  return (
    <div className="flex h-screen w-full bg-gray-950 text-white">
      {/* Sidebar skill palette */}
      <aside className="w-56 flex-shrink-0 bg-gray-900 border-r border-gray-700 flex flex-col p-3 gap-2 overflow-y-auto">
        <h2 className="text-xs font-semibold uppercase tracking-widest text-gray-400 mb-2">
          Skills
        </h2>
        {(Object.keys(SKILL_DEFINITIONS) as SkillType[]).map((skillType) => {
          const def = SKILL_DEFINITIONS[skillType];
          return (
            <div
              key={skillType}
              className="rounded-lg px-3 py-2 cursor-grab active:cursor-grabbing text-sm font-medium shadow"
              style={{ backgroundColor: def.color, color: '#fff' }}
              draggable
              onDragStart={(e) => {
                e.dataTransfer.setData('application/reactflow-skill', skillType);
                e.dataTransfer.effectAllowed = 'move';
              }}
              title={`Drag to add ${def.label} skill`}
            >
              {def.icon} {def.label}
            </div>
          );
        })}
      </aside>

      {/* Main canvas area */}
      <div className="flex-1 flex flex-col">
        {/* Toolbar */}
        <div className="flex items-center gap-3 px-4 py-2 bg-gray-900 border-b border-gray-700">
          <span className="font-bold text-lg tracking-tight">OpenPango Workflow Builder</span>
          <div className="flex-1" />
          <select
            className="bg-gray-800 border border-gray-600 rounded px-2 py-1 text-sm"
            value={exportFormat}
            onChange={(e) => setExportFormat(e.target.value as 'json' | 'yaml')}
          >
            <option value="json">Export as JSON</option>
            <option value="yaml">Export as YAML</option>
          </select>
          <button
            onClick={handleExport}
            className="bg-green-600 hover:bg-green-500 rounded px-4 py-1 text-sm font-semibold transition-colors"
          >
            Export
          </button>
          <button
            onClick={handleClear}
            className="bg-red-700 hover:bg-red-600 rounded px-4 py-1 text-sm font-semibold transition-colors"
          >
            Clear
          </button>
        </div>

        {/* React Flow canvas */}
        <div className="flex-1" ref={reactFlowWrapper}>
          <ReactFlowProvider>
            <ReactFlow
              nodes={nodes}
              edges={edges}
              onNodesChange={onNodesChange}
              onEdgesChange={onEdgesChange}
              onConnect={onConnect}
              onInit={setRfInstance}
              onDrop={onDrop}
              onDragOver={onDragOver}
              nodeTypes={nodeTypes}
              fitView
              deleteKeyCode="Delete"
            >
              <Controls />
              <MiniMap nodeColor={(n) => n.data?.color ?? '#6366f1'} />
              <Background variant={BackgroundVariant.Dots} gap={16} size={1} color="#374151" />
            </ReactFlow>
          </ReactFlowProvider>
        </div>

        {/* Export output / error panel */}
        {(exportOutput || exportError) && (
          <div
            className={`border-t px-4 py-3 text-sm font-mono max-h-48 overflow-y-auto ${
              exportError
                ? 'border-red-600 bg-red-950 text-red-300'
                : 'border-gray-700 bg-gray-900 text-green-300'
            }`}
          >
            {exportError ? (
              <p>⚠ {exportError}</p>
            ) : (
              <pre className="whitespace-pre-wrap break-all">{exportOutput}</pre>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
