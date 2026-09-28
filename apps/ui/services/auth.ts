const API_URL = process.env.NEXT_PUBLIC_API_URL;

export interface LoginResponse {
  message: string;
}

export async function login(
  username: string,
  password: string
): Promise<LoginResponse> {

  const body = new URLSearchParams();

  body.append("username", username);
  body.append("password", password);

  // const response = await fetch(`${API_URL}/auth/login`, {
  //   method: "POST",
  //   headers: {
  //     "Content-Type": "application/x-www-form-urlencoded",
  //   },
  //   body,
  // });

  const response = await fetch(`${API_URL}/auth/login`, {
    method: "POST",
    headers: {
      "Content-Type": "application/x-www-form-urlencoded",
    },
    credentials: "include",
    body,
  });


  if (!response.ok) {
    if (response.status === 401) {
      throw new Error("Usuário ou senha inválidos.");
    }

    throw new Error("Erro ao realizar login.");
  }

  return response.json();
}