"use client";

import { FormEvent, useState } from "react";
import { login } from "@/app/services/auth";

export default function LoginForm() {

    const [username, setUsername] = useState("");
    const [password, setPassword] = useState("");

    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");

    async function handleSubmit(event: FormEvent<HTMLFormElement>) {
        event.preventDefault();

        setError("");
        setLoading(true);

        try {
            const token = await login(username, password);

            console.log(token);

            // próxima etapa:
            // armazenar a sessão
            // redirecionar para a aplicação

        } catch (error) {

            setError(
                error instanceof Error
                    ? error.message
                    : "Erro ao realizar login."
            );

        } finally {
            setLoading(false);
        }
    }

    return (
        <form className="space-y-6 mt-10" onSubmit={handleSubmit}>

            {/* <div>
        <label htmlFor="username">
          Usuário
        </label>

        <input
          id="username"
          type="text"
          value={username}
          onChange={(event) => setUsername(event.target.value)}
          required
        />
      </div> */}
            <div>
                <label htmlFor="email"
                    className="mb-2 text-slate-900 font-medium text-sm inline-block dark:text-slate-50">Email</label>
                <input 
                type="email" 
                id="username" 
                name="email" 
                placeholder="admin@libris.com" 
                value={username}
                onChange={(event) => setUsername(event.target.value)}
                required
                className="px-3 py-2.5 text-sm text-slate-900 rounded-md bg-white w-full outline-1 -outline-offset-1 outline-slate-300 focus:outline-2 focus:-outline-offset-2 focus:outline-blue-600 dark:text-slate-50 dark:bg-neutral-700 dark:outline-neutral-600" />
            </div>

            <div>
                <label htmlFor="password">
                    Senha
                </label>

                <input
                    id="password"
                    type="password"
                    value={password}
                    onChange={(event) => setPassword(event.target.value)}
                    required
                />
            </div>

            {error && (
                <p>{error}</p>
            )}

            <button
                type="submit"
                disabled={loading}
            >
                {loading ? "Entrando..." : "Entrar"}
            </button>

        </form>
    );
}