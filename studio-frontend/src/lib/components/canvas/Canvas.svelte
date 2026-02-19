<script lang="ts">
	import {
		SvelteFlow,
		Controls,
		MiniMap,
		Background,
		BackgroundVariant
	} from '@xyflow/svelte';
	import { nodes, edges } from '$lib/stores/pipeline';
	import AgentNode from './nodes/AgentNode.svelte';
	import ToolNode from './nodes/ToolNode.svelte';
	import ReasoningNode from './nodes/ReasoningNode.svelte';
	import ConditionNode from './nodes/ConditionNode.svelte';

	const nodeTypes = {
		agent: AgentNode,
		tool: ToolNode,
		reasoning: ReasoningNode,
		condition: ConditionNode
	};
</script>

<div class="canvas-wrapper">
	<SvelteFlow
		{nodeTypes}
		bind:nodes={$nodes}
		bind:edges={$edges}
		fitView
		colorMode="dark"
		defaultEdgeOptions={{ animated: true }}
	>
		<Controls position="bottom-left" />
		<MiniMap position="bottom-right" />
		<Background variant={BackgroundVariant.Dots} gap={20} size={1} />
	</SvelteFlow>
</div>

<style>
	.canvas-wrapper {
		width: 100%;
		height: 100%;
	}
</style>
