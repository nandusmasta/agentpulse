<script lang="ts">
	import '../app.css';

	let { children } = $props();
</script>

<div class="app">
	<nav class="navbar">
		<div class="nav-inner">
			<a href="/" class="logo">
				<span class="logo-icon">&#9678;</span>
				AgentPulse
			</a>
			<div class="nav-links">
				<a href="/">Overview</a>
				<a href="/traces">Traces</a>
				<a href="/settings">Settings</a>
			</div>
		</div>
	</nav>
	<main class="container">
		{@render children()}
	</main>
</div>

<style>
	.navbar {
		background: var(--bg-card);
		border-bottom: 1px solid var(--border);
		padding: 0 1.5rem;
		position: sticky;
		top: 0;
		z-index: 100;
	}

	.nav-inner {
		max-width: 1200px;
		margin: 0 auto;
		display: flex;
		align-items: center;
		justify-content: space-between;
		height: 3.5rem;
	}

	.logo {
		font-size: 1.1rem;
		font-weight: 700;
		color: var(--text);
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}

	.logo-icon {
		color: var(--accent);
		font-size: 1.3rem;
	}

	.nav-links {
		display: flex;
		gap: 1.5rem;
	}

	.nav-links a {
		color: var(--text-muted);
		font-size: 0.875rem;
		font-weight: 500;
		transition: color 0.15s;
	}

	.nav-links a:hover {
		color: var(--text);
	}

	main {
		padding-top: 2rem;
		padding-bottom: 3rem;
	}
</style>
