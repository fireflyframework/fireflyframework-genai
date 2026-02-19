<script lang="ts">
	import { FolderOpen, FileText, FileCode, ChevronRight, ChevronDown, File } from 'lucide-svelte';

	interface FileNode {
		name: string;
		type: 'folder' | 'file';
		icon: typeof FileText;
		children?: FileNode[];
		expanded?: boolean;
	}

	let fileTree: FileNode[] = $state([
		{
			name: 'my-agent',
			type: 'folder',
			icon: FolderOpen,
			expanded: true,
			children: [
				{
					name: 'pipelines',
					type: 'folder',
					icon: FolderOpen,
					expanded: true,
					children: [
						{ name: 'main.py', type: 'file', icon: FileCode }
					]
				},
				{
					name: 'tools',
					type: 'folder',
					icon: FolderOpen,
					expanded: true,
					children: [
						{ name: 'search.py', type: 'file', icon: FileCode }
					]
				},
				{ name: 'config.yaml', type: 'file', icon: FileText }
			]
		}
	]);

	let selectedFile: string | null = $state(null);

	function toggleFolder(node: FileNode) {
		if (node.type === 'folder') {
			node.expanded = !node.expanded;
		}
	}

	function selectFile(node: FileNode) {
		if (node.type === 'file') {
			selectedFile = node.name;
		}
	}

	function getFileIcon(name: string): string {
		if (name.endsWith('.py')) return 'Python';
		if (name.endsWith('.yaml') || name.endsWith('.yml')) return 'YAML';
		if (name.endsWith('.json')) return 'JSON';
		return 'Text';
	}
</script>

<div class="page">
	<div class="page-header">
		<div class="page-title">
			<FolderOpen size={20} class="text-accent" />
			<h1>Project Files</h1>
			<span class="project-badge">my-agent</span>
		</div>
	</div>

	<div class="page-content">
		<div class="split-layout">
			<!-- File Tree -->
			<div class="file-tree-panel">
				<div class="panel-header">
					<span class="panel-title">Explorer</span>
				</div>
				<div class="tree-content">
					{#each fileTree as node}
						{@render treeNode(node, 0)}
					{/each}
				</div>
			</div>

			<!-- Content Area -->
			<div class="content-panel">
				{#if selectedFile}
					<div class="content-header">
						<File size={14} />
						<span class="content-filename">{selectedFile}</span>
						<span class="content-type">{getFileIcon(selectedFile)}</span>
					</div>
					<div class="content-placeholder">
						<div class="placeholder-lines">
							{#each Array(12) as _, i}
								<div class="placeholder-line" style="width: {30 + Math.random() * 60}%; opacity: {0.3 + Math.random() * 0.3}"></div>
							{/each}
						</div>
						<div class="placeholder-overlay">
							<FileCode size={32} />
							<span>File preview not yet available</span>
							<span class="placeholder-hint">Backend file reading API will be connected in a future release</span>
						</div>
					</div>
				{:else}
					<div class="no-selection">
						<div class="no-selection-icon">
							<FileText size={40} />
						</div>
						<span class="no-selection-text">Select a file to view its contents</span>
						<span class="no-selection-hint">Browse the project tree on the left</span>
					</div>
				{/if}
			</div>
		</div>
	</div>
</div>

{#snippet treeNode(node: FileNode, depth: number)}
	<button
		class="tree-item"
		class:selected={node.type === 'file' && selectedFile === node.name}
		style="padding-left: {12 + depth * 16}px"
		onclick={() => {
			if (node.type === 'folder') {
				toggleFolder(node);
			} else {
				selectFile(node);
			}
		}}
	>
		{#if node.type === 'folder'}
			<span class="tree-chevron">
				{#if node.expanded}
					<ChevronDown size={14} />
				{:else}
					<ChevronRight size={14} />
				{/if}
			</span>
		{:else}
			<span class="tree-chevron-spacer"></span>
		{/if}
		<node.icon size={14} class={node.type === 'folder' ? 'tree-icon-folder' : 'tree-icon-file'} />
		<span class="tree-name">{node.name}</span>
	</button>
	{#if node.type === 'folder' && node.expanded && node.children}
		{#each node.children as child}
			{@render treeNode(child, depth + 1)}
		{/each}
	{/if}
{/snippet}

<style>
	.page {
		display: flex;
		flex-direction: column;
		height: 100%;
		padding: 24px;
		gap: 24px;
		overflow: hidden;
		background: var(--color-bg-primary);
	}

	.page-header {
		display: flex;
		align-items: center;
		justify-content: space-between;
		flex-shrink: 0;
	}

	.page-title {
		display: flex;
		align-items: center;
		gap: 12px;
	}

	.page-title h1 {
		font-size: 20px;
		font-weight: 600;
		color: var(--color-text-primary);
		margin: 0;
	}

	.project-badge {
		font-size: 11px;
		font-weight: 500;
		padding: 3px 10px;
		border-radius: 6px;
		background: oklch(from var(--color-accent) l c h / 12%);
		color: var(--color-accent);
		font-family: var(--font-mono);
	}

	.page-content {
		flex: 1;
		min-height: 0;
	}

	/* Split Layout */
	.split-layout {
		display: flex;
		height: 100%;
		gap: 1px;
		background: var(--color-border);
		border-radius: 12px;
		overflow: hidden;
	}

	/* File Tree Panel */
	.file-tree-panel {
		width: 240px;
		flex-shrink: 0;
		display: flex;
		flex-direction: column;
		background: var(--color-bg-elevated);
		overflow: hidden;
	}

	.panel-header {
		display: flex;
		align-items: center;
		padding: 12px 14px;
		border-bottom: 1px solid var(--color-border);
	}

	.panel-title {
		font-size: 11px;
		font-weight: 600;
		text-transform: uppercase;
		letter-spacing: 0.05em;
		color: var(--color-text-secondary);
	}

	.tree-content {
		flex: 1;
		overflow-y: auto;
		padding: 4px 0;
	}

	/* Tree Items */
	.tree-item {
		display: flex;
		align-items: center;
		gap: 6px;
		width: 100%;
		padding: 5px 12px;
		border: none;
		background: transparent;
		color: var(--color-text-primary);
		font-size: 12px;
		cursor: pointer;
		transition: background 0.1s;
		text-align: left;
	}

	.tree-item:hover {
		background: oklch(from var(--color-border) l c h / 30%);
	}

	.tree-item.selected {
		background: oklch(from var(--color-accent) l c h / 12%);
		color: var(--color-accent);
	}

	.tree-chevron {
		display: flex;
		align-items: center;
		justify-content: center;
		width: 14px;
		flex-shrink: 0;
		color: var(--color-text-secondary);
	}

	.tree-chevron-spacer {
		width: 14px;
		flex-shrink: 0;
	}

	.tree-name {
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}

	:global(.tree-icon-folder) {
		color: var(--color-accent);
		flex-shrink: 0;
	}

	:global(.tree-icon-file) {
		color: var(--color-text-secondary);
		flex-shrink: 0;
	}

	/* Content Panel */
	.content-panel {
		flex: 1;
		display: flex;
		flex-direction: column;
		background: var(--color-bg-elevated);
		overflow: hidden;
	}

	.content-header {
		display: flex;
		align-items: center;
		gap: 8px;
		padding: 10px 16px;
		border-bottom: 1px solid var(--color-border);
		color: var(--color-text-secondary);
		font-size: 12px;
	}

	.content-filename {
		color: var(--color-text-primary);
		font-weight: 500;
		font-family: var(--font-mono);
	}

	.content-type {
		margin-left: auto;
		font-size: 10px;
		text-transform: uppercase;
		letter-spacing: 0.04em;
		padding: 2px 6px;
		border-radius: 3px;
		background: oklch(from var(--color-text-secondary) l c h / 10%);
		color: var(--color-text-secondary);
	}

	/* Content Placeholder */
	.content-placeholder {
		flex: 1;
		position: relative;
		padding: 20px;
		overflow: hidden;
	}

	.placeholder-lines {
		display: flex;
		flex-direction: column;
		gap: 10px;
	}

	.placeholder-line {
		height: 12px;
		border-radius: 3px;
		background: var(--color-border);
	}

	.placeholder-overlay {
		position: absolute;
		inset: 0;
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		gap: 10px;
		background: oklch(from var(--color-bg-elevated) l c h / 85%);
		color: var(--color-text-secondary);
		font-size: 13px;
	}

	.placeholder-hint {
		font-size: 11px;
		color: oklch(from var(--color-text-secondary) l c h / 60%);
	}

	/* No Selection */
	.no-selection {
		flex: 1;
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		gap: 12px;
	}

	.no-selection-icon {
		display: flex;
		align-items: center;
		justify-content: center;
		width: 72px;
		height: 72px;
		border-radius: 16px;
		background: oklch(from var(--color-text-secondary) l c h / 8%);
		color: var(--color-text-secondary);
	}

	.no-selection-text {
		font-size: 14px;
		font-weight: 500;
		color: var(--color-text-secondary);
	}

	.no-selection-hint {
		font-size: 12px;
		color: oklch(from var(--color-text-secondary) l c h / 60%);
	}
</style>
