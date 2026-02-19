import { writable } from 'svelte/store';
import type { Node, Edge } from '@xyflow/svelte';

export const nodes = writable<Node[]>([]);
export const edges = writable<Edge[]>([]);
export const selectedNodeId = writable<string | null>(null);
