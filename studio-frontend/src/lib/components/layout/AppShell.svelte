<script lang="ts">
	import TopBar from './TopBar.svelte';
	import Sidebar from './Sidebar.svelte';

	let { children } = $props();
</script>

<div class="app-shell">
	<TopBar />
	<div class="app-body">
		<Sidebar />
		<main class="app-content">
			{@render children()}
		</main>
	</div>
</div>

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
