<script lang="ts">
	import { MessageSquare } from 'lucide-svelte';
</script>

<div class="chat-tab">
	<div class="placeholder">
		<div class="placeholder-icon">
			<MessageSquare size={32} />
		</div>
		<span class="placeholder-title">AI Assistant will be available here</span>
		<span class="placeholder-hint">Ask me to help build your pipeline</span>
	</div>
</div>

<style>
	.chat-tab {
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

	.placeholder-title {
		font-size: 12px;
		color: var(--color-text-secondary, #8888a0);
		text-align: center;
	}

	.placeholder-hint {
		font-size: 11px;
		color: var(--color-text-secondary, #8888a0);
		opacity: 0.6;
	}
</style>
