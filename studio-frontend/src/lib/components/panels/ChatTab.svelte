<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import { SendHorizonal, Trash2, Bot, User, Wrench, Loader } from 'lucide-svelte';
	import {
		chatMessages,
		chatStreaming,
		addUserMessage,
		addAssistantMessage,
		appendToken,
		completeMessage,
		addToolCall,
		clearChat
	} from '$lib/stores/chat';

	let inputText = $state('');
	let messagesContainer: HTMLDivElement | undefined = $state(undefined);
	let inputElement: HTMLTextAreaElement | undefined = $state(undefined);
	let ws: WebSocket | null = $state(null);
	let currentAssistantMsgId = $state('');
	let connectionError = $state('');
	let reconnectTimer: ReturnType<typeof setTimeout> | null = null;

	function getWsUrl(): string {
		const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
		return `${protocol}//${window.location.host}/ws/assistant`;
	}

	function connectWs(): void {
		if (ws && ws.readyState === WebSocket.OPEN) return;

		connectionError = '';
		const socket = new WebSocket(getWsUrl());

		socket.onopen = () => {
			connectionError = '';
		};

		socket.onmessage = (event) => {
			const data = JSON.parse(event.data);

			if (data.type === 'token') {
				if (!currentAssistantMsgId) {
					currentAssistantMsgId = addAssistantMessage();
				}
				appendToken(currentAssistantMsgId, data.content);
				scrollToBottom();
			} else if (data.type === 'response_complete') {
				if (currentAssistantMsgId) {
					completeMessage(currentAssistantMsgId, data.full_text);
				}
				currentAssistantMsgId = '';
				scrollToBottom();
			} else if (data.type === 'tool_call') {
				if (currentAssistantMsgId) {
					addToolCall(currentAssistantMsgId, {
						tool: data.tool,
						args: data.args,
						result: data.result
					});
				}
			} else if (data.type === 'error') {
				connectionError = data.message;
				if (currentAssistantMsgId) {
					completeMessage(currentAssistantMsgId, '');
				} else {
					chatStreaming.set(false);
				}
				currentAssistantMsgId = '';
			}
		};

		socket.onclose = () => {
			if (currentAssistantMsgId) {
				completeMessage(currentAssistantMsgId, '[Connection lost]');
				currentAssistantMsgId = '';
			} else {
				chatStreaming.set(false);
			}
			ws = null;
			connectionError = 'Reconnecting...';
			reconnectTimer = setTimeout(connectWs, 3000);
		};

		socket.onerror = () => {
			connectionError = 'Connection lost';
		};

		ws = socket;
	}

	function disconnectWs(): void {
		if (reconnectTimer) {
			clearTimeout(reconnectTimer);
			reconnectTimer = null;
		}
		ws?.close();
		ws = null;
	}

	function sendMessage(): void {
		const text = inputText.trim();
		if (!text || $chatStreaming || !ws) return;

		addUserMessage(text);
		currentAssistantMsgId = addAssistantMessage();
		inputText = '';

		ws.send(JSON.stringify({ action: 'chat', message: text }));
		scrollToBottom();
	}

	function handleKeydown(event: KeyboardEvent): void {
		if (event.key === 'Enter' && !event.shiftKey) {
			event.preventDefault();
			sendMessage();
		}
	}

	function handleClear(): void {
		clearChat();
		if (ws && ws.readyState === WebSocket.OPEN) {
			ws.send(JSON.stringify({ action: 'clear_history' }));
		}
		connectionError = '';
	}

	function scrollToBottom(): void {
		requestAnimationFrame(() => {
			if (messagesContainer) {
				messagesContainer.scrollTop = messagesContainer.scrollHeight;
			}
		});
	}

	function formatTime(isoString: string): string {
		const d = new Date(isoString);
		return d.toLocaleTimeString('en-US', {
			hour: '2-digit',
			minute: '2-digit'
		});
	}

	onMount(() => {
		connectWs();
		inputElement?.focus();
	});

	onDestroy(() => {
		disconnectWs();
	});
</script>

<div class="chat-tab">
	<!-- Messages area -->
	<div class="messages" bind:this={messagesContainer}>
		{#if $chatMessages.length === 0}
			<div class="empty-state">
				<div class="empty-icon-circle">
					<Bot size={48} />
				</div>
				<span class="empty-title">Firefly Assistant</span>
				<span class="empty-hint"
					>Ask me to help build your agent pipeline. I can add nodes, connect them, configure
					settings, and explain framework concepts.</span
				>
			</div>
		{:else}
			{#each $chatMessages as message (message.id)}
				<div
					class="message"
					class:user={message.role === 'user'}
					class:assistant={message.role === 'assistant'}
				>
					<div class="message-avatar">
						{#if message.role === 'user'}
							<User size={14} />
						{:else}
							<Bot size={14} />
						{/if}
					</div>
					<div class="message-body">
						<div class="message-header">
							<span class="message-role"
								>{message.role === 'user' ? 'You' : 'Assistant'}</span
							>
							<span class="message-time">{formatTime(message.timestamp)}</span>
						</div>
						<div class="message-content">
							{message.content}
							{#if message.streaming}
								<span class="streaming-cursor"></span>
							{/if}
						</div>
						{#if message.toolCalls && message.toolCalls.length > 0}
							<div class="tool-calls">
								{#each message.toolCalls as tc}
									<div class="tool-card">
										<div class="tool-card-header">
											<Wrench size={11} />
											<span class="tool-name">{tc.tool}</span>
										</div>
										<div class="tool-card-detail">
											{JSON.stringify(tc.args)}
										</div>
									</div>
								{/each}
							</div>
						{/if}
					</div>
				</div>
			{/each}
		{/if}
	</div>

	<!-- Error banner -->
	{#if connectionError}
		<div class="error-bar">
			<span>{connectionError}</span>
		</div>
	{/if}

	<!-- Input area -->
	<div class="input-area">
		<textarea
			class="chat-input"
			placeholder="Ask the assistant..."
			bind:value={inputText}
			bind:this={inputElement}
			onkeydown={handleKeydown}
			disabled={$chatStreaming}
			rows={1}
		></textarea>
		<div class="input-actions">
			<button
				class="action-btn clear-btn"
				onclick={handleClear}
				title="Clear chat"
				disabled={$chatMessages.length === 0}
			>
				<Trash2 size={14} />
			</button>
			<button
				class="action-btn send-btn"
				onclick={sendMessage}
				disabled={!inputText.trim() || $chatStreaming || !ws}
				title="Send message"
			>
				{#if $chatStreaming}
					<Loader size={14} class="spin-icon" />
				{:else}
					<SendHorizonal size={14} />
				{/if}
			</button>
		</div>
	</div>
</div>

<style>
	.chat-tab {
		display: flex;
		flex-direction: column;
		height: 100%;
		overflow: hidden;
	}

	.messages {
		flex: 1;
		overflow-y: auto;
		padding: 16px;
	}

	.empty-state {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		height: 100%;
		gap: 10px;
		color: var(--color-text-secondary, #8888a0);
		opacity: 0.7;
		padding: 24px;
	}

	.empty-icon-circle {
		width: 72px;
		height: 72px;
		border-radius: 50%;
		background: oklch(from var(--color-accent, #ff6b35) l c h / 10%);
		color: var(--color-accent, #ff6b35);
		display: flex;
		align-items: center;
		justify-content: center;
		margin-bottom: 4px;
	}

	.empty-title {
		font-size: 13px;
		font-weight: 600;
		color: var(--color-text-secondary, #8888a0);
	}

	.empty-hint {
		font-size: 11px;
		color: var(--color-text-secondary, #8888a0);
		text-align: center;
		max-width: 320px;
		line-height: 1.5;
	}

	.message {
		display: flex;
		gap: 10px;
		margin-bottom: 16px;
	}

	.message-avatar {
		width: 24px;
		height: 24px;
		border-radius: 50%;
		display: flex;
		align-items: center;
		justify-content: center;
		flex-shrink: 0;
		margin-top: 2px;
	}

	.message.user .message-avatar {
		background: oklch(from var(--color-accent, #ff6b35) l c h / 15%);
		color: var(--color-accent, #ff6b35);
	}

	.message.assistant .message-avatar {
		background: rgba(255, 255, 255, 0.06);
		color: var(--color-text-secondary, #8888a0);
	}

	.message-body {
		flex: 1;
		min-width: 0;
	}

	.message-header {
		display: flex;
		align-items: baseline;
		gap: 8px;
		margin-bottom: 4px;
	}

	.message-role {
		font-size: 11px;
		font-weight: 600;
		color: var(--color-text-primary, #e8e8ed);
	}

	.message-time {
		font-size: 10px;
		color: var(--color-text-secondary, #8888a0);
		opacity: 0.6;
	}

	.message-content {
		font-size: 12px;
		line-height: 1.6;
		color: var(--color-text-primary, #e8e8ed);
		white-space: pre-wrap;
		word-break: break-word;
	}

	.message.user .message-content {
		background: oklch(from var(--color-accent, #ff6b35) l c h / 10%);
		border-radius: 8px;
		padding: 8px 12px;
	}

	.message.assistant .message-content {
		background: var(--color-bg-elevated, #1a1a26);
		border-radius: 8px;
		padding: 8px 12px;
	}

	.streaming-cursor {
		display: inline-block;
		width: 6px;
		height: 14px;
		background: var(--color-accent, #ff6b35);
		margin-left: 2px;
		animation: blink 0.8s step-end infinite;
		vertical-align: text-bottom;
	}

	@keyframes blink {
		0%,
		100% {
			opacity: 1;
		}
		50% {
			opacity: 0;
		}
	}

	.tool-calls {
		display: flex;
		flex-direction: column;
		gap: 6px;
		margin-top: 8px;
	}

	.tool-card {
		background: rgba(255, 255, 255, 0.03);
		border: 1px solid var(--color-border, #2a2a3a);
		border-radius: 6px;
		padding: 6px 10px;
	}

	.tool-card-header {
		display: flex;
		align-items: center;
		gap: 6px;
		color: var(--color-accent, #ff6b35);
		font-size: 11px;
		font-weight: 600;
		margin-bottom: 4px;
	}

	.tool-name {
		font-size: 11px;
	}

	.tool-card-detail {
		font-family: var(--font-mono, 'JetBrains Mono', ui-monospace, monospace);
		font-size: 10px;
		color: var(--color-text-secondary, #8888a0);
		white-space: pre-wrap;
		word-break: break-all;
		line-height: 1.5;
	}

	.error-bar {
		display: flex;
		align-items: center;
		padding: 6px 12px;
		background: rgba(239, 68, 68, 0.1);
		border-top: 1px solid rgba(239, 68, 68, 0.2);
		font-size: 11px;
		color: var(--color-error, #ef4444);
		flex-shrink: 0;
	}

	.input-area {
		flex-shrink: 0;
		border-top: 1px solid var(--color-border, #2a2a3a);
		padding: 8px 12px;
		display: flex;
		gap: 8px;
		align-items: flex-end;
	}

	.chat-input {
		flex: 1;
		background: transparent;
		border: none;
		outline: none;
		color: var(--color-text-primary, #e8e8ed);
		font-size: 12px;
		font-family: inherit;
		line-height: 1.5;
		resize: none;
		padding: 4px 0;
	}

	.chat-input::placeholder {
		color: var(--color-text-secondary, #8888a0);
		opacity: 0.5;
	}

	.chat-input:disabled {
		opacity: 0.5;
	}

	.input-actions {
		display: flex;
		align-items: center;
		gap: 4px;
		flex-shrink: 0;
	}

	.action-btn {
		display: flex;
		align-items: center;
		justify-content: center;
		width: 28px;
		height: 28px;
		border: none;
		background: transparent;
		border-radius: 4px;
		color: var(--color-text-secondary, #8888a0);
		cursor: pointer;
		transition:
			background 0.15s ease,
			color 0.15s ease;
	}

	.action-btn:hover:not(:disabled) {
		background: rgba(255, 255, 255, 0.05);
		color: var(--color-text-primary, #e8e8ed);
	}

	.action-btn:disabled {
		opacity: 0.3;
		cursor: default;
	}

	.send-btn:not(:disabled) {
		color: var(--color-accent, #ff6b35);
	}

	.send-btn:hover:not(:disabled) {
		background: oklch(from var(--color-accent, #ff6b35) l c h / 12%);
	}

	:global(.spin-icon) {
		animation: chat-spin 1s linear infinite;
	}

	@keyframes chat-spin {
		from {
			transform: rotate(0deg);
		}
		to {
			transform: rotate(360deg);
		}
	}
</style>
