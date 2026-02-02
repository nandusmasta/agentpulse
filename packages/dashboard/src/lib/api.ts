// Use relative URLs - they'll be proxied through /api/ to the collector
const API_BASE = '/api';
const API_KEY = 'ap_dev_default';

async function request<T>(path: string, init?: RequestInit): Promise<T> {
	const res = await fetch(`${API_BASE}${path}`, {
		...init,
		headers: {
			'Content-Type': 'application/json',
			'X-AgentPulse-Key': API_KEY,
			...init?.headers
		}
	});
	if (!res.ok) {
		throw new Error(`API error: ${res.status} ${res.statusText}`);
	}
	return res.json();
}

export interface Trace {
	id: string;
	project_id: string;
	agent_name: string | null;
	status: 'running' | 'success' | 'error';
	started_at: number;
	ended_at: number | null;
	total_tokens_in: number;
	total_tokens_out: number;
	total_cost_usd: number;
	metadata: string | null;
	error: string | null;
}

export interface Span {
	id: string;
	trace_id: string;
	parent_span_id: string | null;
	name: string;
	kind: 'llm' | 'tool' | 'custom';
	started_at: number;
	ended_at: number | null;
	input: string | null;
	output: string | null;
	model: string | null;
	tokens_in: number | null;
	tokens_out: number | null;
	cost_usd: number | null;
	error: string | null;
}

export interface TraceWithSpans extends Trace {
	spans: Span[];
}

export interface TraceListResponse {
	data: Trace[];
	pagination: {
		total: number;
		limit: number;
		offset: number;
	};
}

export interface StatsResponse {
	total_traces: number;
	total_cost_usd: number;
	total_tokens: number;
	daily_costs: Array<{ date: string; cost: number }>;
	top_agents: Array<{
		agent_name: string;
		trace_count: number;
		total_cost: number;
		avg_duration: number | null;
	}>;
}

export interface HealthResponse {
	status: string;
	service: string;
	version: string;
	timestamp: string;
}

export async function getTraces(params?: {
	limit?: number;
	offset?: number;
	status?: string;
	agent?: string;
}): Promise<TraceListResponse> {
	const searchParams = new URLSearchParams();
	if (params?.limit) searchParams.set('limit', String(params.limit));
	if (params?.offset) searchParams.set('offset', String(params.offset));
	if (params?.status) searchParams.set('status', params.status);
	if (params?.agent) searchParams.set('agent', params.agent);
	const query = searchParams.toString();
	return request(`/traces${query ? `?${query}` : ''}`);
}

export async function getTrace(id: string): Promise<TraceWithSpans> {
	return request(`/traces/${id}`);
}

export async function getStats(): Promise<StatsResponse> {
	return request('/stats');
}

export async function getHealth(): Promise<HealthResponse> {
	return request('/health');
}
