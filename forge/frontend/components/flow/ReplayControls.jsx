"use client";

import { useState, useEffect } from "react";

/**
 * ReplayControls - playback controls (play, pause, speed, reset)
 */
export function ReplayControls({ isPlaying, onPlay, onPause, onStop, onSpeedChange, currentSpeed = 1 }) {
  const speeds = [0.25, 0.5, 1, 2, 4];

  return (
    <div className="flex items-center gap-4 p-4 bg-white border border-gray-200 rounded-lg">
      {/* Play/Pause buttons */}
      <div className="flex gap-2">
        <button
          onClick={isPlaying ? onPause : onPlay}
          className={`px-4 py-2 rounded font-medium text-sm transition-colors ${
            isPlaying
              ? "bg-orange-500 hover:bg-orange-600 text-white"
              : "bg-green-500 hover:bg-green-600 text-white"
          }`}
        >
          {isPlaying ? "⏸ Pause" : "▶ Play"}
        </button>
        <button
          onClick={onStop}
          className="px-4 py-2 bg-gray-200 hover:bg-gray-300 rounded font-medium text-sm transition-colors"
        >
          ⏹ Reset
        </button>
      </div>

      {/* Speed selector */}
      <div className="flex items-center gap-2">
        <span className="text-sm text-gray-600 font-medium">Speed:</span>
        <div className="flex gap-1">
          {speeds.map((speed) => (
            <button
              key={speed}
              onClick={() => onSpeedChange(speed)}
              className={`px-2 py-1 text-xs rounded transition-colors ${
                Math.abs(currentSpeed - speed) < 0.01
                  ? "bg-blue-500 text-white font-bold"
                  : "bg-gray-200 hover:bg-gray-300"
              }`}
            >
              {speed}x
            </button>
          ))}
        </div>
      </div>

      {/* Status indicator */}
      <div className="ml-auto">
        <div className="flex items-center gap-2 text-sm">
          <div className={`w-2 h-2 rounded-full ${isPlaying ? "bg-green-500 animate-pulse" : "bg-gray-400"}`} />
          <span className="text-gray-600">
            {isPlaying ? "Playing" : "Paused"}
          </span>
        </div>
      </div>
    </div>
  );
}
