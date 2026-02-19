export type NodeType =
	| 'agent'
	| 'tool'
	| 'reasoning'
	| 'pipeline_step'
	| 'fan_out'
	| 'fan_in'
	| 'condition'
	| 'memory'
	| 'validator'
	| 'custom_code';

export interface GraphNodeData {
	model?: string;
	instructions?: string;
	description?: string;
	label?: string;
	[key: string]: unknown;
}

export interface AgentInfo {
	name: string;
	version: string;
	description: string;
	tags: string[];
}

export interface ToolInfo {
	name: string;
	description: string;
	tags: string[];
	parameter_count: number;
}

export interface PatternInfo {
	name: string;
}

export interface ProjectInfo {
	name: string;
	description: string;
	created_at: string;
}

export interface ExecutionEvent {
	type: 'node_start' | 'node_complete' | 'node_error' | 'node_skip' | 'pipeline_complete';
	node_id?: string;
	pipeline_name?: string;
	latency_ms?: number;
	error?: string;
	success?: boolean;
	duration_ms?: number;
}

export interface Checkpoint {
	index: number;
	node_id: string;
	state: Record<string, unknown>;
	inputs: Record<string, unknown>;
	timestamp: string;
	branch_id?: string;
	parent_index?: number;
}
