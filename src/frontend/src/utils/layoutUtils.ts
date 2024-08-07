import { NODE_HEIGHT, NODE_WIDTH } from "@/constants/constants";
import { NodeType } from "@/types/flow";
import ELK, { ElkNode } from "elkjs/lib/elk.bundled.js";
import { cloneDeep } from "lodash";
import { Edge } from "reactflow";

const layoutOptions = {
  "elk.algorithm": "layered",
  "elk.direction": "RIGHT",
  "elk.layered.spacing.edgeNodeBetweenLayers": "40",
  "elk.spacing.nodeNode": "40",
  "elk.layered.nodePlacement.strategy": "SIMPLE",
};
const elk = new ELK();

// uses elkjs to give each node a layouted position
export const getLayoutedNodes = async (nodes: NodeType[], edges: Edge[]) => {
  const graph = {
    id: "root",
    layoutOptions,
    children: cloneDeep(nodes).map((n) => {
      const targetPorts = edges
        .filter((e) => e.source === n.id)
        .map((e) => ({
          id: e.sourceHandle,
          properties: {
            side: "EAST",
          },
        }));

      const sourcePorts = edges
        .filter((e) => e.target === n.id)
        .map((e) => ({
          id: e.targetHandle,
          properties: {
            side: "WEST",
          },
        }));
      return {
        id: n.id,
        width: NODE_WIDTH,
        height: NODE_HEIGHT,
        // ⚠️ we need to tell elk that the ports are fixed, in order to reduce edge crossings
        properties: {
          "org.eclipse.elk.portConstraints": "FIXED_ORDER",
        },
        // we are also passing the id, so we can also handle edges without a sourceHandle or targetHandle option
        ports: [{ id: n.id }, ...targetPorts, ...sourcePorts],
      };
    }) as ElkNode[],
    edges: edges.map((e) => ({
      id: e.id,
      sources: [e.sourceHandle || e.source],
      targets: [e.targetHandle || e.target],
    })),
  };

  const layoutedGraph = await elk.layout(graph);

  const layoutedNodes = nodes.map((node) => {
    const layoutedNode = layoutedGraph.children?.find(
      (lgNode) => lgNode.id === node.id,
    );

    return {
      ...node,
      position: {
        x: layoutedNode?.x ?? 0,
        y: layoutedNode?.y ?? 0,
      },
      type: "genericNode",
    };
  });

  return layoutedNodes;
};
