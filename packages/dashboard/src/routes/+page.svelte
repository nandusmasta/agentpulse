<script lang="ts">
	import { onMount } from 'svelte';
	import { getStats, getTraces, type StatsResponse, type Trace } from '$lib/api';
	import { formatCost, formatTokens, formatDuration, timeAgo } from '$lib/format';

	let stats: StatsResponse | null = $state(null);
	let recentTraces: Trace[] = $state([]);
	let error: string | null = $state(null);

	onMount(async () => {
		try {
			const [s, t] = await Promise.all([getStats(), getTraces({ limit: 10 })]);
			stats = s;
			recentTraces = t.data;
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to load data';
		}
	});
</script>

<svelte:head>
	<title>AgentPulse - Overview</title>
</svelte:head>

<div class="page-header">
	<h1>Overview</h1>
</div>

{#if error}
	<div class="card" style="border-color: var(--error); color: var(--error);">
		{error}
	</div>
{:else if !stats}
	<p style="color: var(--text-muted);">Loading...</p>
{:else}
	<div class="stat-grid">
		<div class="stat-card">
			<div class="label">Total Traces</div>
			<div class="value">{stats.totals.total_traces}</div>
		</div>
		<div class="stat-card">
			<div class="label">Total Cost</div>
			<div class="value">{formatCost(stats.totals.total_cost_usd || 0)}</div>
		</div>
		<div class="stat-card">
			<div class="label">Tokens Used</div>
			<div class="value">
				{formatTokens((stats.totals.total_tokens_in || 0) + (stats.totals.total_tokens_out || 0))}
			</div>
		</div>
		<div class="stat-card">
			<div class="label">Avg Duration</div>
			<div class="value">
				{stats.totals.avg_duration_s ? formatDuration(stats.totals.avg_duration_s) : '-'}
			</div>
		</div>
		<div class="stat-card">
			<div class="label">Success Rate</div>
			<div class="value">
				{#if stats.totals.total_traces > 0}
					{Math.round(
						((stats.totals.success_count || 0) / stats.totals.total_traces) * 100
					)}%
				{:else}
					-
				{/if}
			</div>
		</div>
		<div class="stat-card">
			<div class="label">Errors</div>
			<div class="value" style="color: {(stats.totals.error_count || 0) > 0 ? 'var(--error)' : 'inherit'}">
				{stats.totals.error_count || 0}
			</div>
		</div>
	</div>

	{#if stats.top_agents.length > 0}
		<h2 class="section-title">Top Agents by Cost</h2>
		<div class="card">
			<table>
				<thead>
					<tr>
						<th>Agent</th>
						<th>Traces</th>
						<th>Total Cost</th>
						<th>Avg Duration</th>
					</tr>
				</thead>
				<tbody>
					{#each stats.top_agents as agent}
						<tr>
							<td>
								<a href="/traces?agent={agent.agent_name}">{agent.agent_name}</a>
							</td>
							<td>{agent.trace_count}</td>
							<td>{formatCost(agent.total_cost)}</td>
							<td>{agent.avg_duration ? formatDuration(agent.avg_duration) : '-'}</td>
						</tr>
					{/each}
				</tbody>
			</table>
		</div>
	{/if}

	<h2 class="section-title">Recent Traces</h2>
	{#if recentTraces.length === 0}
		<div class="card">
			<p style="color: var(--text-muted); text-align: center; padding: 2rem;">
				No traces yet. Instrument your agent with the SDK to get started.
			</p>
		</div>
	{:else}
		<div class="card">
			<table>
				<thead>
					<tr>
						<th>Agent</th>
						<th>Status</th>
						<th>Duration</th>
						<th>Tokens</th>
						<th>Cost</th>
						<th>When</th>
					</tr>
				</thead>
				<tbody>
					{#each recentTraces as trace}
						<tr>
							<td>
								<a href="/traces/{trace.id}">{trace.agent_name || 'unnamed'}</a>
							</td>
							<td>
								<span class="badge badge-{trace.status}">{trace.status}</span>
							</td>
							<td>
								{trace.ended_at
									? formatDuration(trace.ended_at - trace.started_at)
									: 'running'}
							</td>
							<td class="mono">
								{formatTokens(trace.total_tokens_in + trace.total_tokens_out)}
							</td>
							<td class="mono">{formatCost(trace.total_cost_usd)}</td>
							<td style="color: var(--text-muted);">{timeAgo(trace.started_at)}</td>
						</tr>
					{/each}
				</tbody>
			</table>
		</div>
	{/if}
{/if}

<style>
	.section-title {
		font-size: 1.1rem;
		font-weight: 600;
		margin-top: 2rem;
		margin-bottom: 0.75rem;
	}
</style>
