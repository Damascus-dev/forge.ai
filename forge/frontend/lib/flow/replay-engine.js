/**
 * Replay engine for event playback
 * Manages playback state, time position, and event filtering
 */
import { filterEventsByTime, getTimelineBounds } from './timeline';

export class ReplayEngine {
  constructor(events = []) {
    this.events = events;
    this.isPlaying = false;
    this.currentTime = null;
    this.speed = 1;
    this.animationFrameId = null;
    this.lastFrameTime = null;
    this.onTimeChange = null;
  }

  start() {
    this.isPlaying = true;
    const bounds = getTimelineBounds(this.events);
    if (this.currentTime === null) {
      this.currentTime = bounds.startTime;
    }
    this.lastFrameTime = Date.now();
    this.animate();
  }

  pause() {
    this.isPlaying = false;
    if (this.animationFrameId) {
      cancelAnimationFrame(this.animationFrameId);
      this.animationFrameId = null;
    }
  }

  stop() {
    this.pause();
    const bounds = getTimelineBounds(this.events);
    this.currentTime = bounds.startTime;
  }

  setTime(time) {
    this.currentTime = time;
    if (this.onTimeChange) {
      this.onTimeChange(time);
    }
  }

  setSpeed(speed) {
    this.speed = speed;
  }

  animate() {
    if (!this.isPlaying) return;

    const now = Date.now();
    const deltaMs = this.lastFrameTime ? now - this.lastFrameTime : 0;
    this.lastFrameTime = now;

    const bounds = getTimelineBounds(this.events);
    const timeStep = deltaMs * this.speed;
    const newTime = this.currentTime + timeStep;

    if (newTime > bounds.endTime) {
      // Reached end
      this.currentTime = bounds.endTime;
      this.pause();
    } else {
      this.currentTime = newTime;
    }

    if (this.onTimeChange) {
      this.onTimeChange(this.currentTime);
    }

    this.animationFrameId = requestAnimationFrame(() => this.animate());
  }

  /**
   * Get events up to current time
   */
  getVisibleEvents() {
    if (this.currentTime === null) {
      return [];
    }
    const bounds = getTimelineBounds(this.events);
    return filterEventsByTime(this.events, bounds.startTime, this.currentTime);
  }

  /**
   * Get next event from current time
   */
  getNextEvent() {
    if (this.currentTime === null) {
      return null;
    }
    return this.events.find(
      (e) => new Date(e.timestamp).getTime() > this.currentTime
    ) || null;
  }
}
