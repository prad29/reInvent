import { WEBUI_API_BASE_URL, WEBUI_DEFAULT_API_BASE_URL } from '$lib/constants';

export interface DailyUsageStats {
	tokens_input: number;
	tokens_output: number;
	tokens_total: number;
	cost: number;
	date: string;
}

export interface MonthlyUsageStats {
	tokens_total: number;
	cost: number;
	budget: number;
	remaining: number;
	percent_used: number;
}

export interface SessionUsageStats {
	tokens_input: number;
	tokens_output: number;
	tokens_total: number;
	cost: number;
}

export interface UsageStatsResponse {
	daily: DailyUsageStats;
	monthly: MonthlyUsageStats;
	session: SessionUsageStats;
	budget_daily: number;
	budget_monthly: number;
}

export interface DailyHistoryItem {
	date: string;
	tokens_input: number;
	tokens_output: number;
	tokens_total: number;
	cost: number;
}

export interface DailyHistoryResponse {
	user_id: string;
	days: number;
	history: DailyHistoryItem[];
}

export interface MonthlyHistoryItem {
	month: string;
	tokens_total: number;
	cost: number;
}

export interface MonthlyHistoryResponse {
	user_id: string;
	months: number;
	history: MonthlyHistoryItem[];
}

export const getUsageStats = async (token: string): Promise<UsageStatsResponse | null> => {
	let error = null;

	const res = await fetch(`${WEBUI_DEFAULT_API_BASE_URL}/usage`, {
		method: 'GET',
		headers: {
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		}
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			console.error(err);
			error = err;
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

export const getDailyHistory = async (
	token: string,
	days: number = 30
): Promise<DailyHistoryResponse | null> => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/usage/history/daily?days=${days}`, {
		method: 'GET',
		headers: {
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		}
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			console.error(err);
			error = err;
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

export const getMonthlyHistory = async (
	token: string,
	months: number = 12
): Promise<MonthlyHistoryResponse | null> => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/usage/history/monthly?months=${months}`, {
		method: 'GET',
		headers: {
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		}
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			console.error(err);
			error = err;
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

export const resetDailyUsage = async (
	token: string,
	targetDate?: string
): Promise<{ success: boolean; message: string; user_id: string; date: string } | null> => {
	let error = null;
	//not exists http://localhost:8080/docs#/default/get_current_usage_api_usage_get
	const res = await fetch(`${WEBUI_API_BASE_URL}/usage/reset/daily`, {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		},
		body: JSON.stringify(targetDate ? { target_date: targetDate } : {})
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			console.error(err);
			error = err;
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};
