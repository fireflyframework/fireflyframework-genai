import { writable, derived } from 'svelte/store';
import type { Node, Edge } from '@xyflow/svelte';

export const nodes = writable<Node[]>([]);
export const edges = writable<Edge[]>([]);
export const selectedNodeId = writable<string | null>(null);

export const selectedNode = derived(
	[nodes, selectedNodeId],
	([$nodes, $id]) => ($id ? $nodes.find((n) => n.id === $id) ?? null : null)
);

export function updateNodeData(nodeId: string, key: string, value: unknown) {
	nodes.update((ns) =>
		ns.map((n) => (n.id === nodeId ? { ...n, data: { ...n.data, [key]: value } } : n))
	);
}
