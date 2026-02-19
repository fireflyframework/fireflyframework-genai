<script lang="ts">
	import { onMount } from 'svelte';
	import { Copy, RefreshCw, Check } from 'lucide-svelte';
	import { nodes, edges } from '$lib/stores/pipeline';
	import { api } from '$lib/api/client';
	import { get } from 'svelte/store';

	let code = $state('');
	let loading = $state(false);
	let error = $state('');
	let copied = $state(false);

	function serializeGraph() {
		const currentNodes = get(nodes);
		const currentEdges = get(edges);
		const serializedNodes = currentNodes.map((n) => ({
			id: n.id,
			type: n.type,
			label: (n.data?.label as string) ?? '',
			position: n.position,
			data: n.data
		}));
		const serializedEdges = currentEdges.map((e) => ({
			id: e.id,
			source: e.source,
			target: e.target
		}));
		return { nodes: serializedNodes, edges: serializedEdges };
	}

	async function generateCode() {
		loading = true;
		error = '';
		try {
			const graph = serializeGraph();
			const result = await api.codegen.toCode(graph);
			code = result.code;
		} catch (err) {
			error = err instanceof Error ? err.message : 'Code generation failed';
			code = '';
		} finally {
			loading = false;
		}
	}

	async function copyToClipboard() {
		if (!code) return;
		try {
			await navigator.clipboard.writeText(code);
			copied = true;
			setTimeout(() => {
				copied = false;
			}, 2000);
		} catch {
			// Clipboard API not available
		}
	}

	// Generate code on mount
	onMount(() => {
		generateCode();
	});
</script>

<div class="code-tab">
	<div class="code-toolbar">
		<span class="toolbar-label">Generated Python</span>
		<div class="toolbar-actions">
			<button class="toolbar-btn" onclick={copyToClipboard} title="Copy to clipboard" disabled={!code}>
				{#if copied}
					<Check size={13} />
				{:else}
					<Copy size={13} />
				{/if}
			</button>
			<button class="toolbar-btn" onclick={generateCode} title="Regenerate code" disabled={loading}>
				<RefreshCw size={13} class={loading ? 'spin' : ''} />
			</button>
		</div>
	</div>

	<div class="code-content">
		{#if loading}
			<div class="code-state">
				<RefreshCw size={20} class="spin" />
				<span>Generating code...</span>
			</div>
		{:else if error}
			<div class="code-state code-error">
				<span>{error}</span>
			</div>
		{:else if code}
			<pre class="code-block"><code>{code}</code></pre>
		{:else}
			<div class="code-state">
				<span>Add nodes to your pipeline to generate code.</span>
			</div>
		{/if}
	</div>
</div>

<style>
	.code-tab {
		display: flex;
		flex-direction: column;
		height: 100%;
		overflow: hidden;
	}

	.code-toolbar {
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: 6px 12px;
		border-bottom: 1px solid var(--color-border, #2a2a3a);
		flex-shrink: 0;
	}

	.toolbar-label {
		font-size: 11px;
		color: var(--color-text-secondary, #8888a0);
		font-weight: 500;
	}

	.toolbar-actions {
		display: flex;
		gap: 4px;
	}

	.toolbar-btn {
		display: flex;
		align-items: center;
		justify-content: center;
		width: 26px;
		height: 26px;
		border: none;
		background: transparent;
		border-radius: 4px;
		color: var(--color-text-secondary, #8888a0);
		cursor: pointer;
		transition: background 0.15s ease, color 0.15s ease;
	}

	.toolbar-btn:hover:not(:disabled) {
		background: rgba(255, 255, 255, 0.05);
		color: var(--color-text-primary, #e8e8ed);
	}

	.toolbar-btn:disabled {
		opacity: 0.4;
		cursor: not-allowed;
	}

	.code-content {
		flex: 1;
		overflow-y: auto;
		font-family: var(--font-mono, 'JetBrains Mono', ui-monospace, monospace);
		font-size: 12px;
		line-height: 1.6;
	}

	.code-state {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		height: 100%;
		gap: 8px;
		color: var(--color-text-secondary, #8888a0);
		font-size: 12px;
	}

	.code-error {
		color: var(--color-error, #ef4444);
	}

	.code-block {
		margin: 0;
		padding: 12px;
		white-space: pre;
		color: var(--color-text-primary, #e8e8ed);
		tab-size: 4;
	}

	:global(.spin) {
		animation: spin 1s linear infinite;
	}

	@keyframes spin {
		from { transform: rotate(0deg); }
		to { transform: rotate(360deg); }
	}
</style>
