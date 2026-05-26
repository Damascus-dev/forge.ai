/**
 * Force-directed layout algorithm for React Flow
 * Positions nodes to minimize overlaps and improve readability
 */

/**
 * Simple force-directed layout using spring physics
 * Nodes repel each other, edges attract connected nodes
 */
export function computeForceDirectedLayout(nodes, edges, iterations = 50) {
  if (nodes.length === 0) return [];

  // Initialize velocities
  const velocities = nodes.map(() => ({ x: 0, y: 0 }));
  const forces = nodes.map(() => ({ x: 0, y: 0 }));

  const K = Math.sqrt(800 * 600 / nodes.length); // Optimal distance
  const C = 0.1; // Coulomb constant (repulsion)
  const dt = 0.1; // Time step

  // Run iterations
  for (let iter = 0; iter < iterations; iter++) {
    // Reset forces
    forces.forEach((f) => {
      f.x = 0;
      f.y = 0;
    });

    // Repulsive forces (Coulomb)
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

    // Attractive forces (Hooke's law) for edges
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

    // Update positions
    let maxForce = 0;
    for (let i = 0; i < nodes.length; i++) {
      velocities[i].x = (velocities[i].x + forces[i].x * dt) * 0.9;
      velocities[i].y = (velocities[i].y + forces[i].y * dt) * 0.9;

      nodes[i].position.x += velocities[i].x;
      nodes[i].position.y += velocities[i].y;

      maxForce = Math.max(maxForce, Math.abs(forces[i].x), Math.abs(forces[i].y));
    }

    // Early exit if converged
    if (maxForce < 0.1) break;
  }

  return nodes;
}

/**
 * Hierarchical layout (for agent → nodes relationships)
 * Places experiment at top, agents below, nodes at bottom
 */
export function computeHierarchicalLayout(nodes, edges) {
  const layers = {
    experiment: [],
    agents: [],
    nodes: [],
  };

  // Classify nodes
  nodes.forEach((node) => {
    if (node.data?.type === 'experiment') {
      layers.experiment.push(node);
    } else if (node.data?.type === 'agent') {
      layers.agents.push(node);
    } else {
      layers.nodes.push(node);
    }
  });

  const padding = 80;
  const horizontalSpacing = 200;
  const verticalSpacing = 150;

  // Position experiment at top center
  layers.experiment.forEach((node, i) => {
    node.position = {
      x: 200 + i * horizontalSpacing,
      y: padding,
    };
  });

  // Position agents in middle
  layers.agents.forEach((node, i) => {
    const width = Math.max(layers.agents.length * horizontalSpacing, 400);
    node.position = {
      x: (i - layers.agents.length / 2) * horizontalSpacing + 200,
      y: padding + verticalSpacing,
    };
  });

  // Position nodes at bottom
  const nodeWidth = Math.max(layers.nodes.length * horizontalSpacing, 600);
  layers.nodes.forEach((node, i) => {
    node.position = {
      x: (i - layers.nodes.length / 2) * horizontalSpacing + 300,
      y: padding + verticalSpacing * 2,
    };
  });

  return nodes;
}

/**
 * Circular layout - arrange nodes in a circle
 * Good for small networks
 */
export function computeCircularLayout(nodes) {
  const center = { x: 300, y: 300 };
  const radius = 200;

  nodes.forEach((node, i) => {
    const angle = (i / nodes.length) * 2 * Math.PI;
    node.position = {
      x: center.x + radius * Math.cos(angle),
      y: center.y + radius * Math.sin(angle),
    };
  });

  return nodes;
}
