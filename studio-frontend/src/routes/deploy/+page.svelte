<script lang="ts">
	import { Rocket, Container, Globe, Cloud, ArrowRight, Clock } from 'lucide-svelte';

	interface DeployTarget {
		name: string;
		description: string;
		icon: typeof Container;
		action: string;
		disabled: boolean;
	}

	const deployTargets: DeployTarget[] = [
		{
			name: 'Docker Container',
			description: 'Generate a Dockerfile for your pipeline',
			icon: Container,
			action: 'Generate',
			disabled: false
		},
		{
			name: 'REST API',
			description: 'Deploy as a FastAPI endpoint',
			icon: Globe,
			action: 'Configure',
			disabled: false
		},
		{
			name: 'Cloud Function',
			description: 'Deploy to AWS Lambda / GCP Cloud Functions',
			icon: Cloud,
			action: 'Coming Soon',
			disabled: true
		}
	];
</script>

<div class="page">
	<div class="page-header">
		<div class="page-title">
			<Rocket size={20} class="text-accent" />
			<h1>Deploy</h1>
		</div>
	</div>

	<div class="page-content">
		<!-- Deployment Targets -->
		<div class="section">
			<h2 class="section-title">Deployment Targets</h2>
			<div class="targets-grid">
				{#each deployTargets as target}
					<div class="target-card" class:disabled={target.disabled}>
						<div class="target-icon">
							<target.icon size={28} />
						</div>
						<div class="target-info">
							<h3 class="target-name">{target.name}</h3>
							<p class="target-description">{target.description}</p>
						</div>
						<div class="target-action">
							{#if target.disabled}
								<span class="coming-soon-badge">
									<Clock size={12} />
									Coming Soon
								</span>
							{:else}
								<button class="btn-secondary">
									{target.action}
									<ArrowRight size={14} />
								</button>
							{/if}
						</div>
					</div>
				{/each}
			</div>
		</div>

		<!-- Recent Deployments -->
		<div class="section">
			<h2 class="section-title">Recent Deployments</h2>
			<div class="empty-state-card">
				<div class="empty-icon">
					<Rocket size={36} />
				</div>
				<h3 class="empty-title">No deployments yet</h3>
				<p class="empty-subtitle">
					Choose a deployment target above to get started
				</p>
			</div>
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
		gap: 32px;
	}

	/* Section */
	.section {
		display: flex;
		flex-direction: column;
		gap: 16px;
	}

	.section-title {
		font-size: 14px;
		font-weight: 600;
		color: var(--color-text-primary);
		margin: 0;
	}

	/* Buttons */
	.btn-secondary {
		display: flex;
		align-items: center;
		gap: 6px;
		padding: 8px 16px;
		background: transparent;
		border: 1px solid var(--color-border);
		border-radius: 8px;
		color: var(--color-text-primary);
		font-size: 13px;
		font-weight: 500;
		cursor: pointer;
		transition: border-color 0.15s;
	}

	.btn-secondary:hover {
		border-color: var(--color-accent);
	}

	/* Targets Grid */
	.targets-grid {
		display: grid;
		grid-template-columns: repeat(3, 1fr);
		gap: 16px;
	}

	@media (max-width: 1024px) {
		.targets-grid {
			grid-template-columns: 1fr;
		}
	}

	.target-card {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 16px;
		padding: 28px 20px;
		background: var(--color-bg-elevated);
		border: 1px solid var(--color-border);
		border-radius: 12px;
		text-align: center;
		transition: border-color 0.15s;
	}

	.target-card:not(.disabled):hover {
		border-color: oklch(from var(--color-accent) l c h / 40%);
	}

	.target-card.disabled {
		opacity: 0.6;
	}

	.target-icon {
		display: flex;
		align-items: center;
		justify-content: center;
		width: 56px;
		height: 56px;
		border-radius: 14px;
		background: oklch(from var(--color-accent) l c h / 10%);
		color: var(--color-accent);
	}

	.target-info {
		display: flex;
		flex-direction: column;
		gap: 6px;
	}

	.target-name {
		font-size: 15px;
		font-weight: 600;
		color: var(--color-text-primary);
		margin: 0;
	}

	.target-description {
		font-size: 12px;
		color: var(--color-text-secondary);
		margin: 0;
		line-height: 1.5;
	}

	.target-action {
		margin-top: 4px;
	}

	.coming-soon-badge {
		display: inline-flex;
		align-items: center;
		gap: 5px;
		padding: 6px 12px;
		border-radius: 6px;
		font-size: 11px;
		font-weight: 500;
		background: oklch(from var(--color-text-secondary) l c h / 10%);
		color: var(--color-text-secondary);
	}

	/* Empty State */
	.empty-state-card {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		padding: 40px 24px;
		background: var(--color-bg-elevated);
		border: 1px solid var(--color-border);
		border-radius: 12px;
		text-align: center;
		gap: 12px;
	}

	.empty-icon {
		display: flex;
		align-items: center;
		justify-content: center;
		width: 64px;
		height: 64px;
		border-radius: 14px;
		background: oklch(from var(--color-text-secondary) l c h / 8%);
		color: var(--color-text-secondary);
	}

	.empty-title {
		font-size: 15px;
		font-weight: 600;
		color: var(--color-text-primary);
		margin: 0;
	}

	.empty-subtitle {
		font-size: 13px;
		color: var(--color-text-secondary);
		margin: 0;
		max-width: 360px;
		line-height: 1.5;
	}
</style>
