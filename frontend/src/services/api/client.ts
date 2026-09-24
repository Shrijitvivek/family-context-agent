const apiBaseUrl = (import.meta.env.VITE_API_BASE_URL ?? "").replace(/\/$/, "");

function buildUrl(path: string): string {
	const normalizedPath = path.startsWith("/") ? path : `/${path}`;

	if (apiBaseUrl.endsWith("/api/v1") && normalizedPath.startsWith("/api/v1/")) {
		return `${apiBaseUrl}${normalizedPath.slice("/api/v1".length)}`;
	}

	return `${apiBaseUrl}${normalizedPath}`;
}

export async function apiRequest<T>(path: string, init?: RequestInit): Promise<T> {
	const response = await fetch(buildUrl(path), {
		...init,
		headers: { Accept: "application/json", ...init?.headers },
	});

	if (!response.ok) {
		const message = await response.text();
		throw new Error(message || `Request failed with status ${response.status}`);
	}

	return response.json() as Promise<T>;
}
