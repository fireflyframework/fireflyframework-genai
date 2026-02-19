<script lang="ts">
	import { GitBranch, Plus, ArrowRight } from 'lucide-svelte';

	let showPreview: boolean = $state(true);

	interface Variant {
		name: string;
		pipeline: string;
		traffic: number;
		successRate: number;
	}

	interface Experiment {
		name: string;
		status: 'running' | 'completed' | 'draft';
		createdDate: string;
		variants: Variant[];
	}

	const mockExperiment: Experiment = {
		name: 'GPT-4o vs Claude Sonnet',
		status: 'running',
		createdDate: '2026-02-16',
		variants: [
			{
				name: 'Variant A',
				pipeline: 'GPT-4o pipeline',
				traffic: 50,
				successRate: 89
			},
			{
				name: 'Variant B',
				pipeline: 'Claude pipeline',
				traffic: 50,
				successRate: 92
			}
		]
	};

	function statusColor(status: string): string {
		if (status === 'running') return 'var(--color-success)';
		if (status === 'completed') return 'var(--color-info)';
		return 'var(--color-text-secondary)';
	}
</script>

<div class="page">
	<div class="page-header">
		<div class="page-title">
			<GitBranch size={20} class="text-accent" />
			<h1>Experiments</h1>
		</div>
		<div class="page-actions">
			<button class="btn-primary">
				<Plus size={14} />
				New Experiment
			</button>
		</div>
	</div>

	<div class="page-content">
		<!-- Empty State -->
		<div class="empty-state-card">
			<div class="empty-icon">
				<GitBranch size={48} />
			</div>
			<h2 class="empty-title">Design your first experiment</h2>
			<p class="empty-subtitle">
				Compare pipeline variants side-by-side with configurable traffic splits
			</p>
			<button class="btn-primary">
				<Plus size={14} />
				Get Started
			</button>
		</div>

		<!-- Preview Section -->
		<div class="preview-section">
			<div class="preview-header">
				<h2 class="preview-title">Preview</h2>
				<span class="preview-badge">Mock Data</span>
				<button class="btn-secondary btn-sm" onclick={() => showPreview = !showPreview}>
					{showPreview ? 'Hide' : 'Show'}
				</button>
			</div>

			{#if showPreview}
				<div class="experiment-card">
					<div class="experiment-card-header">
						<div class="experiment-info">
							<h3 class="experiment-name">{mockExperiment.name}</h3>
							<span class="experiment-date">Created {mockExperiment.createdDate}</span>
						</div>
						<span
							class="status-badge"
							style="--status-color: {statusColor(mockExperiment.status)}"
						>
							{#if mockExperiment.status === 'running'}
								<span class="pulse-dot"></span>
							{/if}
							{mockExperiment.status}
						</span>
					</div>

					<!-- Traffic Split Visual -->
					<div class="traffic-split-bar">
						{#each mockExperiment.variants as variant, i}
							<div
								class="traffic-segment"
								style="width: {variant.traffic}%; --segment-color: {i === 0 ? 'var(--color-info)' : 'var(--color-accent)'}"
							>
								<span class="segment-label">{variant.name} ({variant.traffic}%)</span>
							</div>
						{/each}
					</div>

					<!-- Variant Rows -->
					<div class="variants-list">
						{#each mockExperiment.variants as variant, i}
							<div class="variant-row">
								<div class="variant-indicator" style="--indicator-color: {i === 0 ? 'var(--color-info)' : 'var(--color-accent)'}"></div>
								<div class="variant-details">
									<div class="variant-name-row">
										<span class="variant-name">{variant.name}</span>
										<span class="variant-pipeline">{variant.pipeline}</span>
									</div>
									<div class="variant-stats">
										<div class="stat">
											<span class="stat-label">Traffic</span>
											<span class="stat-value">{variant.traffic}%</span>
										</div>
										<div class="stat">
											<span class="stat-label">Success Rate</span>
											<span class="stat-value">{variant.successRate}%</span>
										</div>
									</div>
								</div>
							</div>
						{/each}
					</div>

					<div class="experiment-card-footer">
						<button class="btn-secondary">
							View Results
							<ArrowRight size={14} />
						</button>
					</div>
				</div>
			{/if}
		</div>
	</div>
</div>

<style>
	.page {
		display: flex;
		flex-direction: column;
		height: 100%;
		padding: 24px;
		gap: 24px;
		overflow-y: auto;
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

	.page-content {
		flex: 1;
		display: flex;
		flex-direction: column;
		gap: 24px;
	}

	/* Buttons */
	.btn-primary {
		display: flex;
		align-items: center;
		gap: 6px;
		padding: 8px 16px;
		background: var(--color-accent);
		border: none;
		border-radius: 8px;
		color: white;
		font-size: 13px;
		font-weight: 500;
		cursor: pointer;
		transition: opacity 0.15s;
	}

	.btn-primary:hover {
		opacity: 0.9;
	}

	.btn-secondary {
		display: flex;
		align-items: center;
		gap: 6px;
		padding: 6px 14px;
		background: transparent;
		border: 1px solid var(--color-border);
		border-radius: 6px;
		color: var(--color-text-primary);
		font-size: 12px;
		cursor: pointer;
		transition: border-color 0.15s;
	}

	.btn-secondary:hover {
		border-color: var(--color-accent);
	}

	.btn-sm {
		padding: 4px 10px;
		font-size: 11px;
	}

	/* Empty State */
	.empty-state-card {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		padding: 48px 24px;
		background: var(--color-bg-elevated);
		border: 1px solid var(--color-border);
		border-radius: 12px;
		text-align: center;
		gap: 16px;
	}

	.empty-icon {
		display: flex;
		align-items: center;
		justify-content: center;
		width: 80px;
		height: 80px;
		border-radius: 16px;
		background: oklch(from var(--color-accent) l c h / 10%);
		color: var(--color-accent);
	}

	.empty-title {
		font-size: 18px;
		font-weight: 600;
		color: var(--color-text-primary);
		margin: 0;
	}

	.empty-subtitle {
		font-size: 13px;
		color: var(--color-text-secondary);
		margin: 0;
		max-width: 400px;
		line-height: 1.5;
	}

	/* Preview Section */
	.preview-section {
		display: flex;
		flex-direction: column;
		gap: 16px;
	}

	.preview-header {
		display: flex;
		align-items: center;
		gap: 12px;
	}

	.preview-title {
		font-size: 14px;
		font-weight: 600;
		color: var(--color-text-primary);
		margin: 0;
	}

	.preview-badge {
		font-size: 10px;
		font-weight: 500;
		text-transform: uppercase;
		letter-spacing: 0.05em;
		padding: 2px 8px;
		border-radius: 4px;
		background: oklch(from var(--color-info) l c h / 15%);
		color: var(--color-info);
	}

	/* Experiment Card */
	.experiment-card {
		background: var(--color-bg-elevated);
		border: 1px solid var(--color-border);
		border-radius: 12px;
		padding: 20px;
		display: flex;
		flex-direction: column;
		gap: 20px;
	}

	.experiment-card-header {
		display: flex;
		align-items: flex-start;
		justify-content: space-between;
		gap: 12px;
	}

	.experiment-info {
		display: flex;
		flex-direction: column;
		gap: 4px;
	}

	.experiment-name {
		font-size: 16px;
		font-weight: 600;
		color: var(--color-text-primary);
		margin: 0;
	}

	.experiment-date {
		font-size: 12px;
		color: var(--color-text-secondary);
	}

	.status-badge {
		display: inline-flex;
		align-items: center;
		gap: 6px;
		padding: 4px 10px;
		border-radius: 6px;
		font-size: 11px;
		font-weight: 500;
		text-transform: capitalize;
		background: oklch(from var(--status-color) l c h / 15%);
		color: var(--status-color);
		flex-shrink: 0;
	}

	.pulse-dot {
		width: 6px;
		height: 6px;
		border-radius: 50%;
		background: var(--color-success);
		animation: pulse-glow 2s ease-in-out infinite;
	}

	@keyframes pulse-glow {
		0%, 100% { opacity: 1; transform: scale(1); }
		50% { opacity: 0.5; transform: scale(1.3); }
	}

	/* Traffic Split Bar */
	.traffic-split-bar {
		display: flex;
		height: 32px;
		border-radius: 6px;
		overflow: hidden;
		gap: 2px;
	}

	.traffic-segment {
		display: flex;
		align-items: center;
		justify-content: center;
		background: oklch(from var(--segment-color) l c h / 20%);
		color: var(--segment-color);
		transition: width 0.3s ease;
	}

	.segment-label {
		font-size: 11px;
		font-weight: 500;
	}

	/* Variant Rows */
	.variants-list {
		display: flex;
		flex-direction: column;
		gap: 12px;
	}

	.variant-row {
		display: flex;
		align-items: stretch;
		gap: 12px;
		padding: 14px;
		background: var(--color-bg-secondary);
		border-radius: 8px;
		border: 1px solid oklch(from var(--color-border) l c h / 60%);
	}

	.variant-indicator {
		width: 4px;
		border-radius: 2px;
		background: var(--indicator-color);
		flex-shrink: 0;
	}

	.variant-details {
		flex: 1;
		display: flex;
		flex-direction: column;
		gap: 10px;
	}

	.variant-name-row {
		display: flex;
		align-items: center;
		gap: 10px;
	}

	.variant-name {
		font-size: 13px;
		font-weight: 600;
		color: var(--color-text-primary);
	}

	.variant-pipeline {
		font-size: 12px;
		color: var(--color-text-secondary);
		font-family: var(--font-mono);
	}

	.variant-stats {
		display: flex;
		gap: 24px;
	}

	.stat {
		display: flex;
		flex-direction: column;
		gap: 2px;
	}

	.stat-label {
		font-size: 10px;
		font-weight: 500;
		text-transform: uppercase;
		letter-spacing: 0.05em;
		color: var(--color-text-secondary);
	}

	.stat-value {
		font-size: 16px;
		font-weight: 700;
		color: var(--color-text-primary);
		font-family: var(--font-mono);
	}

	.experiment-card-footer {
		display: flex;
		justify-content: flex-end;
		padding-top: 4px;
		border-top: 1px solid var(--color-border);
	}
</style>
