<script lang="ts">
	import { Handle, Position } from '@xyflow/svelte';
	import { Bot } from 'lucide-svelte';

	let { data } = $props();
</script>

<div class="agent-node">
	<div class="node-header">
		<div class="icon-wrapper agent-icon">
			<Bot size={14} />
		</div>
		<span class="node-label">{data.label || 'Agent'}</span>
	</div>
	{#if data.model}
		<div class="node-detail">{data.model}</div>
	{/if}
	<Handle type="target" position={Position.Left} />
	<Handle type="source" position={Position.Right} />
</div>

<style>
	.agent-node {
		background: #1a1a26;
		border: 1px solid rgba(99, 102, 241, 0.3);
		border-radius: 12px;
		padding: 12px 16px;
		min-width: 180px;
		box-shadow: 0 4px 12px rgba(99, 102, 241, 0.05);
	}
	.node-header {
		display: flex;
		align-items: center;
		gap: 8px;
		margin-bottom: 6px;
	}
	.icon-wrapper {
		width: 24px;
		height: 24px;
		border-radius: 6px;
		display: flex;
		align-items: center;
		justify-content: center;
	}
	.agent-icon {
		background: rgba(99, 102, 241, 0.2);
		color: #6366f1;
	}
	.node-label {
		font-size: 12px;
		font-weight: 600;
		color: #e8e8ed;
	}
	.node-detail {
		font-size: 10px;
		color: #8888a0;
		font-family: 'JetBrains Mono', monospace;
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}
</style>
