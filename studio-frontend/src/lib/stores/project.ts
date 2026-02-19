import { writable } from 'svelte/store';
import type { ProjectInfo } from '$lib/types/graph';

export const currentProject = writable<ProjectInfo | null>(null);
export const projects = writable<ProjectInfo[]>([]);
