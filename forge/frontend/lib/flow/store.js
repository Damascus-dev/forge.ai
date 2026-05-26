/**
 * Zustand store for React Flow visualization state
 */
import { create } from 'zustand';

export const useFlowStore = create((set) => ({
  // Nodes and edges
  nodes: [],
  edges: [],

  // Selected node/edge
  selectedNode: null,
  selectedEdge: null,

  // Visualization mode
  mode: 'live', // 'live' or 'replay'
  replayTime: null,

  // Chaos injections (active)
  activeChaos: {}, // { nodeId: { type, params, startTime } }

  // Agent states
  agentStates: {}, // { agentId: { state, step, observation, decision, action } }

  // Set nodes and edges
  setNodes: (nodes) => set({ nodes }),
  setEdges: (edges) => set({ edges }),

  // Update single node
  updateNode: (nodeId, data) =>
    set((state) => ({
      nodes: state.nodes.map((n) =>
        n.id === nodeId ? { ...n, data: { ...n.data, ...data } } : n
      ),
    })),

  // Select node
  selectNode: (nodeId) => set({ selectedNode: nodeId }),

  // Add chaos effect to node
  addChaos: (nodeId, chaosType, params) =>
    set((state) => ({
      activeChaos: {
        ...state.activeChaos,
        [nodeId]: { type: chaosType, params, startTime: Date.now() },
      },
    })),

  // Remove chaos effect
  removeChaos: (nodeId) =>
    set((state) => {
      const newChaos = { ...state.activeChaos };
      delete newChaos[nodeId];
      return { activeChaos: newChaos };
    }),

  // Update agent state
  updateAgentState: (agentId, stateUpdate) =>
    set((state) => ({
      agentStates: {
        ...state.agentStates,
        [agentId]: { ...state.agentStates[agentId], ...stateUpdate },
      },
    })),

  // Set mode
  setMode: (mode) => set({ mode }),

  // Reset
  reset: () =>
    set({
      nodes: [],
      edges: [],
      selectedNode: null,
      selectedEdge: null,
      mode: 'live',
      replayTime: null,
      activeChaos: {},
      agentStates: {},
    }),
}));
