<script lang="ts">
	import { onMount } from 'svelte';
	import { getHealth } from '$lib/api';

	let health: { status: string; version: string } | null = $state(null);
	let error: string | null = $state(null);

	const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:3000';
	const apiKey = import.meta.env.VITE_API_KEY || 'ap_dev_default';

	onMount(async () => {
		try {
			health = await getHealth();
		} catch (e) {
			error = e instanceof Error ? e.message : 'Cannot connect to collector';
		}
	});
</script>

<svelte:head>
	<title>Settings - AgentPulse</title>
</svelte:head>

<div class="page-header">
	<h1>Settings</h1>
</div>

<div class="settings-grid">
	<div class="card">
		<h3>Collector Connection</h3>
		<div class="field">
			<span class="field-label">Endpoint</span>
			<code>{apiUrl}</code>
		</div>
		<div class="field">
			<span class="field-label">API Key</span>
			<code>{apiKey.slice(0, 8)}{'*'.repeat(apiKey.length - 8)}</code>
		</div>
		<div class="field">
			<span class="field-label">Status</span>
			{#if health}
				<span class="badge badge-success">Connected (v{health.version})</span>
			{:else if error}
				<span class="badge badge-error">Disconnected</span>
			{:else}
				<span style="color: var(--text-muted);">Checking...</span>
			{/if}
		</div>
	</div>

	<div class="card">
		<h3>Quick Start</h3>
		<p class="muted">Install the Python SDK and start tracing:</p>
		<pre class="code-block">pip install agentpulse</pre>
		<pre class="code-block">from agentpulse import AgentPulse, trace

ap = AgentPulse(
    endpoint="{apiUrl}",
    api_key="{apiKey}"
)
ap.patch_openai()

@trace(name="my-agent")
async def my_agent(prompt):
    response = await openai.chat.completions.create(
        model="gpt-4o",
        messages=[{"{"}role": "user", "content": prompt{"}"}]
    )
    return response.choices[0].message.content</pre>
	</div>
</div>

<style>
	.settings-grid {
		display: flex;
		flex-direction: column;
		gap: 1.5rem;
	}

	.card h3 {
		margin-bottom: 1rem;
		font-size: 1rem;
	}

	.field {
		display: flex;
		align-items: center;
		gap: 1rem;
		margin-bottom: 0.75rem;
	}

	.field .field-label {
		font-size: 0.85rem;
		color: var(--text-muted);
		min-width: 5rem;
	}

	code {
		font-family: var(--font-mono);
		font-size: 0.8rem;
		background: var(--bg);
		padding: 0.25rem 0.5rem;
		border-radius: 4px;
	}

	.muted {
		color: var(--text-muted);
		font-size: 0.875rem;
		margin-bottom: 0.75rem;
	}

	.code-block {
		font-family: var(--font-mono);
		font-size: 0.8rem;
		background: var(--bg);
		padding: 1rem;
		border-radius: 6px;
		overflow-x: auto;
		margin-bottom: 0.75rem;
		white-space: pre;
		line-height: 1.5;
	}
</style>
