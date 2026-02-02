<script lang="ts">
	import { onMount } from 'svelte';
	import { page } from '$app/state';
	import { getTraces, type Trace, type TraceListResponse } from '$lib/api';
	import { formatCost, formatTokens, formatDuration, timeAgo } from '$lib/format';

	let response: TraceListResponse | null = $state(null);
	let error: string | null = $state(null);
	let statusFilter: string = $state('');
	let currentPage: number = $state(0);
	const pageSize = 25;

	async function load() {
		try {
			const agentFilter = page.url.searchParams.get('agent') || undefined;
			response = await getTraces({
				limit: pageSize,
				offset: currentPage * pageSize,
				status: statusFilter || undefined,
				agent: agentFilter
			});
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to load traces';
		}
	}

	onMount(load);

	function nextPage() {
		currentPage++;
		load();
	}

	function prevPage() {
		if (currentPage > 0) {
			currentPage--;
			load();
		}
	}

	function filterStatus(status: string) {
		statusFilter = status;
		currentPage = 0;
		load();
	}
</script>

<svelte:head>
	<title>Traces - AgentPulse</title>
</svelte:head>

<div class="page-header">
	<h1>Traces</h1>
	<div class="filters">
		<button class:active={statusFilter === ''} class="secondary" onclick={() => filterStatus('')}
			>All</button
		>
		<button
			class:active={statusFilter === 'success'}
			class="secondary"
			onclick={() => filterStatus('success')}>Success</button
		>
		<button
			class:active={statusFilter === 'error'}
			class="secondary"
			onclick={() => filterStatus('error')}>Errors</button
		>
		<button
			class:active={statusFilter === 'running'}
			class="secondary"
			onclick={() => filterStatus('running')}>Running</button
		>
	</div>
</div>

{#if error}
	<div class="card" style="border-color: var(--error); color: var(--error);">
		{error}
	</div>
{:else if !response}
	<p style="color: var(--text-muted);">Loading...</p>
{:else}
	<div class="card">
		<table>
			<thead>
				<tr>
					<th>ID</th>
					<th>Agent</th>
					<th>Status</th>
					<th>Duration</th>
					<th>Tokens (in/out)</th>
					<th>Cost</th>
					<th>Started</th>
				</tr>
			</thead>
			<tbody>
				{#each response.data as trace}
					<tr>
						<td class="mono">
							<a href="/traces/{trace.id}">{trace.id.slice(0, 8)}</a>
						</td>
						<td>{trace.agent_name || '-'}</td>
						<td>
							<span class="badge badge-{trace.status}">{trace.status}</span>
						</td>
						<td>
							{trace.ended_at
								? formatDuration(trace.ended_at - trace.started_at)
								: 'running'}
						</td>
						<td class="mono">
							{formatTokens(trace.total_tokens_in)} / {formatTokens(trace.total_tokens_out)}
						</td>
						<td class="mono">{formatCost(trace.total_cost_usd)}</td>
						<td style="color: var(--text-muted);">{timeAgo(trace.started_at)}</td>
					</tr>
				{/each}
			</tbody>
		</table>
	</div>

	<div class="pagination">
		<button class="secondary" onclick={prevPage} disabled={currentPage === 0}>Prev</button>
		<span class="page-info">
			{response.offset + 1}-{Math.min(response.offset + response.limit, response.total)} of {response.total}
		</span>
		<button
			class="secondary"
			onclick={nextPage}
			disabled={response.offset + response.limit >= response.total}>Next</button
		>
	</div>
{/if}

<style>
	.filters {
		display: flex;
		gap: 0.5rem;
	}

	.filters button {
		font-size: 0.8rem;
		padding: 0.35rem 0.75rem;
	}

	.filters button.active {
		background: var(--accent);
		color: white;
		border-color: var(--accent);
	}

	.pagination {
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 1rem;
		margin-top: 1rem;
	}

	.page-info {
		font-size: 0.85rem;
		color: var(--text-muted);
	}
</style>
