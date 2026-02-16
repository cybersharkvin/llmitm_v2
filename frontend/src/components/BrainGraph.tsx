import { useRef, useEffect, useCallback, useMemo } from "react";
import ForceGraph3D from "react-force-graph-3d";
import * as THREE from "three";
import { UnrealBloomPass } from "three/examples/jsm/postprocessing/UnrealBloomPass.js";
import type { GraphData, GraphNode, NodeStatus } from "../lib/schemas";

/** ForceGraph3D node: GraphNode fields + force-layout y-pin. */
interface FGNode extends GraphNode {
  fy: number;
}

const NODE_BASE_COLOR = 0xfff0e8;
const NODE_EMISSIVE = 0xff88aa;
const HOVER_HEIGHT = 4.0;
const HOVER_JITTER = 1.2;

const EMISSIVE_INTENSITY: Record<NodeStatus, number> = {
  idle: 1.0,
  active: 2.2,
  completed: 1.6,
  error: 2.0,
};

const SPIKE_COUNTS: Record<NodeStatus, number> = {
  idle: 6,
  active: 16,
  completed: 10,
  error: 12,
};

const SPIKE_PALETTE: number[] = [0xff69b4, 0x44ff88, 0x66ccff, 0xcc66ff, 0xffaa00, 0x00cccc];

const LINK_COLORS: Record<string, string> = {
  data_flow: "#00ccaa",
  feedback: "#ff4488",
};

// ── Seeded PRNG (Fix 2: No spike flicker) ──
function mulberry32(seed: number) {
  return function () {
    seed |= 0;
    seed = (seed + 0x6d2b79f5) | 0;
    let t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function hashString(str: string): number {
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    hash = ((hash << 5) - hash + str.charCodeAt(i)) | 0;
  }
  return Math.abs(hash);
}

interface Props {
  graphData: GraphData;
  selectedNode: string | null;
  onNodeClick: (nodeId: string) => void;
}

export function BrainGraph({ graphData, selectedNode, onNodeClick }: Props) {
  const fgRef = useRef<any>(null);
  const bloomAdded = useRef(false);
  const sceneSetup = useRef(false);

  // ── Fix 1: Build topology when COUNT changes (not every status update) ──
  const fgData = useMemo(() => {
    const nodes = graphData.nodes.map((n, i) => ({
      id: n.id,
      name: n.name,
      type: n.type,
      group: n.group,
      status: n.status,
      errorMsg: n.errorMsg,
      fy: HOVER_HEIGHT + Math.sin(i * 2.39) * HOVER_JITTER,
    }));
    return { nodes, links: [...graphData.links] };
  }, [graphData.nodes.length, graphData.links.length]);

  // ── Fix 1: Update appearance in-place ──
  useEffect(() => {
    if (!fgRef.current) return;

    fgData.nodes.forEach((fgNode) => {
      const latest = graphData.nodes.find((n) => n.id === fgNode.id);
      if (latest) {
        fgNode.status = latest.status;
        fgNode.errorMsg = latest.errorMsg;
      }
    });

    fgRef.current.refresh();
  }, [graphData, fgData]);

  // Scene setup: grid, axes, bloom, camera, forces
  useEffect(() => {
    const trySetup = () => {
      const fg = fgRef.current;
      if (!fg) {
        setTimeout(trySetup, 200);
        return;
      }
      const scene = fg.scene?.();
      const camera = fg.camera?.();
      const renderer = fg.renderer?.();
      if (!scene || !camera || !renderer) {
        setTimeout(trySetup, 200);
        return;
      }

      fg.d3Force("charge")?.strength(-200);
      fg.d3Force("link")?.distance(15);

      if (!sceneSetup.current) {
        sceneSetup.current = true;

        const grid = new THREE.GridHelper(150, 50, 0x151525, 0x0e0e1e);
        grid.material.opacity = 0.25;
        grid.material.transparent = true;
        scene.add(grid);

        const axisMat = new THREE.LineBasicMaterial({ color: 0xff00ff, opacity: 0.3, transparent: true });
        for (const [a, b] of [
          [[-60, 0, 0], [60, 0, 0]],
          [[0, -2, 0], [0, 30, 0]],
          [[0, 0, -60], [0, 0, 60]],
        ] as [number[], number[]][]) {
          const geo = new THREE.BufferGeometry().setFromPoints([
            new THREE.Vector3(...a),
            new THREE.Vector3(...b),
          ]);
          scene.add(new THREE.Line(geo, axisMat));
        }

        camera.position.set(70, 55, 80);
        camera.lookAt(0, HOVER_HEIGHT, 0);
        const controls = fg.controls?.();
        if (controls) controls.target.set(0, HOVER_HEIGHT, 0);
      }

      if (!bloomAdded.current) {
        bloomAdded.current = true;
        const composer = fg.postProcessingComposer?.();
        if (composer) {
          const bloom = new UnrealBloomPass(
            new THREE.Vector2(window.innerWidth, window.innerHeight),
            1.8,
            0.4,
            0.15,
          );
          composer.addPass(bloom);
        }
      }
    };
    setTimeout(trySetup, 600);
  }, []);

  // ── Fix 2: Seeded spike rendering ──
  const nodeThreeObject = useCallback(
    (node: FGNode) => {
      const rng = mulberry32(hashString(node.id));
      const status: NodeStatus = node.status || "idle";
      const isSelected = node.id === selectedNode;
      const group = new THREE.Group();

      // Sphere core
      const radius = isSelected ? 1.5 : 0.95;
      const sphereGeo = new THREE.SphereGeometry(radius, 16, 16);
      const sphereMat = new THREE.MeshStandardMaterial({
        color: NODE_BASE_COLOR,
        emissive: NODE_EMISSIVE,
        emissiveIntensity: EMISSIVE_INTENSITY[status],
        roughness: 0.3,
        metalness: 0.1,
      });
      group.add(new THREE.Mesh(sphereGeo, sphereMat));

      // Spike lines with SEEDED randomness
      const spikeCount = SPIKE_COUNTS[status];
      const baseLength = status === "active" ? 3.2 : 2.2;
      const spikeOpacity = status === "active" ? 0.75 : 0.35;

      for (let s = 0; s < spikeCount; s++) {
        const theta = rng() * Math.PI * 2;
        const phi = Math.acos(2 * rng() - 1);
        const len = baseLength * (0.25 + rng() * 0.75);
        const dx = Math.sin(phi) * Math.cos(theta) * len;
        const dy = Math.sin(phi) * Math.sin(theta) * len;
        const dz = Math.cos(phi) * len;
        const sGeo = new THREE.BufferGeometry().setFromPoints([
          new THREE.Vector3(0, 0, 0),
          new THREE.Vector3(dx, dy, dz),
        ]);
        const color = SPIKE_PALETTE[Math.floor(rng() * SPIKE_PALETTE.length)];
        const sMat = new THREE.LineBasicMaterial({
          color,
          transparent: true,
          opacity: spikeOpacity,
        });
        group.add(new THREE.LineSegments(sGeo, sMat));
      }

      // Drop line
      const nodeY = node.fy ?? HOVER_HEIGHT;
      if (nodeY > 0.1) {
        const dGeo = new THREE.BufferGeometry().setFromPoints([
          new THREE.Vector3(0, 0, 0),
          new THREE.Vector3(0, -nodeY, 0),
        ]);
        const dMat = new THREE.LineBasicMaterial({ color: 0x44ff88, transparent: true, opacity: 0.2 });
        group.add(new THREE.Line(dGeo, dMat));
      }

      return group;
    },
    [selectedNode, graphData],
  );

  const handleClick = useCallback(
    (node: FGNode) => {
      if (node?.id) onNodeClick(node.id);
    },
    [onNodeClick],
  );

  return (
    <ForceGraph3D
      ref={fgRef}
      graphData={fgData}
      backgroundColor="#08081a"
      nodeThreeObject={nodeThreeObject}
      nodeThreeObjectExtend={false}
      linkColor={(link: any) => LINK_COLORS[link.type] || "#1a3a4a"}
      linkWidth={0.4}
      linkOpacity={0.5}
      linkDirectionalParticles={2}
      linkDirectionalParticleWidth={0.8}
      linkDirectionalParticleSpeed={0.005}
      linkDirectionalParticleColor={(link: any) => LINK_COLORS[link.type] || "#00ccaa"}
      onNodeClick={handleClick}
      showNavInfo={false}
      enableNodeDrag={false}
      cooldownTicks={300}
      d3AlphaDecay={0.02}
      d3VelocityDecay={0.3}
      width={window.innerWidth * 0.72 || 900}
      height={window.innerHeight - 90 || 700}
    />
  );
}
