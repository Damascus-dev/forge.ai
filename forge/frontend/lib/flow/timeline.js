/**
 * Event timeline utilities for temporal visualization
 */

/**
 * Calculate time-based positions for events
 * Maps event timestamps to X positions on a timeline
 */
export function calculateEventPositions(events, containerWidth = 1000) {
  if (!events || events.length === 0) {
    return {};
  }

  const timestamps = events
    .map((e) => new Date(e.timestamp).getTime())
    .filter((t) => !isNaN(t));

  if (timestamps.length === 0) return {};

  const minTime = Math.min(...timestamps);
  const maxTime = Math.max(...timestamps);
  const timeRange = maxTime - minTime || 1;

  const padding = 50;
  const usableWidth = containerWidth - padding * 2;

  return events.reduce((acc, event) => {
    const eventTime = new Date(event.timestamp).getTime();
    if (!isNaN(eventTime)) {
      const normalizedPos = (eventTime - minTime) / timeRange;
      const xPos = padding + normalizedPos * usableWidth;
      acc[event.id || event.timestamp] = xPos;
    }
    return acc;
  }, {});
}

/**
 * Filter events by time range (for replay scrubbing)
 */
export function filterEventsByTime(events, startTime, endTime) {
  return events.filter((e) => {
    const eventTime = new Date(e.timestamp).getTime();
    return eventTime >= startTime && eventTime <= endTime;
  });
}

/**
 * Group events by node/agent for visualization
 */
export function groupEventsBySource(events) {
  return events.reduce((acc, event) => {
    const source = event.source || 'unknown';
    if (!acc[source]) {
      acc[source] = [];
    }
    acc[source].push(event);
    return acc;
  }, {});
}

/**
 * Get event at specific time (for replay playhead)
 */
export function getEventAtTime(events, targetTime) {
  return events.find((e) => {
    const eventTime = new Date(e.timestamp).getTime();
    return Math.abs(eventTime - targetTime) < 100; // 100ms tolerance
  });
}

/**
 * Calculate timeline bounds
 */
export function getTimelineBounds(events) {
  if (!events || events.length === 0) {
    return { startTime: 0, endTime: Date.now(), duration: 0 };
  }

  const timestamps = events
    .map((e) => new Date(e.timestamp).getTime())
    .filter((t) => !isNaN(t));

  if (timestamps.length === 0) {
    return { startTime: 0, endTime: Date.now(), duration: 0 };
  }

  const startTime = Math.min(...timestamps);
  const endTime = Math.max(...timestamps);
  const duration = endTime - startTime;

  return { startTime, endTime, duration };
}

/**
 * Format time for display
 */
export function formatEventTime(timestamp) {
  const date = new Date(timestamp);
  return date.toLocaleTimeString([], { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' });
}

/**
 * Calculate event density for a time bucket (for histogram)
 */
export function calculateEventDensity(events, bucketCount = 20) {
  const { startTime, endTime, duration } = getTimelineBounds(events);
  if (duration === 0) return [];

  const buckets = Array(bucketCount).fill(0);
  const bucketSize = duration / bucketCount;

  events.forEach((event) => {
    const eventTime = new Date(event.timestamp).getTime();
    if (!isNaN(eventTime)) {
      const bucketIndex = Math.floor((eventTime - startTime) / bucketSize);
      if (bucketIndex >= 0 && bucketIndex < bucketCount) {
        buckets[bucketIndex]++;
      }
    }
  });

  return buckets.map((count, i) => ({
    bucket: i,
    count,
    timestamp: startTime + i * bucketSize,
  }));
}
