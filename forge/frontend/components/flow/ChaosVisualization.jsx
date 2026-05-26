"use client";

import { motion } from "framer-motion";

/**
 * ChaosIndicator - shows active fault injections on a node
 * Used as an overlay badge on sandbox nodes
 */
export function ChaosIndicator({ type, intensity = 0.5 }) {
  const icons = {
    latency: "⏱️",
    packet_loss: "📉",
    crash: "💥",
    disconnect: "🔌",
  };

  const colors = {
    latency: "bg-orange-500",
    packet_loss: "bg-red-500",
    crash: "bg-red-600",
    disconnect: "bg-pink-500",
  };

  return (
    <motion.div
      className={`absolute -top-2 -right-2 w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold text-white ${colors[type] || "bg-gray-500"} shadow-lg`}
      animate={{ scale: [1, 1.1, 1] }}
      transition={{ duration: 1, repeat: Infinity }}
      title={`${type}: ${Math.round(intensity * 100)}%`}
    >
      {icons[type] || "!"}
    </motion.div>
  );
}

/**
 * ChaosPanel - shows all active chaos injections in a session
 */
export function ChaosPanel({ activeChaos = {} }) {
  if (Object.keys(activeChaos).length === 0) {
    return null;
  }

  return (
    <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
      <h3 className="text-sm font-semibold text-red-900 mb-3">🌪️ Active Chaos Injections</h3>
      <div className="space-y-2">
        {Object.entries(activeChaos).map(([nodeId, chaos]) => (
          <motion.div
            key={nodeId}
            className="flex items-center justify-between bg-white border border-red-100 rounded p-2"
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
          >
            <span className="text-xs">
              <span className="font-mono text-gray-600">{nodeId}</span>
              <span className="mx-2 text-gray-400">→</span>
              <span className="font-semibold text-red-700">{chaos.type}</span>
            </span>
            {chaos.params && (
              <span className="text-xs text-gray-500 font-mono">
                {JSON.stringify(chaos.params)}
              </span>
            )}
          </motion.div>
        ))}
      </div>
    </div>
  );
}

/**
 * AgentStatePanel - shows agent observation, reasoning, and action
 */
export function AgentStatePanel({ agentId, state = {} }) {
  const stateToColor = {
    observing: "blue",
    reasoning: "amber",
    acting: "purple",
    complete: "green",
  };

  const color = stateToColor[state.state] || "gray";

  return (
    <motion.div
      className={`p-4 bg-${color}-50 border border-${color}-200 rounded-lg`}
      initial={{ opacity: 0, y: -10 }}
      animate={{ opacity: 1, y: 0 }}
    >
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-semibold text-gray-900">🤖 Agent Activity</h3>
        <span className={`text-xs font-bold px-2 py-1 rounded bg-${color}-200 text-${color}-800`}>
          {state.state || "idle"}
        </span>
      </div>

      {state.step && (
        <p className="text-xs text-gray-600 mb-2">
          <span className="font-mono">Step {state.step}</span>
        </p>
      )}

      {state.observation && (
        <div className="mb-3 p-2 bg-blue-100 rounded text-xs text-blue-900">
          <p className="font-semibold mb-1">📍 Observation:</p>
          <p className="whitespace-pre-wrap break-words">{state.observation}</p>
        </div>
      )}

      {state.decision && (
        <div className="mb-3 p-2 bg-amber-100 rounded text-xs text-amber-900">
          <p className="font-semibold mb-1">🧠 Decision:</p>
          <p className="whitespace-pre-wrap break-words">{state.decision}</p>
        </div>
      )}

      {state.action && (
        <div className="p-2 bg-purple-100 rounded text-xs text-purple-900">
          <p className="font-semibold mb-1">⚡ Action:</p>
          <p className="whitespace-pre-wrap break-words font-mono">{state.action}</p>
        </div>
      )}
    </motion.div>
  );
}

/**
 * MetricsOverlay - shows live metrics on flow visualization
 */
export function MetricsOverlay({ exp = {} }) {
  return (
    <div className="absolute top-4 right-4 bg-white rounded-lg shadow-lg p-3 text-xs space-y-1 z-10">
      <div className="flex items-center justify-between gap-4">
        <span className="text-gray-600">Status:</span>
        <span className="font-bold">{exp.status}</span>
      </div>
      {exp.node_count && (
        <div className="flex items-center justify-between gap-4">
          <span className="text-gray-600">Nodes:</span>
          <span className="font-bold">{exp.node_count}</span>
        </div>
      )}
      {exp.created_at && (
        <div className="flex items-center justify-between gap-4">
          <span className="text-gray-600">Runtime:</span>
          <span className="font-mono text-gray-500">
            {Math.round((Date.now() - new Date(exp.created_at).getTime()) / 1000)}s
          </span>
        </div>
      )}
    </div>
  );
}
