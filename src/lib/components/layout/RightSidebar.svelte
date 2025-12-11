<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import { writable } from 'svelte/store';
	import { slide } from 'svelte/transition';
	import Tooltip from '../common/Tooltip.svelte';
	import Spinner from '../common/Spinner.svelte';
	import { getUsageStats, type UsageStatsResponse } from '$lib/apis/usage';

	// Props
	export let show = false;

	// Usage data store
	const usageData = writable<UsageStatsResponse | null>(null);
	const isLoading = writable(true);
	const error = writable<string | null>(null);

	let updateInterval: ReturnType<typeof setInterval> | undefined;

	// Format numbers
	const formatNumber = (num: number): string => {
		if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
		if (num >= 1000) return `${(num / 1000).toFixed(1)}K`;
		return num.toString();
	};

	const formatCurrency = (amount: number): string => {
		return `$${amount.toFixed(amount < 1 ? 6 : 2)}`;
	};

	// Progress bar color based on percentage
	const getProgressColor = (percent: number, isBudget: boolean = false): string => {
		if (percent >= 95) return isBudget ? 'bg-red-600' : 'bg-red-500';
		if (percent >= 80) return isBudget ? 'bg-orange-500' : 'bg-yellow-500';
		if (percent >= 60) return 'bg-blue-500';
		return 'bg-green-500';
	};

	// Fetch usage stats from API
	const fetchUsageStats = async () => {
		const token = localStorage.token;
		if (!token) {
			console.log('No token found in localStorage');
			error.set('Please log in to view usage statistics');
			isLoading.set(false);
			return;
		}

		try {
			isLoading.set(true);
			error.set(null);

			console.log('Fetching usage stats with token:', token.substring(0, 10) + '...');
			const stats = await getUsageStats(token);
			console.log('Usage stats received:', stats);

			if (stats) {
				usageData.set(stats);
			} else {
				error.set('Failed to fetch usage statistics');
			}
		} catch (err) {
			console.error('Error fetching usage stats:', err);
			error.set(`Failed to load usage data: ${err?.detail || 'Unknown error'}`);
		} finally {
			isLoading.set(false);
		}
	};

	onMount(() => {
		// Initial fetch
		fetchUsageStats();

		// Poll for updates every 5 seconds
		updateInterval = setInterval(fetchUsageStats, 5000);
	});

	onDestroy(() => {
		if (updateInterval) {
			clearInterval(updateInterval);
		}
	});

	const isWindows = /Windows/i.test(navigator.userAgent);
</script>

{#if show}
	<div
		class="h-screen max-h-[100dvh] min-h-screen select-none bg-gray-50 dark:bg-gray-950 shrink-0 text-gray-900 dark:text-gray-200 text-sm fixed top-0 right-0 border-l border-gray-200 dark:border-gray-800 z-40"
		transition:slide={{ duration: 250, axis: 'x' }}
	>
		<div class="my-auto flex flex-col justify-between h-screen max-h-[100dvh] w-[320px] overflow-x-hidden">
			<!-- Header -->
			<div class="px-4 pt-3 pb-2 flex justify-between items-center sticky top-0 bg-gray-50 dark:bg-gray-950 border-b border-gray-200 dark:border-gray-800 z-10">
				<div class="font-semibold text-base font-primary">Usage Metrics</div>
				<Tooltip content="Close Metrics Panel" placement="left">
					<button
						class="flex rounded-xl size-8 justify-center items-center hover:bg-gray-100 dark:hover:bg-gray-850 transition {isWindows
							? 'cursor-pointer'
							: 'cursor-[w-resize]'}"
						on:click={() => (show = false)}
						aria-label="Close Metrics Panel"
					>
						<svg
							xmlns="http://www.w3.org/2000/svg"
							fill="none"
							viewBox="0 0 24 24"
							stroke-width="2"
							stroke="currentColor"
							class="size-5"
						>
							<path
								stroke-linecap="round"
								stroke-linejoin="round"
								d="M13.5 4.5 21 12m0 0-7.5 7.5M21 12H3"
							/>
						</svg>
					</button>
				</Tooltip>
			</div>

			<!-- Content -->
			<div class="flex-1 overflow-y-auto scrollbar-hidden px-4 py-4 space-y-4">
				{#if $isLoading && !$usageData}
					<div class="flex items-center justify-center py-8">
						<Spinner className="size-8" />
					</div>
				{:else if $error}
					<div class="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl p-4">
						<div class="flex items-start gap-2">
							<span class="text-lg">⚠️</span>
							<div class="flex-1">
								<h4 class="font-semibold text-sm text-red-800 dark:text-red-200 mb-1">Error</h4>
								<p class="text-xs text-red-700 dark:text-red-300">{$error}</p>
							</div>
						</div>
					</div>
				{:else if $usageData}
					<!-- Token Usage Section -->
					<div class="bg-white dark:bg-gray-900 rounded-xl p-4 border border-gray-200 dark:border-gray-800 shadow-sm">
						<div class="flex items-center gap-2 mb-3">
							<div class="text-xl">🪙</div>
							<h3 class="font-semibold text-sm font-primary">Token Usage (Today)</h3>
						</div>

						<div class="space-y-3">
							<!-- Total Tokens -->
							<div>
								<div class="flex justify-between items-center mb-1.5">
									<span class="text-xs text-gray-600 dark:text-gray-400">Total Tokens</span>
									<span class="text-sm font-semibold font-mono">
										{formatNumber($usageData.daily.tokens_total)}
									</span>
								</div>
							</div>

							<!-- Input/Output Breakdown -->
							<div class="grid grid-cols-2 gap-3">
								<div class="bg-gray-50 dark:bg-gray-850 rounded-lg p-2.5">
									<div class="flex items-center gap-1.5 mb-1">
										<span class="text-base">🔽</span>
										<span class="text-xs text-gray-600 dark:text-gray-400">Input</span>
									</div>
									<div class="text-lg font-semibold font-mono">{formatNumber($usageData.daily.tokens_input)}</div>
								</div>
								<div class="bg-gray-50 dark:bg-gray-850 rounded-lg p-2.5">
									<div class="flex items-center gap-1.5 mb-1">
										<span class="text-base">🔼</span>
										<span class="text-xs text-gray-600 dark:text-gray-400">Output</span>
									</div>
									<div class="text-lg font-semibold font-mono">{formatNumber($usageData.daily.tokens_output)}</div>
								</div>
							</div>
						</div>
					</div>

					<!-- Cost Section -->
					<div class="bg-white dark:bg-gray-900 rounded-xl p-4 border border-gray-200 dark:border-gray-800 shadow-sm">
						<div class="flex items-center gap-2 mb-3">
							<div class="text-xl">💰</div>
							<h3 class="font-semibold text-sm font-primary">Cost Tracking</h3>
						</div>

						<div class="space-y-2.5">
							<div class="flex justify-between items-center">
								<span class="text-xs text-gray-600 dark:text-gray-400">Current Session</span>
								<span class="text-sm font-semibold font-mono"
									>{formatCurrency($usageData.session.cost)}</span
								>
							</div>
							<div class="flex justify-between items-center">
								<span class="text-xs text-gray-600 dark:text-gray-400">Today</span>
								<span class="text-sm font-semibold font-mono">{formatCurrency($usageData.daily.cost)}</span>
							</div>
							<div class="flex justify-between items-center">
								<span class="text-xs text-gray-600 dark:text-gray-400">This Month</span>
								<span class="text-sm font-semibold font-mono">{formatCurrency($usageData.monthly.cost)}</span>
							</div>
						</div>
					</div>

					<!-- Daily Budget Section -->
					<div class="bg-white dark:bg-gray-900 rounded-xl p-4 border border-gray-200 dark:border-gray-800 shadow-sm">
						<div class="flex items-center gap-2 mb-3">
							<div class="text-xl">🏦</div>
							<h3 class="font-semibold text-sm font-primary">Daily Budget</h3>
						</div>

						<div class="space-y-2">
							<div class="flex justify-between items-center">
								<span class="text-xs text-gray-600 dark:text-gray-400">Used</span>
								<span class="text-sm font-semibold font-mono">
									{formatCurrency($usageData.daily.cost)}/{formatCurrency($usageData.budget_daily)}
								</span>
							</div>
							<div class="w-full bg-gray-200 dark:bg-gray-800 rounded-full h-3 overflow-hidden">
								<div
									class="h-full rounded-full transition-all duration-300 {getProgressColor(
										($usageData.daily.cost / $usageData.budget_daily) * 100,
										true
									)}"
									style="width: {Math.min(($usageData.daily.cost / $usageData.budget_daily) * 100, 100)}%"
								/>
							</div>
							<div class="flex justify-between items-center">
								<span class="text-xs text-gray-500 dark:text-gray-500">
									{(($usageData.daily.cost / $usageData.budget_daily) * 100).toFixed(1)}% of daily budget
								</span>
								{#if ($usageData.daily.cost / $usageData.budget_daily) * 100 >= 95}
									<span class="text-xs text-red-600 dark:text-red-400 font-medium">⚠️ Limit</span>
								{:else if ($usageData.daily.cost / $usageData.budget_daily) * 100 >= 80}
									<span class="text-xs text-orange-600 dark:text-orange-400 font-medium">⚠️ High</span>
								{/if}
							</div>
						</div>
					</div>

					<!-- Monthly Budget Section -->
					<div class="bg-white dark:bg-gray-900 rounded-xl p-4 border border-gray-200 dark:border-gray-800 shadow-sm">
						<div class="flex items-center gap-2 mb-3">
							<div class="text-xl">🗓️</div>
							<h3 class="font-semibold text-sm font-primary">Monthly Budget</h3>
						</div>

						<div class="space-y-2">
							<div class="flex justify-between items-center">
								<span class="text-xs text-gray-600 dark:text-gray-400">Remaining</span>
								<span class="text-lg font-bold font-mono text-green-600 dark:text-green-400">
									{formatCurrency($usageData.monthly.remaining)}
								</span>
							</div>
							<div class="flex justify-between items-center text-xs">
								<span class="text-gray-600 dark:text-gray-400">
									Used: {formatCurrency($usageData.monthly.cost)}
								</span>
								<span class="text-gray-600 dark:text-gray-400">
									Total: {formatCurrency($usageData.monthly.budget)}
								</span>
							</div>
							<div class="w-full bg-gray-200 dark:bg-gray-800 rounded-full h-3 overflow-hidden">
								<div
									class="h-full rounded-full transition-all duration-300 {getProgressColor(
										$usageData.monthly.percent_used,
										true
									)}"
									style="width: {Math.min($usageData.monthly.percent_used, 100)}%"
								/>
							</div>
							<div class="text-center">
								<span class="text-xs text-gray-500 dark:text-gray-500">
									{$usageData.monthly.percent_used.toFixed(1)}% used this month
								</span>
							</div>
						</div>
					</div>

					<!-- Session Tokens Section -->
					<div class="bg-white dark:bg-gray-900 rounded-xl p-4 border border-gray-200 dark:border-gray-800 shadow-sm">
						<div class="flex items-center gap-2 mb-3">
							<div class="text-xl">📊</div>
							<h3 class="font-semibold text-sm font-primary">Current Session</h3>
						</div>

						<div class="space-y-2.5">
							<div class="flex justify-between items-center">
								<span class="text-xs text-gray-600 dark:text-gray-400">Session Tokens</span>
								<span class="text-sm font-semibold font-mono">{formatNumber($usageData.session.tokens_total)}</span>
							</div>
							<div class="grid grid-cols-2 gap-2 text-xs">
								<div class="flex justify-between">
									<span class="text-gray-600 dark:text-gray-400">Input:</span>
									<span class="font-mono">{formatNumber($usageData.session.tokens_input)}</span>
								</div>
								<div class="flex justify-between">
									<span class="text-gray-600 dark:text-gray-400">Output:</span>
									<span class="font-mono">{formatNumber($usageData.session.tokens_output)}</span>
								</div>
							</div>
						</div>
					</div>

					<!-- Status Indicator -->
					<div class="bg-gray-100 dark:bg-gray-850 rounded-xl p-3 border border-gray-200 dark:border-gray-800">
						<div class="flex items-center justify-between">
							<div class="flex items-center gap-2">
								<div
									class="size-2 rounded-full {$usageData.daily.tokens_total > 0
										? 'bg-green-500'
										: 'bg-gray-400'}"
								/>
								<span class="text-xs font-medium text-gray-700 dark:text-gray-300">
									{$usageData.daily.tokens_total > 0 ? 'Active' : 'Ready'}
								</span>
							</div>
							<span class="text-xs text-gray-500 dark:text-gray-500">Live Metrics</span>
						</div>
					</div>
				{/if}
			</div>
		</div>
	</div>
{/if}

<style>
	/* Custom scrollbar for right sidebar */
	.scrollbar-hidden::-webkit-scrollbar {
		display: none;
	}
	.scrollbar-hidden {
		-ms-overflow-style: none;
		scrollbar-width: none;
	}
</style>
