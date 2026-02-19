import { writable } from 'svelte/store';
import type { ExecutionEvent, Checkpoint } from '$lib/types/graph';

export const isRunning = writable(false);
export const isDebugging = writable(false);
export const executionEvents = writable<ExecutionEvent[]>([]);
export const activeNodes = writable<Set<string>>(new Set());
export const checkpoints = writable<Checkpoint[]>([]);
