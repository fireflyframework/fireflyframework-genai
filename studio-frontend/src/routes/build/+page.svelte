<script lang="ts">
	import Canvas from '$lib/components/canvas/Canvas.svelte';
	import NodePalette from '$lib/components/canvas/NodePalette.svelte';
	import ConfigPanel from '$lib/components/panels/ConfigPanel.svelte';
	import { selectedNodeId } from '$lib/stores/pipeline';
</script>

<div class="build-page">
	<NodePalette />
	<Canvas />
	{#if $selectedNodeId}
		<ConfigPanel />
	{/if}
</div>

<style>
	.build-page {
		display: flex;
		height: 100%;
		width: 100%;
	}
</style>
