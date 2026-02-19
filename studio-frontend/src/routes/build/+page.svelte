<script lang="ts">
	import Canvas from '$lib/components/canvas/Canvas.svelte';
	import NodePalette from '$lib/components/canvas/NodePalette.svelte';
</script>

<div class="build-page">
	<NodePalette />
	<Canvas />
</div>

<style>
	.build-page {
		display: flex;
		height: 100%;
		width: 100%;
	}
</style>
