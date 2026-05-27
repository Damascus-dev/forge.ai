/**
 * Export utilities for React Flow visualization
 * Supports PNG screenshot and print-to-PDF
 */

/**
 * Capture a React Flow container as a PNG image
 * Uses the DOM element directly via canvas
 */
export function captureFlowAsPNG(elementId = "experiment-flow", filename = "experiment-flow.png") {
  const element = document.getElementById(elementId);
  if (!element) {
    console.warn(`Element #${elementId} not found`);
    return;
  }

  // Use the built-in React Flow export functionality via SVG
  const svgElement = element.querySelector(".react-flow__renderer svg");
  if (!svgElement) {
    console.warn("No React Flow SVG found");
    return;
  }

  const svgData = new XMLSerializer().serializeToString(svgElement);
  const canvas = document.createElement("canvas");
  const rect = svgElement.getBoundingClientRect();
  canvas.width = rect.width * 2;
  canvas.height = rect.height * 2;
  const ctx = canvas.getContext("2d");
  ctx.scale(2, 2);

  const img = new Image();
  const blob = new Blob([svgData], { type: "image/svg+xml;charset=utf-8" });
  const url = URL.createObjectURL(blob);

  img.onload = () => {
    ctx.fillStyle = "#ffffff";
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    ctx.drawImage(img, 0, 0, rect.width, rect.height);
    URL.revokeObjectURL(url);

    const link = document.createElement("a");
    link.download = filename;
    link.href = canvas.toDataURL("image/png");
    link.click();
  };

  img.src = url;
}

/**
 * Print the visualization (user can choose "Save as PDF" in print dialog)
 */
export function printFlow(elementId = "experiment-flow") {
  const element = document.getElementById(elementId);
  if (!element) return;

  const originalTitle = document.title;
  document.title = "Experiment Flow";

  const clone = element.cloneNode(true);
  const printWindow = window.open("", "_blank");
  if (!printWindow) {
    console.warn("Pop-up blocked; cannot print");
    return;
  }

  const styles = Array.from(document.styleSheets)
    .map((sheet) => {
      try {
        return Array.from(sheet.cssRules || [])
          .map((rule) => rule.cssText)
          .join("\n");
      } catch {
        return "";
      }
    })
    .join("\n");

  printWindow.document.write(`
    <!DOCTYPE html>
    <html>
    <head>
      <title>Experiment Flow</title>
      <style>
        ${styles}
        body { padding: 20px; margin: 0; }
        @media print {
          body { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
        }
      </style>
    </head>
    <body>
      <div id="print-root">${clone.outerHTML}</div>
      <script>
        window.onload = () => { window.print(); window.close(); };
      </script>
    </body>
    </html>
  `);
  printWindow.document.close();

  document.title = originalTitle;
}

/**
 * Export current experiment state as JSON (for sharing/reloading)
 */
export function exportExperimentState(nodes, edges, activeChaos, agentStates) {
  const state = {
    timestamp: new Date().toISOString(),
    version: "1.0",
    nodes,
    edges,
    activeChaos,
    agentStates,
  };

  const blob = new Blob([JSON.stringify(state, null, 2)], { type: "application/json" });
  const link = document.createElement("a");
  link.download = `experiment-state-${Date.now()}.json`;
  link.href = URL.createObjectURL(blob);
  link.click();
  URL.revokeObjectURL(link.href);
}

/**
 * Get a simple performance report for the flow system
 */
export function getFlowPerformanceReport() {
  if (typeof performance === "undefined" || !performance.memory) {
    return { supported: false, message: "Performance API not available" };
  }

  return {
    supported: true,
    memory: {
      usedJSHeapSize: `${(performance.memory.usedJSHeapSize / 1048576).toFixed(1)} MB`,
      totalJSHeapSize: `${(performance.memory.totalJSHeapSize / 1048576).toFixed(1)} MB`,
      jsHeapSizeLimit: `${(performance.memory.jsHeapSizeLimit / 1048576).toFixed(1)} MB`,
    },
    timestamp: new Date().toISOString(),
  };
}
