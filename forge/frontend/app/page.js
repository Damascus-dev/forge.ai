"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { listExperiments, createExperiment } from "@/lib/api";

export default function Home() {
  const router = useRouter();
  const [experiments, setExperiments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [name, setName] = useState("");
  const [nodeCount, setNodeCount] = useState(2);

  async function load() {
    try {
      const data = await listExperiments();
      setExperiments(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); }, []);

  async function handleCreate(e) {
    e.preventDefault();
    try {
      const exp = await createExperiment(name, nodeCount);
      setShowCreate(false);
      setName("");
      router.push(`/experiments/${exp.id}`);
    } catch (e) {
      alert(e.message);
    }
  }

  const statusColor = {
    running: "text-green-600 bg-green-50 border-green-200",
    pending: "text-yellow-600 bg-yellow-50 border-yellow-200",
    completed: "text-zinc-500 bg-zinc-50 border-zinc-200",
    failed: "text-red-600 bg-red-50 border-red-200",
  };

  return (
    <div className="max-w-3xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">Experiments</h1>
        <button
          onClick={() => setShowCreate(!showCreate)}
          className="px-4 py-2 bg-zinc-900 text-white rounded-lg text-sm font-medium hover:bg-zinc-800 transition-colors"
        >
          + New Experiment
        </button>
      </div>

      {showCreate && (
        <form onSubmit={handleCreate} className="mb-6 p-4 border border-zinc-200 rounded-lg bg-white">
          <div className="flex gap-3 items-end">
            <div className="flex-1">
              <label className="block text-xs font-medium text-zinc-500 mb-1">Name</label>
              <input
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="w-full px-3 py-2 border border-zinc-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-zinc-400"
                placeholder="my-experiment"
                required
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-zinc-500 mb-1">Nodes</label>
              <input
                type="number"
                min={1}
                max={10}
                value={nodeCount}
                onChange={(e) => setNodeCount(Number(e.target.value))}
                className="w-20 px-3 py-2 border border-zinc-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-zinc-400"
              />
            </div>
            <button
              type="submit"
              className="px-4 py-2 bg-zinc-900 text-white rounded-lg text-sm font-medium hover:bg-zinc-800 transition-colors"
            >
              Create
            </button>
          </div>
        </form>
      )}

      {loading ? (
        <p className="text-zinc-400 text-sm">Loading...</p>
      ) : experiments.length === 0 ? (
        <div className="text-center py-16 text-zinc-400">
          <p className="text-lg mb-1">No experiments yet</p>
          <p className="text-sm">Create one to get started</p>
        </div>
      ) : (
        <div className="space-y-2">
          {experiments.map((exp) => (
            <div
              key={exp.id}
              onClick={() => router.push(`/experiments/${exp.id}`)}
              className="p-4 border border-zinc-200 rounded-lg bg-white hover:border-zinc-400 cursor-pointer transition-colors flex items-center justify-between"
            >
              <div>
                <p className="font-medium">{exp.name}</p>
                <p className="text-xs text-zinc-400 mt-0.5">{exp.id} &middot; {exp.node_count} nodes</p>
              </div>
              <span className={`text-xs px-2 py-1 rounded border font-medium ${statusColor[exp.status] || "text-zinc-500"}`}>
                {exp.status}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
