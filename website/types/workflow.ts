// types/workflow.ts
// Central type definitions and skill registry for the OpenPango workflow builder.
// WHY: Keeping skill definitions in one place means adding a new OpenPango skill
// only requires editing this file — all UI components derive from it automatically.

export type DataType = 'text' | 'url' | 'json' | 'email' | 'image' | 'any';

export type SkillType =
  | 'browser'
  | 'researcher'
  | 'dataAnalysis'
  | 'email'
  | 'summarizer'
  | 'codeRunner'
  | 'fileReader'
  | 'webhook';

export interface SkillDefinition {
  label: string;
  icon: string;
  /** Data type this skill outputs — used for connection compatibility checks */
  outputType: DataType;
  /** Data type this skill expects as primary input */
  inputType: DataType;
  /** Tailwind-compatible hex/named colour for the node header */
  color: string;
  /** Default configuration fields shown in the node config panel */
  defaultConfig: Record<string, string>;
  /** Human-readable description shown as tooltip */
  description: string;
}

// SKILL_DEFINITIONS is the single source of truth for all supported skills.
// router.py maps the `skillType` field to the matching Python skill class.
export const SKILL_DEFINITIONS: Record<SkillType, SkillDefinition> = {
  browser: {
    label: 'Browser',
    icon: '🌐',
    inputType: 'url',
    outputType: 'text',
    color: '#2563eb',
    description: 'Fetches a web page and returns its text content.',
    defaultConfig: {
      url: '',
      waitForSelector: '',
    },
  },
  researcher: {
    label: 'Researcher',
    icon: '🔍',
    inputType: 'text',
    outputType: 'json',
    color: '#7c3aed',
    description: 'Searches the web and returns structured research results.',
    defaultConfig: {
      query: '',
      maxResults: '5',
    },
  },
  dataAnalysis: {
    label: 'Data Analysis',
    icon: '📊',
    inputType: 'json',
    outputType: 'json',
    color: '#0891b2',
    description: 'Runs analysis or transformation on structured JSON data.',
    defaultConfig: {
      prompt: '',
    },
  },
  email: {
    label: 'Email',
    icon: '✉️',
    inputType: 'text',
    outputType: 'any',
    color: '#16a34a',
    description: 'Sends an email with the provided content.',
    defaultConfig: {
      to: '',
      subject: '',
      bodyTemplate: '',
    },
  },
  summarizer: {
    label: 'Summarizer',
    icon: '📝',
    inputType: 'text',
    outputType: 'text',
    color: '#d97706',
    description: 'Produces a concise summary of the input text using an LLM.',
    defaultConfig: {
      maxWords: '200',
      style: 'bullet',
    },
  },
  codeRunner: {
    label: 'Code Runner',
    icon: '⚙️',
    inputType: 'any',
    outputType: 'json',
    color: '#be185d',
    description: 'Executes a Python snippet and returns stdout as JSON.',
    defaultConfig: {
      language: 'python',
      code: '',
    },
  },
  fileReader: {
    label: 'File Reader',
    icon: '📂',
    inputType: 'any',
    outputType: 'text',
    color: '#92400e',
    description: 'Reads a local or remote file and returns its contents.',
    defaultConfig: {
      path: '',
      encoding: 'utf-8',
    },
  },
  webhook: {
    label: 'Webhook',
    icon: '🔗',
    inputType: 'any',
    outputType: 'json',
    color: '#374151',
    description: 'POSTs the input payload to an external HTTP endpoint.',
    defaultConfig: {
      url: '',
      method: 'POST',
      headers: '{}',
    },
  },
};

// WorkflowExport is the JSON schema that router.py consumes.
// WHY: Naming fields to match router.py conventions avoids a translation layer.
export interface WorkflowNode {
  id: string;
  skillType: SkillType;
  label: string;
  config: Record<string, string>;
  position: { x: number; y: number };
}

export interface WorkflowEdge {
  id: string;
  source: string;
  target: string;
  sourceHandle: string | null;
  targetHandle: string | null;
}

export interface WorkflowExport {
  version: string;
  nodes: WorkflowNode[];
  edges: WorkflowEdge[];
}
