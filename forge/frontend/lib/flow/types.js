/**
 * React Flow node and edge types for Forge visualization
 */

export const NODE_TYPES = {
  EXPERIMENT: 'experiment',
  SANDBOX_NODE: 'sandbox_node',
  AGENT: 'agent',
  EVENT: 'event',
};

export const EDGE_TYPES = {
  COMMUNICATION: 'communication',
  CHAOS_EFFECT: 'chaos_effect',
  REPLAY_FLOW: 'replay_flow',
};

export const NODE_COLORS = {
  pending: '#d4d4d8',
  running: '#22c55e',
  stopped: '#ef4444',
  healthy: '#22c55e',
  degraded: '#f97316',
  failed: '#ef4444',
};

export const AGENT_STATES = {
  IDLE: 'idle',
  OBSERVING: 'observing',
  REASONING: 'reasoning',
  ACTING: 'acting',
  COMPLETE: 'complete',
};

export const CHAOS_TYPES = {
  LATENCY: 'latency',
  PACKET_LOSS: 'packet_loss',
  CRASH: 'crash',
  DISCONNECT: 'disconnect',
};

/**
 * Create a default experiment node for React Flow
 */
export function createExperimentNode(exp) {
  return {
    id: `exp-${exp.id}`,
    data: {
      label: exp.name,
      status: exp.status,
      nodeCount: exp.node_count,
      type: 'experiment',
    },
    position: { x: 0, y: 0 },
    type: NODE_TYPES.EXPERIMENT,
    style: {
      background: NODE_COLORS[exp.status] || NODE_COLORS.pending,
      border: `2px solid ${NODE_COLORS[exp.status] || NODE_COLORS.pending}`,
    },
  };
}

/**
 * Create sandbox node items for React Flow
 */
export function createSandboxNodes(nodes, expId) {
  return nodes.map((n, i) => ({
    id: `node-${n.id}`,
    data: {
      label: n.name,
      status: n.status,
      type: 'sandbox_node',
    },
    position: { x: 200 + i * 150, y: 100 },
    type: NODE_TYPES.SANDBOX_NODE,
    parentNode: `exp-${expId}`,
    style: {
      background: NODE_COLORS[n.status] || NODE_COLORS.pending,
    },
  }));
}

/**
 * Create agent node
 */
export function createAgentNode(agentId, state = AGENT_STATES.IDLE) {
  const stateColors = {
    [AGENT_STATES.IDLE]: '#6b7280',
    [AGENT_STATES.OBSERVING]: '#3b82f6',
    [AGENT_STATES.REASONING]: '#f59e0b',
    [AGENT_STATES.ACTING]: '#8b5cf6',
    [AGENT_STATES.COMPLETE]: '#10b981',
  };

  return {
    id: `agent-${agentId}`,
    data: {
      label: `Agent ${agentId}`,
      state,
      type: 'agent',
    },
    position: { x: 600, y: 0 },
    type: NODE_TYPES.AGENT,
    style: {
      background: stateColors[state] || stateColors[AGENT_STATES.IDLE],
      color: '#fff',
    },
  };
}

/**
 * Create edge between nodes
 */
export function createEdge(source, target, type = EDGE_TYPES.COMMUNICATION, label = '') {
  return {
    id: `${source}-${target}`,
    source,
    target,
    type,
    label,
    animated: type === EDGE_TYPES.CHAOS_EFFECT,
    style: {
      stroke: type === EDGE_TYPES.CHAOS_EFFECT ? '#ef4444' : '#d4d4d8',
      strokeWidth: type === EDGE_TYPES.CHAOS_EFFECT ? 3 : 2,
    },
  };
}
