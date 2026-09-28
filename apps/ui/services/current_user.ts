const API_URL = process.env.NEXT_PUBLIC_API_URL;

export interface CurrentUser {
  id: string;
  username: string;
  email: string;
  roles: string[];
}

export async function getCurrentUser(): Promise<CurrentUser | null> {
  const response = await fetch(`${API_URL}/auth/me`, {
    method: "GET",
    credentials: "include",
    cache: "no-store",
  });

  if (response.status === 401) {
    return null;
  }

  if (!response.ok) {
    throw new Error("Erro ao carregar usuário.");
  }

  return response.json();
}