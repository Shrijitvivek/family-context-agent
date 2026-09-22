const apiBaseUrl = "";

export async function apiRequest<T>(path: string, init?: RequestInit): Promise<T> {
	const response = await fetch(`${apiBaseUrl}${path}`, {
		...init,
		headers: { Accept: "application/json", ...init?.headers },
	});

	if (!response.ok) {
		const message = await response.text();
		throw new Error(message || `Request failed with status ${response.status}`);
	}

	return response.json() as Promise<T>;
}
