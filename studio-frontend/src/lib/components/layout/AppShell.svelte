<script lang="ts">
	import TopBar from './TopBar.svelte';
	import Sidebar from './Sidebar.svelte';
	import CommandPalette from './CommandPalette.svelte';
	import { commandPaletteOpen } from '$lib/stores/ui';

	let { children } = $props();

	function handleKeydown(e: KeyboardEvent) {
		if (e.key === 'k' && (e.metaKey || e.ctrlKey)) {
			e.preventDefault();
			commandPaletteOpen.update((v) => !v);
		}
	}
</script>

<svelte:window onkeydown={handleKeydown} />

<div class="app-shell">
	<TopBar />
	<div class="app-body">
		<Sidebar />
		<main class="app-content">
			{@render children()}
		</main>
	</div>
</div>

<CommandPalette />

<style>
	.app-shell {
		display: flex;
		flex-direction: column;
		height: 100vh;
		width: 100vw;
		overflow: hidden;
		background: var(--color-bg-primary);
		color: var(--color-text-primary);
	}

	.app-body {
		display: flex;
		flex: 1;
		min-height: 0;
	}

	.app-content {
		flex: 1;
		min-width: 0;
		overflow: auto;
	}
</style>
