<script lang="ts">
	import { Handle, Position } from '@xyflow/svelte';
	import { Brain, CheckCircle2, AlertCircle } from 'lucide-svelte';

	let { data } = $props();

	let execState = $derived((data._executionState as string) ?? 'idle');
	let showComplete = $state(false);
	let completeTimer: ReturnType<typeof setTimeout> | undefined;

	$effect(() => {
		if (execState === 'complete') {
			showComplete = true;
			clearTimeout(completeTimer);
			completeTimer = setTimeout(() => {
				showComplete = false;
			}, 3000);
		} else {
			showComplete = false;
			clearTimeout(completeTimer);
		}
	});
</script>

<div
	class="reasoning-node"
	class:exec-running={execState === 'running'}
	class:exec-complete={execState === 'complete'}
	class:exec-error={execState === 'error'}
>
	<div class="node-inner">
		<div class="node-header">
			<div class="icon-wrapper reasoning-icon">
				<Brain size={14} />
			</div>
			<span class="node-label">{data.label || 'Reasoning'}</span>
			{#if showComplete}
				<span class="state-icon state-complete">
					<CheckCircle2 size={14} />
				</span>
			{/if}
			{#if execState === 'error'}
				<span class="state-icon state-error">
					<AlertCircle size={14} />
				</span>
			{/if}
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
		transition: border-color 0.3s ease, box-shadow 0.3s ease;
	}
	.reasoning-node.exec-running {
		animation: pulse-reasoning 1.5s ease-in-out infinite;
	}
	.reasoning-node.exec-complete {
		border-color: var(--color-success);
		box-shadow: 0 0 12px rgba(34, 197, 94, 0.3);
	}
	.reasoning-node.exec-error {
		border-color: var(--color-error);
		box-shadow: 0 0 12px rgba(239, 68, 68, 0.3);
	}
	@keyframes pulse-reasoning {
		0%, 100% {
			box-shadow: 0 0 8px rgba(236, 72, 153, 0.15);
		}
		50% {
			box-shadow: 0 0 20px rgba(236, 72, 153, 0.4);
		}
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
	.state-icon {
		margin-left: auto;
		display: flex;
		align-items: center;
	}
	.state-complete {
		color: var(--color-success);
	}
	.state-error {
		color: var(--color-error);
	}
</style>
