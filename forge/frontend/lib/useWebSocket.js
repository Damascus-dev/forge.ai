"use client";
import { useEffect, useRef, useCallback, useState } from "react";

/**
 * WebSocket hook for real-time experiment event streaming
 * Connects to backend WebSocket endpoint and dispatches events
 */
export function useExperimentWebSocket(experimentId, {
  onEvent = () => {},
  onChaosUpdate = () => {},
  onAgentUpdate = () => {},
  onNodeUpdate = () => {},
  onReconnect = () => {},
  enabled = true,
} = {}) {
  const wsRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);
  const [connected, setConnected] = useState(false);
  const [lastEvent, setLastEvent] = useState(null);
  const reconnectAttempt = useRef(0);

  const WS_URL = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000";

  const connect = useCallback(() => {
    if (!experimentId || !enabled) return;

    const ws = new WebSocket(`${WS_URL}/api/v1/experiments/${experimentId}/ws`);

    ws.onopen = () => {
      setConnected(true);
      reconnectAttempt.current = 0;
      onReconnect();
    };

    ws.onmessage = (msg) => {
      try {
        const data = JSON.parse(msg.data);
        setLastEvent(data);

        switch (data.type) {
          case "event":
            onEvent(data.payload);
            break;
          case "chaos":
            onChaosUpdate(data.payload);
            break;
          case "agent_state":
            onAgentUpdate(data.payload);
            break;
          case "node_status":
            onNodeUpdate(data.payload);
            break;
        }
      } catch {
        // ignore malformed messages
      }
    };

    ws.onclose = () => {
      setConnected(false);
      wsRef.current = null;
      const delay = Math.min(1000 * Math.pow(2, reconnectAttempt.current), 30000);
      reconnectAttempt.current++;
      reconnectTimeoutRef.current = setTimeout(connect, delay);
    };

    ws.onerror = () => {
      ws.close();
    };

    wsRef.current = ws;
  }, [experimentId, enabled, onEvent, onChaosUpdate, onAgentUpdate, onNodeUpdate, onReconnect, WS_URL]);

  useEffect(() => {
    connect();
    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
    };
  }, [connect]);

  const send = useCallback((data) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(data));
    }
  }, []);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    setConnected(false);
  }, []);

  return { connected, lastEvent, send, disconnect };
}

/**
 * Hook that automatically updates experiment state from WebSocket
 * Integrates with the flow store and experiment page state
 */
export function useRealtimeExperiment(id, {
  onEvent,
  onChaosUpdate,
  onAgentUpdate,
  setNodes,
  setActiveChaos,
  setAgentState,
  enabled = true,
} = {}) {
  const ws = useExperimentWebSocket(id, {
    onEvent: (event) => {
      if (onEvent) onEvent(event);

      if (event.event_type?.startsWith("agent_") && setAgentState) {
        setAgentState((prev) => ({
          ...prev,
          state: event.event_type.replace("agent_", ""),
          observation: event.data?.observation,
          decision: event.data?.decision,
          action: event.data?.action,
        }));
      }
    },
    onChaosUpdate: (chaos) => {
      if (onChaosUpdate) onChaosUpdate(chaos);
      if (setActiveChaos) {
        setActiveChaos((prev) => ({
          ...prev,
          [chaos.nodeId]: { type: chaos.type, params: chaos.params, startTime: Date.now() },
        }));
      }
    },
    onAgentUpdate: (agentState) => {
      if (onAgentUpdate) onAgentUpdate(agentState);
      if (setAgentState) {
        setAgentState((prev) => ({ ...prev, ...agentState }));
      }
    },
    onNodeUpdate: (nodeStatus) => {
      if (setNodes) {
        setNodes((prev) =>
          prev.map((n) =>
            n.id === nodeStatus.id ? { ...n, status: nodeStatus.status } : n
          )
        );
      }
    },
    enabled,
  });

  return ws;
}
