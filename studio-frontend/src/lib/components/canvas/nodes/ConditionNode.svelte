<script lang="ts">
	import { Handle, Position } from '@xyflow/svelte';
	import { CircleDot } from 'lucide-svelte';

	let { data } = $props();
</script>

<div class="condition-node">
	<div class="diamond">
		<div class="diamond-content">
			<div class="icon-wrapper condition-icon">
				<CircleDot size={12} />
			</div>
			<span class="node-label">{data.label || 'Condition'}</span>
		</div>
	</div>
	<Handle type="target" position={Position.Left} class="handle-left" />
	<Handle type="source" position={Position.Right} id="true" class="handle-true" style="top: 35%;" />
	<Handle type="source" position={Position.Right} id="false" class="handle-false" style="top: 65%;" />
	<span class="handle-label true-label">T</span>
	<span class="handle-label false-label">F</span>
</div>

<style>
	.condition-node {
		position: relative;
		min-width: 120px;
		min-height: 80px;
		display: flex;
		align-items: center;
		justify-content: center;
	}
	.diamond {
		background: #1a1a26;
		border: 1px solid rgba(136, 136, 160, 0.3);
		width: 100px;
		height: 100px;
		transform: rotate(45deg);
		display: flex;
		align-items: center;
		justify-content: center;
		box-shadow: 0 4px 12px rgba(136, 136, 160, 0.05);
	}
	.diamond-content {
		transform: rotate(-45deg);
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 4px;
		white-space: nowrap;
	}
	.icon-wrapper {
		width: 20px;
		height: 20px;
		border-radius: 5px;
		display: flex;
		align-items: center;
		justify-content: center;
	}
	.condition-icon {
		background: rgba(136, 136, 160, 0.2);
		color: #8888a0;
	}
	.node-label {
		font-size: 10px;
		font-weight: 600;
		color: #e8e8ed;
	}
	.handle-label {
		position: absolute;
		font-size: 8px;
		font-weight: 700;
		font-family: 'JetBrains Mono', monospace;
		right: -4px;
	}
	.true-label {
		top: 25%;
		color: #22c55e;
	}
	.false-label {
		top: 58%;
		color: #ef4444;
	}
</style>
