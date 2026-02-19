<script lang="ts">
	import { FlaskConical, Plus, CheckCircle2, XCircle, Loader2, Calendar } from 'lucide-svelte';

	let showPreview: boolean = $state(true);

	interface Evaluation {
		name: string;
		dataset: string;
		status: 'passed' | 'failed' | 'running';
		date: string;
		passed: number;
		total: number;
	}

	const mockEvaluations: Evaluation[] = [
		{
			name: 'Customer Support QA',
			dataset: 'support-tickets-v2.jsonl',
			status: 'passed',
			date: '2026-02-18',
			passed: 26,
			total: 30
		},
		{
			name: 'Tool Selection Accuracy',
			dataset: 'tool-selection-bench.jsonl',
			status: 'passed',
			date: '2026-02-17',
			passed: 28,
			total: 30
		}
	];

	function passRate(ev: Evaluation): number {
		return Math.round((ev.passed / ev.total) * 100);
	}

	function statusColor(status: string): string {
		if (status === 'passed') return 'var(--color-success)';
		if (status === 'failed') return 'var(--color-error)';
		return 'var(--color-warning)';
	}
</script>

<div class="page">
	<div class="page-header">
		<div class="page-title">
			<FlaskConical size={20} class="text-accent" />
			<h1>Evaluation Lab</h1>
		</div>
		<div class="page-actions">
			<button class="btn-primary">
				<Plus size={14} />
				New Evaluation
			</button>
		</div>
	</div>

	<div class="page-content">
		<!-- Empty State -->
		<div class="empty-state-card">
			<div class="empty-icon">
				<FlaskConical size={48} />
			</div>
			<h2 class="empty-title">No evaluations yet</h2>
			<p class="empty-subtitle">
				Upload a dataset and run your pipeline against it to measure quality
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
				<div class="eval-grid">
					{#each mockEvaluations as ev}
						<div class="eval-card">
							<div class="eval-card-header">
								<div class="eval-info">
									<h3 class="eval-name">{ev.name}</h3>
									<span class="eval-dataset">{ev.dataset}</span>
								</div>
								<span
									class="status-badge"
									style="--status-color: {statusColor(ev.status)}"
								>
									{#if ev.status === 'passed'}
										<CheckCircle2 size={12} />
									{:else if ev.status === 'failed'}
										<XCircle size={12} />
									{:else}
										<Loader2 size={12} class="spin" />
									{/if}
									{ev.status}
								</span>
							</div>

							<div class="eval-metrics">
								<div class="eval-score">
									<span class="score-value">{passRate(ev)}%</span>
									<span class="score-label">Pass Rate</span>
								</div>
								<div class="eval-counts">
									<span class="count-detail">{ev.passed}/{ev.total} passed</span>
									<span class="eval-date">
										<Calendar size={12} />
										{ev.date}
									</span>
								</div>
							</div>

							<div class="progress-bar">
								<div
									class="progress-fill progress-pass"
									style="width: {passRate(ev)}%"
								></div>
								<div
									class="progress-fill progress-fail"
									style="width: {100 - passRate(ev)}%"
								></div>
							</div>
						</div>
					{/each}
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

	/* Evaluation Grid */
	.eval-grid {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(380px, 1fr));
		gap: 16px;
	}

	.eval-card {
		background: var(--color-bg-elevated);
		border: 1px solid var(--color-border);
		border-radius: 12px;
		padding: 20px;
		display: flex;
		flex-direction: column;
		gap: 16px;
	}

	.eval-card-header {
		display: flex;
		align-items: flex-start;
		justify-content: space-between;
		gap: 12px;
	}

	.eval-info {
		display: flex;
		flex-direction: column;
		gap: 4px;
	}

	.eval-name {
		font-size: 15px;
		font-weight: 600;
		color: var(--color-text-primary);
		margin: 0;
	}

	.eval-dataset {
		font-size: 12px;
		color: var(--color-text-secondary);
		font-family: var(--font-mono);
	}

	.status-badge {
		display: inline-flex;
		align-items: center;
		gap: 5px;
		padding: 4px 10px;
		border-radius: 6px;
		font-size: 11px;
		font-weight: 500;
		text-transform: capitalize;
		background: oklch(from var(--status-color) l c h / 15%);
		color: var(--status-color);
		flex-shrink: 0;
	}

	.eval-metrics {
		display: flex;
		align-items: center;
		justify-content: space-between;
	}

	.eval-score {
		display: flex;
		align-items: baseline;
		gap: 8px;
	}

	.score-value {
		font-size: 28px;
		font-weight: 700;
		color: var(--color-text-primary);
		font-family: var(--font-mono);
		line-height: 1;
	}

	.score-label {
		font-size: 11px;
		font-weight: 500;
		text-transform: uppercase;
		letter-spacing: 0.05em;
		color: var(--color-text-secondary);
	}

	.eval-counts {
		display: flex;
		flex-direction: column;
		align-items: flex-end;
		gap: 4px;
	}

	.count-detail {
		font-size: 13px;
		color: var(--color-text-secondary);
		font-family: var(--font-mono);
	}

	.eval-date {
		display: flex;
		align-items: center;
		gap: 4px;
		font-size: 11px;
		color: var(--color-text-secondary);
	}

	/* Progress Bar */
	.progress-bar {
		display: flex;
		height: 6px;
		border-radius: 3px;
		overflow: hidden;
		background: var(--color-bg-secondary);
	}

	.progress-fill {
		height: 100%;
		transition: width 0.3s ease;
	}

	.progress-pass {
		background: var(--color-success);
	}

	.progress-fail {
		background: var(--color-error);
	}

	:global(.spin) {
		animation: spin 1s linear infinite;
	}

	@keyframes spin {
		from { transform: rotate(0deg); }
		to { transform: rotate(360deg); }
	}
</style>
