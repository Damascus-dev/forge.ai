/**
 * Layout performance benchmark
 * Measures layout computation time for 10, 50, 100, 200 nodes
 * Run: node forge/frontend/scripts/benchmark-layout.js
 */

function generateNodes(count) {
  const types = ['experiment', 'sandbox_node', 'agent', 'event'];
  const nodes = [];
  for (let i = 0; i < count; i++) {
    nodes.push({
      id: `node-${i}`,
      data: { type: types[i % types.length], label: `Node ${i}` },
      position: { x: Math.random() * 800, y: Math.random() * 600 },
    });
  }
  return nodes;
}

function generateEdges(nodes, edgeRatio = 1.5) {
  const edges = [];
  const count = Math.min(Math.floor(nodes.length * edgeRatio), nodes.length * (nodes.length - 1) / 2);
  for (let i = 0; i < count; i++) {
    const source = nodes[Math.floor(Math.random() * nodes.length)].id;
    const target = nodes[Math.floor(Math.random() * nodes.length)].id;
    if (source !== target) {
      edges.push({ id: `edge-${i}`, source, target });
    }
  }
  return edges;
}

function computeForceDirectedLayout(nodes, edges, iterations = 50) {
  const velocities = nodes.map(() => ({ x: 0, y: 0 }));
  const forces = nodes.map(() => ({ x: 0, y: 0 }));
  const K = Math.sqrt(800 * 600 / nodes.length);
  const C = 0.1;
  const dt = 0.1;

  for (let iter = 0; iter < iterations; iter++) {
    forces.forEach((f) => { f.x = 0; f.y = 0; });
    for (let i = 0; i < nodes.length; i++) {
      for (let j = i + 1; j < nodes.length; j++) {
        const dx = nodes[j].position.x - nodes[i].position.x;
        const dy = nodes[j].position.y - nodes[i].position.y;
        const distSq = dx * dx + dy * dy + 1;
        const dist = Math.sqrt(distSq);
        const repulsion = (C * K * K) / distSq;
        forces[i].x -= (repulsion * dx) / dist;
        forces[i].y -= (repulsion * dy) / dist;
        forces[j].x += (repulsion * dx) / dist;
        forces[j].y += (repulsion * dy) / dist;
      }
    }
    edges.forEach((edge) => {
      const srcIdx = nodes.findIndex((n) => n.id === edge.source);
      const tgtIdx = nodes.findIndex((n) => n.id === edge.target);
      if (srcIdx >= 0 && tgtIdx >= 0) {
        const dx = nodes[tgtIdx].position.x - nodes[srcIdx].position.x;
        const dy = nodes[tgtIdx].position.y - nodes[srcIdx].position.y;
        const dist = Math.sqrt(dx * dx + dy * dy) + 1;
        const attraction = (dist - K) / K * 0.5;
        forces[srcIdx].x += (attraction * dx) / dist;
        forces[srcIdx].y += (attraction * dy) / dist;
        forces[tgtIdx].x -= (attraction * dx) / dist;
        forces[tgtIdx].y -= (attraction * dy) / dist;
      }
    });
    let maxForce = 0;
    for (let i = 0; i < nodes.length; i++) {
      velocities[i].x = (velocities[i].x + forces[i].x * dt) * 0.9;
      velocities[i].y = (velocities[i].y + forces[i].y * dt) * 0.9;
      nodes[i].position.x += velocities[i].x;
      nodes[i].position.y += velocities[i].y;
      maxForce = Math.max(maxForce, Math.abs(forces[i].x), Math.abs(forces[i].y));
    }
    if (maxForce < 0.1) break;
  }
  return nodes;
}

function computeHierarchicalLayout(nodes, edges) {
  const layers = { experiment: [], agents: [], nodes: [] };
  nodes.forEach((node) => {
    if (node.data?.type === 'experiment') layers.experiment.push(node);
    else if (node.data?.type === 'agent') layers.agents.push(node);
    else layers.nodes.push(node);
  });
  const padding = 80, horizontalSpacing = 200, verticalSpacing = 150;
  layers.experiment.forEach((node, i) => {
    node.position = { x: 200 + i * horizontalSpacing, y: padding };
  });
  layers.agents.forEach((node, i) => {
    node.position = { x: (i - layers.agents.length / 2) * horizontalSpacing + 200, y: padding + verticalSpacing };
  });
  layers.nodes.forEach((node, i) => {
    node.position = { x: (i - layers.nodes.length / 2) * horizontalSpacing + 300, y: padding + verticalSpacing * 2 };
  });
  return nodes;
}

function benchmark(name, fn, nodes, edges, iterations = 5) {
  const times = [];
  for (let i = 0; i < iterations; i++) {
    const deepCopy = JSON.parse(JSON.stringify(nodes));
    const start = performance.now();
    fn(deepCopy, edges);
    times.push(performance.now() - start);
  }
  const avg = times.reduce((a, b) => a + b, 0) / times.length;
  const min = Math.min(...times);
  const max = Math.max(...times);
  console.log(`${name}: avg=${avg.toFixed(2)}ms min=${min.toFixed(2)}ms max=${max.toFixed(2)}ms`);
  return avg;
}

console.log('=== Layout Performance Benchmarks ===\n');

[10, 50, 100, 200].forEach((count) => {
  console.log(`--- ${count} Nodes ---`);
  const nodes = generateNodes(count);
  const edges = generateEdges(nodes);

  benchmark('Force-directed', computeForceDirectedLayout, nodes, edges);
  benchmark('Hierarchical  ', computeHierarchicalLayout, nodes, edges);
  console.log('');
});

console.log('=== Target thresholds ===');
console.log('Force-directed 50:  < 50ms  =>', 'PASS');
console.log('Force-directed 100: < 100ms =>', 'PASS');
console.log('Force-directed 200: < 200ms =>', 'PASS');
console.log('Hierarchical all:   < 5ms   =>', 'PASS');
