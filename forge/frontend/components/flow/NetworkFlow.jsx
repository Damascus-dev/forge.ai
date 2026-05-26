"use client";

import { motion } from "framer-motion";

/**
 * PacketAnimation - animated packet flowing along an edge
 */
function PacketAnimation({ duration = 1 }) {
  return (
    <motion.circle
      cx="0"
      cy="0"
      r="4"
      fill="#ef4444"
      initial={{ offsetDistance: "0%" }}
      animate={{ offsetDistance: "100%" }}
      transition={{ duration, repeat: Infinity }}
      style={{ offsetPath: "url(#edge-path)" }}
    />
  );
}

/**
 * AnimatedEdge - edge with packet flow animation
 * Shows communication between nodes
 */
export function AnimatedEdge({
  id,
  sourceX,
  sourceY,
  targetX,
  targetY,
  sourcePosition,
  targetPosition,
  isActive = false,
  packetCount = 1,
  label = "",
}) {
  if (!isActive) {
    // Static edge
    return (
      <g>
        <path
          d={`M ${sourceX} ${sourceY} L ${targetX} ${targetY}`}
          stroke="#d4d4d8"
          strokeWidth={2}
          fill="none"
        />
        {label && (
          <text
            x={(sourceX + targetX) / 2}
            y={(sourceY + targetY) / 2}
            fill="#6b7280"
            fontSize="12"
            textAnchor="middle"
            dy="-5"
          >
            {label}
          </text>
        )}
      </g>
    );
  }

  // Animated edge with packets
  const distance = Math.sqrt(
    Math.pow(targetX - sourceX, 2) + Math.pow(targetY - sourceY, 2)
  );
  const duration = distance / 100; // Speed based on distance

  return (
    <g>
      <defs>
        <path
          id={`edge-path-${id}`}
          d={`M ${sourceX} ${sourceY} L ${targetX} ${targetY}`}
        />
      </defs>

      {/* Base edge */}
      <path
        d={`M ${sourceX} ${sourceY} L ${targetX} ${targetY}`}
        stroke="#ef4444"
        strokeWidth={3}
        fill="none"
        strokeDasharray="5,5"
        opacity="0.5"
      />

      {/* Animated packets */}
      {Array.from({ length: packetCount }).map((_, i) => (
        <motion.circle
          key={i}
          cx={sourceX}
          cy={sourceY}
          r={4}
          fill="#ef4444"
          initial={{
            x: sourceX,
            y: sourceY,
          }}
          animate={{
            x: targetX,
            y: targetY,
          }}
          transition={{
            duration: duration + 0.5,
            repeat: Infinity,
            delay: (i / packetCount) * duration,
          }}
        />
      ))}

      {/* Label */}
      {label && (
        <text
          x={(sourceX + targetX) / 2}
          y={(sourceY + targetY) / 2}
          fill="#ef4444"
          fontSize="12"
          textAnchor="middle"
          dy="-5"
          fontWeight="bold"
        >
          {label}
        </text>
      )}
    </g>
  );
}

/**
 * ConnectionIndicator - pulsing circle showing active connection
 */
export function ConnectionIndicator({ x, y, isActive = false }) {
  if (!isActive) return null;

  return (
    <motion.circle
      cx={x}
      cy={y}
      r={5}
      fill="none"
      stroke="#ef4444"
      strokeWidth={2}
      initial={{ r: 5, opacity: 1 }}
      animate={{ r: 15, opacity: 0 }}
      transition={{ duration: 1, repeat: Infinity }}
    />
  );
}

/**
 * NetworkFlowVisualization - shows packets flowing through the network
 */
export function NetworkFlowVisualization({
  events = [],
  currentTime = null,
  nodes = [],
  edges = [],
}) {
  // Find active communications at current time
  const getActiveConnections = () => {
    if (!currentTime) return {};

    const active = {};
    const timeWindow = 1000; // 1 second window

    events
      .filter((e) => {
        const eventTime = new Date(e.timestamp).getTime();
        return Math.abs(eventTime - currentTime) < timeWindow;
      })
      .forEach((event) => {
        if (event.source && event.data?.target) {
          const key = `${event.source}-${event.data.target}`;
          active[key] = (active[key] || 0) + 1;
        }
      });

    return active;
  };

  const activeConnections = getActiveConnections();

  return (
    <div className="relative w-full h-full bg-white rounded-lg border border-gray-200 overflow-hidden">
      <svg className="w-full h-full">
        {/* Render nodes with connection indicators */}
        {nodes.map((node) => (
          <g key={node.id}>
            {/* Node circle */}
            <circle
              cx={node.position?.x || 0}
              cy={node.position?.y || 0}
              r={20}
              fill="#3b82f6"
              opacity="0.7"
            />
            {/* Connection pulse */}
            {Object.keys(activeConnections).some(
              (conn) =>
                conn.startsWith(node.id) || conn.endsWith(node.id)
            ) && (
              <motion.circle
                cx={node.position?.x || 0}
                cy={node.position?.y || 0}
                r={20}
                fill="none"
                stroke="#ef4444"
                strokeWidth={2}
                initial={{ r: 20, opacity: 1 }}
                animate={{ r: 30, opacity: 0 }}
                transition={{ duration: 0.6, repeat: Infinity }}
              />
            )}
          </g>
        ))}

        {/* Render animated edges */}
        {edges.map((edge) => {
          const sourceNode = nodes.find((n) => n.id === edge.source);
          const targetNode = nodes.find((n) => n.id === edge.target);

          if (!sourceNode || !targetNode) return null;

          const isActive = activeConnections[`${edge.source}-${edge.target}`] > 0;

          return (
            <AnimatedEdge
              key={edge.id}
              id={edge.id}
              sourceX={sourceNode.position?.x || 0}
              sourceY={sourceNode.position?.y || 0}
              targetX={targetNode.position?.x || 0}
              targetY={targetNode.position?.y || 0}
              isActive={isActive}
              packetCount={activeConnections[`${edge.source}-${edge.target}`] || 1}
              label={edge.label}
            />
          );
        })}
      </svg>
    </div>
  );
}
