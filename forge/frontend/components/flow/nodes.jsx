"use client";

import { memo } from "react";
import { Handle, Position } from "reactflow";

/**
 * Experiment node - shows overall experiment status
 */
export const ExperimentNode = memo(({ data, isConnecting }) => {
  return (
    <div className="px-4 py-3 rounded-lg border-2 min-w-48 shadow-md bg-white">
      <Handle type="target" position={Position.Top} />

      <div className="flex items-center justify-between mb-2">
        <h3 className="font-bold text-sm">{data.label}</h3>
        <span
          className={`text-xs font-semibold px-2 py-1 rounded ${
            data.status === "running"
              ? "bg-green-100 text-green-800"
              : data.status === "pending"
                ? "bg-yellow-100 text-yellow-800"
                : "bg-red-100 text-red-800"
          }`}
        >
          {data.status}
        </span>
      </div>

      <div className="text-xs text-gray-600 space-y-1">
        <p>Nodes: {data.nodeCount}</p>
      </div>

      <Handle type="source" position={Position.Bottom} />
    </div>
  );
});
ExperimentNode.displayName = "ExperimentNode";

/**
 * Sandbox node - shows individual container status
 */
export const SandboxNode = memo(({ data, isConnecting, selected }) => {
  return (
    <div
      className={`px-3 py-2 rounded-lg border-2 min-w-40 text-center ${
        selected
          ? "border-blue-500 bg-blue-50 shadow-lg"
          : "border-gray-300 bg-white shadow"
      }`}
    >
      <Handle type="target" position={Position.Top} />

      <p className="font-semibold text-xs">{data.label}</p>
      <p
        className={`text-xs mt-1 px-2 py-1 rounded inline-block ${
          data.status === "running"
            ? "bg-green-100 text-green-700"
            : data.status === "pending"
              ? "bg-yellow-100 text-yellow-700"
              : "bg-red-100 text-red-700"
        }`}
      >
        {data.status}
      </p>

      <Handle type="source" position={Position.Bottom} />
    </div>
  );
});
SandboxNode.displayName = "SandboxNode";

/**
 * Agent node - shows agent state (observe → reason → act)
 */
export const AgentNode = memo(({ data, selected }) => {
  const stateColors = {
    idle: "bg-gray-100 text-gray-700",
    observing: "bg-blue-100 text-blue-700",
    reasoning: "bg-amber-100 text-amber-700",
    acting: "bg-purple-100 text-purple-700",
    complete: "bg-green-100 text-green-700",
  };

  return (
    <div
      className={`px-4 py-3 rounded-lg border-2 min-w-48 ${
        selected
          ? "border-blue-500 bg-blue-50 shadow-lg"
          : "border-gray-300 bg-white shadow"
      }`}
    >
      <Handle type="target" position={Position.Left} />

      <div className="flex items-center justify-between mb-2">
        <h3 className="font-bold text-sm">{data.label}</h3>
        <span className={`text-xs font-semibold px-2 py-1 rounded ${stateColors[data.state] || stateColors.idle}`}>
          {data.state}
        </span>
      </div>

      {data.step && <p className="text-xs text-gray-600">Step: {data.step}</p>}

      {data.observation && (
        <p className="text-xs text-gray-700 mt-2 max-w-xs truncate">Obs: {data.observation}</p>
      )}

      <Handle type="source" position={Position.Right} />
    </div>
  );
});
AgentNode.displayName = "AgentNode";

/**
 * Event node - shows discrete events in the timeline
 */
export const EventNode = memo(({ data }) => {
  const typeColors = {
    latency: "bg-orange-100 text-orange-700",
    packet_loss: "bg-red-100 text-red-700",
    crash: "bg-red-200 text-red-800",
    disconnect: "bg-pink-100 text-pink-700",
    node_start: "bg-green-100 text-green-700",
    node_stop: "bg-gray-100 text-gray-700",
  };

  return (
    <div className={`px-3 py-2 rounded-lg border-2 border-gray-300 min-w-36 text-center shadow ${typeColors[data.eventType] || "bg-white"}`}>
      <p className="font-semibold text-xs">{data.eventType}</p>
      {data.timestamp && <p className="text-xs text-gray-600 mt-1">{new Date(data.timestamp).toLocaleTimeString()}</p>}
    </div>
  );
});
EventNode.displayName = "EventNode";
