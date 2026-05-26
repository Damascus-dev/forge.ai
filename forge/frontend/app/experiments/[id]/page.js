"use client";

import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import dynamic from "next/dynamic";
import {
  getExperiment, startExperiment, terminateExperiment,
  listNodes, getEvents, getTimeline, startReplay,
  injectFault, startAgent, runAgentStep, getAgentLogs,
} from "@/lib/api";

const ExperimentFlow = dynamic(
  () => import("@/components/flow/ExperimentFlow"),
  { ssr: false, loading: () => <div className="h-96 bg-gray-100 rounded-lg animate-pulse" /> }
);

const ChaosPanel = dynamic(
  () => import("@/components/flow/ChaosVisualization").then((m) => m.ChaosPanel),
  { ssr: false }
);

const AgentStatePanel = dynamic(
  () => import("@/components/flow/ChaosVisualization").then((m) => m.AgentStatePanel),
  { ssr: false }
);

const TABS = ["Overview", "Flow", "Events", "Replay", "Agent"];

export default function ExperimentPage() {
  const { id } = useParams();
  const [exp, setExp] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [tab, setTab] = useState("Overview");
  const [nodes, setNodes] = useState([]);
  const [events, setEvents] = useState([]);
  const [timeline, setTimeline] = useState(null);
  const [replayResult, setReplayResult] = useState(null);
  const [agentId, setAgentId] = useState(null);
  const [agentLogs, setAgentLogs] = useState([]);
  const [agentModel, setAgentModel] = useState("ollama/qwen2.5:0.5b");
  const [faultType, setFaultType] = useState("latency");
  const [faultParams, setFaultParams] = useState("{}");
  const [actionMsg, setActionMsg] = useState("");
  const [activeChaos, setActiveChaos] = useState({});
  const [agentState, setAgentState] = useState({});

  async function load() {
    try {
      const data = await getExperiment(id);
      setExp(data);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); }, [id]);

  async function loadNodes() {
    const data = await listNodes(id);
    setNodes(Array.isArray(data) ? data : []);
  }

  async function loadEvents() {
    const data = await getEvents(id);
    setEvents(Array.isArray(data) ? data : []);
  }

  async function loadTimeline() {
    try {
      const data = await getTimeline(id);
      setTimeline(data);
    } catch { setTimeline(null); }
  }

  async function handleStart() {
    setActionMsg("Starting...");
    const res = await startExperiment(id);
    setActionMsg(res.status);
    await load();
  }

  async function handleTerminate() {
    setActionMsg("Terminating...");
    const res = await terminateExperiment(id);
    setActionMsg(res.status);
    await load();
  }

  async function handleInjectFault(e) {
    e.preventDefault();
    const target = `node-${id}-0`;
    let params = {};
    try { params = JSON.parse(faultParams); } catch {}
    const res = await injectFault(id, target, faultType, params);
    setActionMsg(`Fault: ${res.status}`);
    
    // Track active chaos
    setActiveChaos((prev) => ({
      ...prev,
      [target]: { type: faultType, params, startTime: Date.now() },
    }));
  }

  async function handleStartAgent() {
    const res = await startAgent(id, agentModel);
    setAgentId(res.agent_id);
    setActionMsg(`Agent ${res.agent_id} started`);
  }

  async function handleAgentStep() {
    if (!agentId) return;
    const res = await runAgentStep(id, agentId);
    setActionMsg(`Step ${res.step} done`);
    const logs = await getAgentLogs(id, agentId);
    setAgentLogs(logs);
    
    // Track agent state (update from latest log)
    if (logs.length > 0) {
      const latest = logs[logs.length - 1];
      setAgentState({
        state: 'acting', // Simplified - would need better logic in full impl
        step: latest.step,
        observation: latest.observation,
        decision: latest.decision,
        action: latest.action,
      });
    }
  }

  async function handleReplay() {
    const res = await startReplay(id);
    setReplayResult(res);
  }

  if (loading) return <p className="text-zinc-400 text-sm">Loading...</p>;
  if (error) return <p className="text-red-500 text-sm">Error: {error}</p>;
  if (!exp) return <p className="text-zinc-400 text-sm">Not found</p>;

  return (
    <div className="max-w-4xl mx-auto">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h1 className="text-2xl font-bold">{exp.name}</h1>
          <p className="text-sm text-zinc-400">{exp.id} &middot; {exp.node_count} nodes</p>
        </div>
        <div className="flex gap-2">
          {exp.status === "pending" && (
            <button onClick={handleStart} className="px-4 py-2 bg-green-600 text-white rounded-lg text-sm font-medium hover:bg-green-500 transition-colors">
              Start
            </button>
          )}
          {exp.status === "running" && (
            <button onClick={handleTerminate} className="px-4 py-2 bg-red-600 text-white rounded-lg text-sm font-medium hover:bg-red-500 transition-colors">
              Terminate
            </button>
          )}
        </div>
      </div>

      {actionMsg && (
        <p className="mb-4 text-sm text-zinc-500 bg-zinc-100 px-3 py-1.5 rounded">{actionMsg}</p>
      )}

      <div className="flex gap-1 mb-6 border-b border-zinc-200">
        {TABS.map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
              tab === t
                ? "border-zinc-900 text-zinc-900"
                : "border-transparent text-zinc-400 hover:text-zinc-600"
            }`}
          >
            {t}
          </button>
        ))}
      </div>

      {tab === "Overview" && (
        <div className="space-y-6">
          <div className="p-4 border border-zinc-200 rounded-lg bg-white">
            <h2 className="text-sm font-semibold text-zinc-500 mb-2">Status</h2>
            <p className="text-lg font-medium">{exp.status}</p>
          </div>
          <div className="p-4 border border-zinc-200 rounded-lg bg-white">
            <h2 className="text-sm font-semibold text-zinc-500 mb-3">Nodes</h2>
            <button onClick={loadNodes} className="text-xs text-zinc-400 hover:text-zinc-600 mb-2">Refresh</button>
            {nodes.length === 0 ? (
              <p className="text-sm text-zinc-400">No nodes running. Start the experiment first.</p>
            ) : (
              <div className="space-y-1">
                {nodes.map((n) => (
                  <div key={n.id} className="flex items-center justify-between text-sm py-1 border-b border-zinc-100 last:border-0">
                    <span>{n.name}</span>
                    <span className="text-xs text-zinc-400">{n.status}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
          <div className="p-4 border border-zinc-200 rounded-lg bg-white">
            <h2 className="text-sm font-semibold text-zinc-500 mb-3">Inject Fault</h2>
            <form onSubmit={handleInjectFault} className="flex gap-2 items-end">
              <select
                value={faultType}
                onChange={(e) => setFaultType(e.target.value)}
                className="px-3 py-2 border border-zinc-200 rounded-lg text-sm"
              >
                <option value="latency">Latency</option>
                <option value="packet_loss">Packet Loss</option>
                <option value="crash">Crash</option>
                <option value="disconnect">Disconnect</option>
              </select>
              <input
                value={faultParams}
                onChange={(e) => setFaultParams(e.target.value)}
                className="flex-1 px-3 py-2 border border-zinc-200 rounded-lg text-sm font-mono"
                placeholder='{"delay_ms": 200}'
              />
              <button type="submit" className="px-4 py-2 bg-orange-600 text-white rounded-lg text-sm font-medium hover:bg-orange-500 transition-colors">
                Inject
              </button>
            </form>
          </div>
        </div>
      )}

      {tab === "Flow" && (
        <div className="space-y-4">
          <ExperimentFlow 
            exp={exp} 
            nodes={nodes} 
            agentId={agentId}
            activeChaos={activeChaos}
          />
          {Object.keys(activeChaos).length > 0 && <ChaosPanel activeChaos={activeChaos} />}
          {agentId && <AgentStatePanel agentId={agentId} state={agentState} />}
          <p className="text-sm text-gray-500">
            Visualization shows experiment topology. Use the toolbar to pan, zoom, and explore.
          </p>
        </div>
      )}

      {tab === "Events" && (
        <div className="p-4 border border-zinc-200 rounded-lg bg-white">
          <h2 className="text-sm font-semibold text-zinc-500 mb-3">Event Timeline</h2>
          <button onClick={loadEvents} className="text-xs text-zinc-400 hover:text-zinc-600 mb-2">Refresh</button>
          {events.length === 0 ? (
            <p className="text-sm text-zinc-400">No events yet.</p>
          ) : (
            <div className="space-y-1 max-h-96 overflow-y-auto">
              {events.map((e, i) => (
                <div key={e.id || i} className="flex items-start gap-3 text-sm py-2 border-b border-zinc-100 last:border-0">
                  <span className="text-xs text-zinc-400 whitespace-nowrap font-mono">
                    {new Date(e.timestamp).toLocaleTimeString()}
                  </span>
                  <span className="px-1.5 py-0.5 rounded bg-zinc-100 text-xs font-medium">{e.event_type}</span>
                  <span className="text-zinc-500 text-xs">{e.source}</span>
                  {e.data && Object.keys(e.data).length > 0 && (
                    <span className="text-xs text-zinc-400 font-mono">{JSON.stringify(e.data)}</span>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {tab === "Replay" && (
        <div className="p-4 border border-zinc-200 rounded-lg bg-white">
          <h2 className="text-sm font-semibold text-zinc-500 mb-3">Replay</h2>
          <button onClick={handleReplay} className="px-4 py-2 bg-zinc-900 text-white rounded-lg text-sm font-medium hover:bg-zinc-800 transition-colors mb-4">
            Replay Experiment
          </button>
          {replayResult && (
            <div className="text-sm space-y-1">
              <p>Events: {replayResult.event_count}</p>
              <div className="max-h-64 overflow-y-auto mt-2 space-y-1">
                {replayResult.timeline.map((t, i) => (
                  <div key={i} className="flex items-start gap-3 py-1.5 border-b border-zinc-100">
                    <span className="text-xs text-zinc-400 font-mono whitespace-nowrap">
                      {new Date(t.timestamp).toLocaleTimeString()}
                    </span>
                    <span className="px-1.5 py-0.5 rounded bg-zinc-100 text-xs font-medium">{t.type}</span>
                    <span className="text-xs text-zinc-500">{t.source}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
          <div className="mt-4">
            <h3 className="text-sm font-semibold text-zinc-500 mb-2">Timeline</h3>
            <button onClick={loadTimeline} className="text-xs text-zinc-400 hover:text-zinc-600 mb-2">Refresh</button>
            {timeline && timeline.timeline ? (
              <div className="max-h-64 overflow-y-auto space-y-1">
                {timeline.timeline.map((t, i) => (
                  <div key={i} className="flex items-start gap-3 py-1.5 border-b border-zinc-100 text-sm">
                    <span className="text-xs text-zinc-400 font-mono whitespace-nowrap">
                      {new Date(t.timestamp).toLocaleTimeString()}
                    </span>
                    <span className="px-1.5 py-0.5 rounded bg-zinc-100 text-xs font-medium">{t.type}</span>
                    <span className="text-xs text-zinc-500">{t.source}</span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-zinc-400">No timeline available.</p>
            )}
          </div>
        </div>
      )}

      {tab === "Agent" && (
        <div className="space-y-4">
          <div className="p-4 border border-zinc-200 rounded-lg bg-white">
            <h2 className="text-sm font-semibold text-zinc-500 mb-3">Agent Control</h2>
            {!agentId ? (
              <div className="flex gap-2 items-end">
                <div className="flex-1">
                  <label className="block text-xs font-medium text-zinc-500 mb-1">Model</label>
                  <input
                    value={agentModel}
                    onChange={(e) => setAgentModel(e.target.value)}
                    className="w-full px-3 py-2 border border-zinc-200 rounded-lg text-sm"
                    placeholder="ollama/qwen2.5:0.5b"
                  />
                </div>
                <button onClick={handleStartAgent} className="px-4 py-2 bg-zinc-900 text-white rounded-lg text-sm font-medium hover:bg-zinc-800 transition-colors">
                  Start Agent
                </button>
              </div>
            ) : (
              <div>
                <p className="text-sm mb-3">Agent: <span className="font-mono">{agentId}</span></p>
                <button onClick={handleAgentStep} className="px-4 py-2 bg-zinc-900 text-white rounded-lg text-sm font-medium hover:bg-zinc-800 transition-colors">
                  Run Step
                </button>
              </div>
            )}
          </div>

          {agentLogs.length > 0 && (
            <div className="p-4 border border-zinc-200 rounded-lg bg-white">
              <h2 className="text-sm font-semibold text-zinc-500 mb-3">Agent Logs</h2>
              <div className="space-y-3 max-h-96 overflow-y-auto">
                {agentLogs.map((log, i) => (
                  <div key={i} className="p-3 bg-zinc-50 rounded-lg text-sm">
                    <p className="text-xs text-zinc-400 mb-1">Step {log.step}</p>
                    <p className="font-mono text-xs whitespace-pre-wrap break-words">
                      <span className="text-zinc-500">Decision:</span> {log.decision}
                    </p>
                    {log.result && (
                      <p className="font-mono text-xs text-zinc-600 mt-1 whitespace-pre-wrap break-words">
                        <span className="text-zinc-500">Result:</span> {JSON.stringify(log.result)}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
