<script lang="ts">
	import { Handle, Position } from '@xyflow/svelte';
	import { Brain } from 'lucide-svelte';

	let { data } = $props();
</script>

<div class="reasoning-node">
	<div class="node-inner">
		<div class="node-header">
			<div class="icon-wrapper reasoning-icon">
				<Brain size={14} />
			</div>
			<span class="node-label">{data.label || 'Reasoning'}</span>
		</div>
		{#if data.pattern}
			<div class="node-detail">{data.pattern}</div>
		{/if}
	</div>
	<Handle type="target" position={Position.Left} />
	<Handle type="source" position={Position.Right} />
</div>

<style>
	.reasoning-node {
		background: #1a1a26;
		border: 1px solid rgba(236, 72, 153, 0.3);
		border-radius: 4px 16px 4px 16px;
		padding: 12px 16px;
		min-width: 160px;
		box-shadow: 0 4px 12px rgba(236, 72, 153, 0.05);
	}
	.node-inner {
		display: flex;
		flex-direction: column;
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
	.reasoning-icon {
		background: rgba(236, 72, 153, 0.2);
		color: #ec4899;
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
