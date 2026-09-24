"use client";
import { login } from "@/lib/auth";
import { useRouter } from "next/navigation";
import { useState, SubmitEvent } from "react";

export default function LoginPage() {

    const router = useRouter();

    const [username, setUsername] = useState("");
    const [password, setPassword] = useState("");
    const [error, setError] = useState("");

    async function handleSubmit(
        event: SubmitEvent<HTMLFormElement>
    ) {
        event.preventDefault();

        setError("");

        try {
            await login(username, password);

            router.push("/admin");
            router.refresh();
        } catch {
            setError("Usuário ou senha inválidos.");
        }
    }

    return (
        <main className="min-h-screen flex flex-col items-center justify-center">
            <div
                className="p-6 rounded-lg bg-white border border-slate-300 shadow-xs md:p-8 dark:bg-neutral-800 dark:border-neutral-700">
                <h1 className="text-slate-900 text-center text-3xl font-bold dark:text-slate-50">Login</h1>
                {/* <LoginForm /> */}
                <form onSubmit={handleSubmit}>
                    <div>
                        <label>
                            Usuário
                        </label>
                        <input
                            type="text"
                            value={username}
                            onChange={(event) =>
                                setUsername(event.target.value)
                            }
                        />
                    </div>
                    <div>
                        <label>
                            Senha
                        </label>

                        <input
                            type="password"
                            value={password}
                            onChange={(event) =>
                                setPassword(event.target.value)
                            }
                        />
                    </div>

                    {error && (
                        <p>{error}</p>
                    )}

                    <button type="submit">
                        Entrar
                    </button>
                </form>
            </div>
        </main>
    );
}