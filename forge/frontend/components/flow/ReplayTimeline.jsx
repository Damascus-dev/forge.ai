"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import {
  getTimelineBounds,
  formatEventTime,
  calculateEventDensity,
  filterEventsByTime,
  getEventAtTime,
} from "@/lib/flow/timeline";

/**
 * ReplayTimeline - interactive timeline scrubber for event replay
 * Shows event density, current position, and allows time navigation
 */
export function ReplayTimeline({ events = [], currentTime = null, onTimeChange = () => {}, isPlaying = false }) {
  const [localTime, setLocalTime] = useState(currentTime || null);
  const [dragActive, setDragActive] = useState(false);
  const bounds = getTimelineBounds(events);
  const density = calculateEventDensity(events, 40);

  // Update local time when currentTime prop changes
  useEffect(() => {
    if (currentTime !== null) {
      setLocalTime(currentTime);
    }
  }, [currentTime]);

  if (bounds.duration === 0) {
    return (
      <div className="p-4 bg-gray-50 rounded-lg border border-gray-200 text-center text-sm text-gray-500">
        No events to replay
      </div>
    );
  }

  const timelineWidth = 100; // percentage
  const currentPosition =
    localTime !== null
      ? ((localTime - bounds.startTime) / bounds.duration) * 100
      : 0;

  const maxDensity = Math.max(...density.map((d) => d.count), 1);

  function handleTimelineClick(e) {
    const rect = e.currentTarget.getBoundingClientRect();
    const clickPos = (e.clientX - rect.left) / rect.width;
    const newTime = bounds.startTime + clickPos * bounds.duration;
    setLocalTime(newTime);
    onTimeChange(newTime);
  }

  function handleDrag(e) {
    if (!dragActive) return;
    const rect = e.currentTarget.getBoundingClientRect();
    const dragPos = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width));
    const newTime = bounds.startTime + dragPos * bounds.duration;
    setLocalTime(newTime);
    onTimeChange(newTime);
  }

  return (
    <div className="space-y-3 p-4 bg-white border border-gray-200 rounded-lg">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-gray-900">📊 Event Timeline</h3>
        <div className="text-xs text-gray-500 space-x-2">
          {bounds.startTime && (
            <>
              <span>{formatEventTime(bounds.startTime)}</span>
              <span>→</span>
              <span>{formatEventTime(bounds.endTime)}</span>
            </>
          )}
        </div>
      </div>

      {/* Event density histogram */}
      <div
        className="relative h-12 bg-gray-50 rounded border border-gray-200 cursor-pointer group overflow-hidden"
        onClick={handleTimelineClick}
        onMouseMove={handleDrag}
        onMouseDown={() => setDragActive(true)}
        onMouseUp={() => setDragActive(false)}
        onMouseLeave={() => setDragActive(false)}
      >
        {/* Density bars */}
        <div className="absolute inset-0 flex items-end justify-between px-1 gap-0.5">
          {density.map((bucket, i) => (
            <div
              key={i}
              className="flex-1 bg-blue-200 group-hover:bg-blue-300 transition-colors"
              style={{
                height: `${(bucket.count / maxDensity) * 100}%`,
              }}
              title={`${bucket.count} events at ${formatEventTime(bucket.timestamp)}`}
            />
          ))}
        </div>

        {/* Current time indicator (playhead) */}
        {localTime !== null && (
          <motion.div
            className="absolute top-0 bottom-0 w-1 bg-red-500 cursor-grab active:cursor-grabbing shadow-lg"
            style={{
              left: `${currentPosition}%`,
            }}
            whileHover={{ scaleX: 1.5 }}
          />
        )}
      </div>

      {/* Time display and controls */}
      <div className="flex items-center justify-between">
        <div className="text-xs text-gray-600 font-mono">
          {localTime !== null ? (
            <>
              <span>{formatEventTime(localTime)}</span>
              <span className="text-gray-400 mx-1">/</span>
              <span className="text-gray-400">{formatEventTime(bounds.endTime)}</span>
            </>
          ) : (
            <span className="text-gray-400">—</span>
          )}
        </div>

        {/* Quick actions */}
        <div className="flex gap-2">
          <button
            onClick={() => {
              setLocalTime(bounds.startTime);
              onTimeChange(bounds.startTime);
            }}
            className="px-2 py-1 text-xs bg-gray-100 hover:bg-gray-200 rounded transition-colors"
            title="Go to start"
          >
            ⏮
          </button>
          <button
            onClick={() => {
              const event = getEventAtTime(events, localTime);
              if (event) {
                const nextEvent = events.find(
                  (e) => new Date(e.timestamp).getTime() > new Date(event.timestamp).getTime()
                );
                if (nextEvent) {
                  const nextTime = new Date(nextEvent.timestamp).getTime();
                  setLocalTime(nextTime);
                  onTimeChange(nextTime);
                }
              }
            }}
            className="px-2 py-1 text-xs bg-gray-100 hover:bg-gray-200 rounded transition-colors"
            title="Next event"
          >
            ⏭
          </button>
          <button
            onClick={() => {
              setLocalTime(bounds.endTime);
              onTimeChange(bounds.endTime);
            }}
            className="px-2 py-1 text-xs bg-gray-100 hover:bg-gray-200 rounded transition-colors"
            title="Go to end"
          >
            ⏭️
          </button>
        </div>
      </div>

      {/* Current event info */}
      {localTime !== null && (
        <div className="p-2 bg-blue-50 rounded text-xs">
          {(() => {
            const event = getEventAtTime(events, localTime);
            if (event) {
              return (
                <p>
                  <span className="font-semibold">{event.event_type}</span>
                  {event.source && <span className="text-gray-600 mx-1">from {event.source}</span>}
                  {event.data && (
                    <span className="text-gray-500 font-mono">
                      {JSON.stringify(event.data).slice(0, 50)}
                    </span>
                  )}
                </p>
              );
            }
            return <p className="text-gray-500">No event at this time</p>;
          })()}
        </div>
      )}
    </div>
  );
}

/**
 * EventTimeline - vertical timeline display of all events
 * Useful for reviewing event sequence
 */
export function EventTimeline({ events = [], selectedTime = null, onEventSelect = () => {} }) {
  if (!events || events.length === 0) {
    return (
      <div className="text-sm text-gray-500 text-center p-4">
        No events recorded
      </div>
    );
  }

  // Sort events by time
  const sortedEvents = [...events].sort(
    (a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
  );

  const eventTypeColors = {
    node_start: "bg-green-100 text-green-800",
    node_stop: "bg-gray-100 text-gray-800",
    latency: "bg-orange-100 text-orange-800",
    packet_loss: "bg-red-100 text-red-800",
    crash: "bg-red-200 text-red-900",
    disconnect: "bg-pink-100 text-pink-800",
    agent_observe: "bg-blue-100 text-blue-800",
    agent_reason: "bg-amber-100 text-amber-800",
    agent_act: "bg-purple-100 text-purple-800",
  };

  return (
    <div className="space-y-2">
      {sortedEvents.map((event, i) => (
        <motion.div
          key={event.id || i}
          className={`p-3 border rounded-lg cursor-pointer transition-all ${
            selectedTime &&
            Math.abs(
              new Date(event.timestamp).getTime() - selectedTime
            ) < 100
              ? "border-blue-500 bg-blue-50 shadow-md"
              : "border-gray-200 hover:border-gray-300"
          }`}
          onClick={() => onEventSelect(new Date(event.timestamp).getTime())}
          initial={{ opacity: 0, x: -10 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: i * 0.02 }}
        >
          <div className="flex items-start justify-between gap-2">
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2">
                <span className={`text-xs font-bold px-2 py-1 rounded ${eventTypeColors[event.event_type] || 'bg-gray-100 text-gray-800'}`}>
                  {event.event_type}
                </span>
                <span className="text-xs font-mono text-gray-500">
                  {formatEventTime(event.timestamp)}
                </span>
              </div>
              {event.source && (
                <p className="text-xs text-gray-600 mt-1">Source: {event.source}</p>
              )}
              {event.data && Object.keys(event.data).length > 0 && (
                <p className="text-xs text-gray-500 font-mono mt-1 truncate">
                  {JSON.stringify(event.data)}
                </p>
              )}
            </div>
          </div>
        </motion.div>
      ))}
    </div>
  );
}
