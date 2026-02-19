<script lang="ts">
	import Canvas from '$lib/components/canvas/Canvas.svelte';
	import NodePalette from '$lib/components/canvas/NodePalette.svelte';
	import ConfigPanel from '$lib/components/panels/ConfigPanel.svelte';
	import BottomPanel from '$lib/components/panels/BottomPanel.svelte';
	import { selectedNodeId } from '$lib/stores/pipeline';
</script>

<div class="build-page">
	<div class="top-area">
		<NodePalette />
		<Canvas />
		{#if $selectedNodeId}
			<ConfigPanel />
		{/if}
	</div>
	<BottomPanel />
</div>

<style>
	.build-page {
		display: flex;
		flex-direction: column;
		height: 100%;
		width: 100%;
	}

	.top-area {
		display: flex;
		flex: 1;
		min-height: 0;
		overflow: hidden;
	}
</style>
