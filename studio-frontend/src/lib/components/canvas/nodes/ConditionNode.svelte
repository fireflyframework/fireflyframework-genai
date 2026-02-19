<script lang="ts">
	import { Handle, Position } from '@xyflow/svelte';
	import { CircleDot, CheckCircle2, AlertCircle } from 'lucide-svelte';

	let { data } = $props();

	let execState = $derived((data._executionState as string) ?? 'idle');
	let showComplete = $state(false);

	$effect(() => {
		if (execState === 'complete') {
			showComplete = true;
			const timer = setTimeout(() => {
				showComplete = false;
			}, 3000);
			return () => clearTimeout(timer);
		} else {
			showComplete = false;
		}
	});
</script>

<div class="condition-node">
	<div
		class="diamond"
		class:exec-running={execState === 'running'}
		class:exec-complete={execState === 'complete'}
		class:exec-error={execState === 'error'}
	>
		<div class="diamond-content">
			<div class="icon-wrapper condition-icon">
				<CircleDot size={12} />
			</div>
			<span class="node-label">{data.label || 'Condition'}</span>
			{#if showComplete}
				<span class="state-icon state-complete">
					<CheckCircle2 size={10} />
				</span>
			{/if}
			{#if execState === 'error'}
				<span class="state-icon state-error">
					<AlertCircle size={10} />
				</span>
			{/if}
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
		transition: border-color 0.3s ease, box-shadow 0.3s ease;
	}
	.diamond.exec-running {
		animation: pulse-condition 1.5s ease-in-out infinite;
	}
	.diamond.exec-complete {
		border-color: var(--color-success);
		box-shadow: 0 0 12px rgba(34, 197, 94, 0.3);
	}
	.diamond.exec-error {
		border-color: var(--color-error);
		box-shadow: 0 0 12px rgba(239, 68, 68, 0.3);
	}
	@keyframes pulse-condition {
		0%, 100% {
			box-shadow: 0 0 8px rgba(136, 136, 160, 0.15);
		}
		50% {
			box-shadow: 0 0 20px rgba(136, 136, 160, 0.4);
		}
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
	.state-icon {
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
