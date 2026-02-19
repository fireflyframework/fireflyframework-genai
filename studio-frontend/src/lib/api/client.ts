import type {
	AgentInfo,
	ToolInfo,
	PatternInfo,
	ProjectInfo,
	UsageSummary,
	Checkpoint
} from '$lib/types/graph';

const BASE_URL = '/api';

async function request<T>(path: string, options?: RequestInit): Promise<T> {
	const resp = await fetch(`${BASE_URL}${path}`, {
		headers: { 'Content-Type': 'application/json' },
		...options
	});
	if (!resp.ok) {
		const error = await resp.json().catch(() => ({ detail: resp.statusText }));
		throw new Error(error.detail || resp.statusText);
	}
	return resp.json();
}

export const api = {
	health: () => request<{ status: string; version: string }>('/health'),

	registry: {
		agents: () => request<AgentInfo[]>('/registry/agents'),
		tools: () => request<ToolInfo[]>('/registry/tools'),
		patterns: () => request<PatternInfo[]>('/registry/patterns')
	},

	projects: {
		list: () => request<ProjectInfo[]>('/projects'),
		create: (name: string, description?: string) =>
			request<ProjectInfo>('/projects', {
				method: 'POST',
				body: JSON.stringify({ name, description })
			}),
		delete: (name: string) =>
			request<{ status: string }>(`/projects/${name}`, { method: 'DELETE' }),
		savePipeline: (project: string, pipeline: string, graph: object) =>
			request<{ status: string }>(`/projects/${project}/pipelines/${pipeline}`, {
				method: 'POST',
				body: JSON.stringify({ graph })
			}),
		loadPipeline: (project: string, pipeline: string) =>
			request<object>(`/projects/${project}/pipelines/${pipeline}`)
	},

	codegen: {
		toCode: (graph: object) =>
			request<{ code: string }>('/codegen/to-code', {
				method: 'POST',
				body: JSON.stringify({ graph })
			})
	},

	monitoring: {
		usage: () => request<UsageSummary>('/monitoring/usage')
	},

	checkpoints: {
		list: () => request<Checkpoint[]>('/checkpoints'),
		get: (index: number) => request<Checkpoint>(`/checkpoints/${index}`),
		fork: (fromIndex: number, modifiedState: Record<string, unknown>) =>
			request<Checkpoint>('/checkpoints/fork', {
				method: 'POST',
				body: JSON.stringify({ from_index: fromIndex, modified_state: modifiedState })
			}),
		diff: (indexA: number, indexB: number) =>
			request<{ added: string[]; removed: string[]; changed: string[] }>('/checkpoints/diff', {
				method: 'POST',
				body: JSON.stringify({ index_a: indexA, index_b: indexB })
			}),
		clear: () =>
			request<{ status: string }>('/checkpoints', { method: 'DELETE' })
	}
};
