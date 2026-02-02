<script lang="ts">
	import { onMount } from 'svelte';
	import { page } from '$app/state';
	import { getTrace, type TraceWithSpans, type Span } from '$lib/api';
	import { formatCost, formatTokens, formatDuration, formatTimestamp } from '$lib/format';

	let trace: TraceWithSpans | null = $state(null);
	let error: string | null = $state(null);
	let expandedSpans: Set<string> = $state(new Set());

	onMount(async () => {
		try {
			trace = await getTrace(page.params.id);
			// Expand all by default
			if (trace.spans) {
				expandedSpans = new Set(trace.spans.map((s) => s.id));
			}
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to load trace';
		}
	});

	function toggleSpan(id: string) {
		const next = new Set(expandedSpans);
		if (next.has(id)) next.delete(id);
		else next.add(id);
		expandedSpans = next;
	}

	function buildTree(spans: Span[]): Map<string | null, Span[]> {
		const tree = new Map<string | null, Span[]>();
		for (const span of spans) {
			const key = span.parent_span_id;
			if (!tree.has(key)) tree.set(key, []);
			tree.get(key)!.push(span);
		}
		return tree;
	}

	function getSpanWidth(span: Span): number {
		if (!trace || !span.ended_at) return 0;
		const traceDuration =
			(trace.ended_at || trace.started_at + 1) - trace.started_at;
		if (traceDuration === 0) return 100;
		return ((span.ended_at - span.started_at) / traceDuration) * 100;
	}

	function getSpanOffset(span: Span): number {
		if (!trace) return 0;
		const traceDuration =
			(trace.ended_at || trace.started_at + 1) - trace.started_at;
		if (traceDuration === 0) return 0;
		return ((span.started_at - trace.started_at) / traceDuration) * 100;
	}

	function tryParseJson(s: string | null): string {
		if (!s) return '';
		try {
			return JSON.stringify(JSON.parse(s), null, 2);
		} catch {
			return s;
		}
	}
</script>

<svelte:head>
	<title>Trace {page.params.id.slice(0, 8)} - AgentPulse</title>
</svelte:head>

{#if error}
	<div class="card" style="border-color: var(--error); color: var(--error);">
		{error}
	</div>
{:else if !trace}
	<p style="color: var(--text-muted);">Loading...</p>
{:else}
	<div class="page-header">
		<div>
			<h1>{trace.agent_name || 'Trace'}</h1>
			<span class="trace-id mono">{trace.id}</span>
		</div>
		<span class="badge badge-{trace.status}">{trace.status}</span>
	</div>

	<div class="stat-grid" style="margin-bottom: 1.5rem;">
		<div class="stat-card">
			<div class="label">Duration</div>
			<div class="value">
				{trace.ended_at ? formatDuration(trace.ended_at - trace.started_at) : 'running'}
			</div>
		</div>
		<div class="stat-card">
			<div class="label">Total Cost</div>
			<div class="value">{formatCost(trace.total_cost_usd)}</div>
		</div>
		<div class="stat-card">
			<div class="label">Tokens In</div>
			<div class="value">{formatTokens(trace.total_tokens_in)}</div>
		</div>
		<div class="stat-card">
			<div class="label">Tokens Out</div>
			<div class="value">{formatTokens(trace.total_tokens_out)}</div>
		</div>
	</div>

	{#if trace.error}
		<div class="card error-card">
			<strong>Error:</strong>
			<pre>{trace.error}</pre>
		</div>
	{/if}

	<h2 class="section-title">
		Spans ({trace.spans.length})
	</h2>

	{@const tree = buildTree(trace.spans)}

	<div class="spans-container card">
		{#snippet renderSpans(parentId: string | null, depth: number)}
			{#each tree.get(parentId) || [] as span}
				<div class="span-row" style="padding-left: {depth * 1.5}rem;">
					<button class="span-toggle" onclick={() => toggleSpan(span.id)}>
						{expandedSpans.has(span.id) ? '▾' : '▸'}
					</button>
					<span class="badge badge-{span.kind}">{span.kind}</span>
					<span class="span-name">{span.name}</span>
					{#if span.model}
						<span class="span-model mono">{span.model}</span>
					{/if}
					<div class="span-timeline">
						<div
							class="span-bar span-bar-{span.kind}"
							style="left: {getSpanOffset(span)}%; width: {Math.max(getSpanWidth(span), 0.5)}%;"
						></div>
					</div>
					<span class="span-duration">
						{span.ended_at ? formatDuration(span.ended_at - span.started_at) : '...'}
					</span>
					{#if span.cost_usd}
						<span class="span-cost mono">{formatCost(span.cost_usd)}</span>
					{/if}
				</div>

				{#if expandedSpans.has(span.id)}
					<div class="span-detail" style="margin-left: {depth * 1.5 + 1.5}rem;">
						{#if span.tokens_in || span.tokens_out}
							<div class="detail-row">
								<span class="detail-label">Tokens:</span>
								{formatTokens(span.tokens_in || 0)} in / {formatTokens(span.tokens_out || 0)} out
							</div>
						{/if}
						{#if span.input}
							<div class="detail-row">
								<span class="detail-label">Input:</span>
								<pre class="detail-pre">{tryParseJson(span.input)}</pre>
							</div>
						{/if}
						{#if span.output}
							<div class="detail-row">
								<span class="detail-label">Output:</span>
								<pre class="detail-pre">{tryParseJson(span.output)}</pre>
							</div>
						{/if}
						{#if span.error}
							<div class="detail-row" style="color: var(--error);">
								<span class="detail-label">Error:</span>
								<pre class="detail-pre">{span.error}</pre>
							</div>
						{/if}
					</div>

					{#if tree.has(span.id)}
						{@render renderSpans(span.id, depth + 1)}
					{/if}
				{/if}
			{/each}
		{/snippet}

		{@render renderSpans(null, 0)}

		{#if trace.spans.length === 0}
			<p style="color: var(--text-muted); text-align: center; padding: 2rem;">
				No spans recorded for this trace.
			</p>
		{/if}
	</div>

	<div class="meta-section">
		<div class="detail-row">
			<span class="detail-label">Started:</span>
			{formatTimestamp(trace.started_at)}
		</div>
		{#if trace.ended_at}
			<div class="detail-row">
				<span class="detail-label">Ended:</span>
				{formatTimestamp(trace.ended_at)}
			</div>
		{/if}
	</div>
{/if}

<style>
	.trace-id {
		font-size: 0.8rem;
		color: var(--text-muted);
	}

	.section-title {
		font-size: 1.1rem;
		font-weight: 600;
		margin-bottom: 0.75rem;
	}

	.error-card {
		border-color: var(--error);
		margin-bottom: 1.5rem;
	}

	.error-card pre {
		margin-top: 0.5rem;
		font-family: var(--font-mono);
		font-size: 0.8rem;
		white-space: pre-wrap;
		color: var(--error);
	}

	.spans-container {
		padding: 0.5rem;
	}

	.span-row {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		padding: 0.5rem 0.5rem;
		border-bottom: 1px solid var(--border);
		font-size: 0.875rem;
	}

	.span-row:hover {
		background: var(--bg-hover);
	}

	.span-toggle {
		background: none;
		border: none;
		color: var(--text-muted);
		cursor: pointer;
		padding: 0;
		font-size: 0.75rem;
		width: 1rem;
	}

	.span-name {
		font-weight: 500;
		white-space: nowrap;
	}

	.span-model {
		color: var(--text-muted);
		font-size: 0.75rem;
	}

	.span-timeline {
		flex: 1;
		height: 6px;
		background: var(--border);
		border-radius: 3px;
		position: relative;
		min-width: 80px;
	}

	.span-bar {
		position: absolute;
		height: 100%;
		border-radius: 3px;
		min-width: 2px;
	}

	.span-bar-llm {
		background: var(--accent);
	}

	.span-bar-tool {
		background: var(--warning);
	}

	.span-bar-custom {
		background: var(--text-muted);
	}

	.span-duration {
		font-size: 0.8rem;
		color: var(--text-muted);
		white-space: nowrap;
		min-width: 4rem;
		text-align: right;
	}

	.span-cost {
		font-size: 0.8rem;
		white-space: nowrap;
		min-width: 4rem;
		text-align: right;
	}

	.span-detail {
		padding: 0.5rem;
		margin-bottom: 0.25rem;
		font-size: 0.8rem;
		border-left: 2px solid var(--border);
	}

	.detail-row {
		margin-bottom: 0.35rem;
	}

	.detail-label {
		color: var(--text-muted);
		font-weight: 500;
	}

	.detail-pre {
		font-family: var(--font-mono);
		font-size: 0.75rem;
		background: var(--bg);
		padding: 0.5rem;
		border-radius: 4px;
		margin-top: 0.25rem;
		overflow-x: auto;
		max-height: 200px;
		overflow-y: auto;
		white-space: pre-wrap;
		word-break: break-all;
	}

	.meta-section {
		margin-top: 1.5rem;
		font-size: 0.85rem;
	}
</style>
