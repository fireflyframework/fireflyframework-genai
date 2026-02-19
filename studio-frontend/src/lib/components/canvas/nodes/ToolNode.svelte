<script lang="ts">
	import { Handle, Position } from '@xyflow/svelte';
	import { Wrench } from 'lucide-svelte';

	let { data } = $props();
</script>

<div class="tool-node">
	<div class="node-header">
		<div class="icon-wrapper tool-icon">
			<Wrench size={12} />
		</div>
		<span class="node-label">{data.label || 'Tool'}</span>
	</div>
	{#if data.description}
		<div class="node-detail">{data.description}</div>
	{/if}
	<Handle type="target" position={Position.Left} />
	<Handle type="source" position={Position.Right} />
</div>

<style>
	.tool-node {
		background: #1a1a26;
		border: 1px solid rgba(139, 92, 246, 0.3);
		border-radius: 10px;
		padding: 8px 12px;
		min-width: 140px;
		box-shadow: 0 4px 12px rgba(139, 92, 246, 0.05);
	}
	.node-header {
		display: flex;
		align-items: center;
		gap: 6px;
		margin-bottom: 4px;
	}
	.icon-wrapper {
		width: 20px;
		height: 20px;
		border-radius: 5px;
		display: flex;
		align-items: center;
		justify-content: center;
	}
	.tool-icon {
		background: rgba(139, 92, 246, 0.2);
		color: #8b5cf6;
	}
	.node-label {
		font-size: 11px;
		font-weight: 600;
		color: #e8e8ed;
	}
	.node-detail {
		font-size: 9px;
		color: #8888a0;
		font-family: 'JetBrains Mono', monospace;
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}
</style>
