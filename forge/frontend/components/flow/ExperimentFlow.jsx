"use client";

import ReactFlow, {
  MiniMap,
  Controls,
  Background,
  useNodesState,
  useEdgesState,
} from "reactflow";
import "reactflow/dist/style.css";
import { useEffect } from "react";
import { ExperimentNode, SandboxNode, AgentNode, EventNode } from "./nodes";
import { ChaosIndicator, MetricsOverlay } from "./ChaosVisualization";
import { useFlowStore } from "@/lib/flow/store";
import {
  createExperimentNode,
  createSandboxNodes,
  createAgentNode,
  createEdge,
  NODE_TYPES,
  EDGE_TYPES,
} from "@/lib/flow/types";

const nodeTypes = {
  [NODE_TYPES.EXPERIMENT]: ExperimentNode,
  [NODE_TYPES.SANDBOX_NODE]: SandboxNode,
  [NODE_TYPES.AGENT]: AgentNode,
  [NODE_TYPES.EVENT]: EventNode,
};

/**
 * ExperimentFlow - main visualization component
 * Renders experiment topology, nodes, chaos effects, and agent state
 */
export default function ExperimentFlow({ exp, nodes = [], agentId = null, activeChaos = {} }) {
  const [flowNodes, setFlowNodes, onNodesChange] = useNodesState([]);
  const [flowEdges, setFlowEdges, onEdgesChange] = useEdgesState([]);
  const store = useFlowStore();

  // Initialize flow graph when experiment or nodes change
  useEffect(() => {
    if (!exp) return;

    const newNodes = [];
    const newEdges = [];

    // 1. Create experiment node at center
    const expNode = createExperimentNode(exp);
    newNodes.push(expNode);

    // 2. Create sandbox nodes in a circle around experiment
    if (nodes.length > 0) {
      const sandboxNodes = nodes.map((n, i) => {
        const angle = (i / nodes.length) * 2 * Math.PI;
        const radius = 250;
        const x = radius * Math.cos(angle);
        const y = radius * Math.sin(angle) + 150;
        return {
          id: `node-${n.id}`,
          data: {
            label: n.name,
            status: n.status,
            type: "sandbox_node",
          },
          position: { x, y },
          type: NODE_TYPES.SANDBOX_NODE,
          style: {
            background: n.status === "running" ? "#22c55e" : "#ef4444",
          },
        };
      });
      newNodes.push(...sandboxNodes);

      // Connect experiment to each sandbox node
      sandboxNodes.forEach((n) => {
        newEdges.push(createEdge(`exp-${exp.id}`, n.id, EDGE_TYPES.COMMUNICATION));
      });
    }

    // 3. Add agent node if active
    if (agentId) {
      const agentState = store.agentStates[agentId] || {};
      const agentNode = createAgentNode(agentId, agentState.state || "idle");
      agentNode.position = { x: -300, y: 150 };
      newNodes.push(agentNode);

      // Connect agent to experiment
      newEdges.push(createEdge(`agent-${agentId}`, `exp-${exp.id}`, EDGE_TYPES.COMMUNICATION, "observes"));
    }

    // 4. Add chaos effect edges
    Object.entries(activeChaos).forEach(([nodeId, chaos]) => {
      newEdges.push(
        createEdge(`exp-${exp.id}`, nodeId, EDGE_TYPES.CHAOS_EFFECT, `${chaos.type}`)
      );
    });

    setFlowNodes(newNodes);
    setFlowEdges(newEdges);
  }, [exp, nodes, agentId, activeChaos, store, setFlowNodes, setFlowEdges]);

  if (!exp) {
    return (
      <div className="w-full h-96 flex items-center justify-center bg-gray-50 rounded-lg border border-gray-200">
        <p className="text-gray-500">No experiment loaded</p>
      </div>
    );
  }

  return (
    <div className="w-full h-96 rounded-lg border border-gray-200 bg-white overflow-hidden relative">
      <ReactFlow
        nodes={flowNodes}
        edges={flowEdges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        nodeTypes={nodeTypes}
      >
        <Background color="#aaa" gap={16} />
        <Controls />
        <MiniMap />
      </ReactFlow>
      <MetricsOverlay exp={exp} />
      {Object.keys(activeChaos).length > 0 && (
        <div className="absolute bottom-4 left-4 text-xs space-y-1 pointer-events-none">
          {Object.entries(activeChaos).map(([nodeId, chaos]) => (
            <div key={nodeId} className="text-orange-600 font-semibold animate-pulse">
              {chaos.type.toUpperCase()} on {nodeId}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
