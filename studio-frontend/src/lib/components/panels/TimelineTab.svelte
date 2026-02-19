<script lang="ts">
	import { Clock } from 'lucide-svelte';
	import { checkpoints } from '$lib/stores/execution';
</script>

<div class="timeline-tab">
	<div class="placeholder">
		<div class="placeholder-icon">
			<Clock size={32} />
		</div>
		<span class="placeholder-text">Timeline visualization will appear here during execution</span>
		{#if $checkpoints.length > 0}
			<span class="checkpoint-count">{$checkpoints.length} checkpoint{$checkpoints.length === 1 ? '' : 's'} recorded</span>
		{/if}
	</div>
</div>

<style>
	.timeline-tab {
		display: flex;
		align-items: center;
		justify-content: center;
		height: 100%;
	}

	.placeholder {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 12px;
		padding: 24px;
	}

	.placeholder-icon {
		color: var(--color-text-secondary, #8888a0);
		opacity: 0.4;
	}

	.placeholder-text {
		font-size: 12px;
		color: var(--color-text-secondary, #8888a0);
		text-align: center;
	}

	.checkpoint-count {
		font-size: 11px;
		color: var(--color-accent, #ff6b35);
		font-weight: 500;
	}
</style>
