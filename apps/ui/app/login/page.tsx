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
                <div className="mb-6 flex justify-center">
                    <img src="https://ri.inpa.gov.br/assets/inpa/images/logo_mini.png" alt="logo" className="w-12 min-h-12" />
                </div>
                <div className="text-center">
                    <h1 className="text-slate-900 text-center text-xl font-semibold mb-2 dark:text-slate-50">Bem vindo ao Libris</h1>
                    <p className="text-sm text-slate-600 dark:text-slate-400">Entre com seu email e senha.</p>
                </div>
                <form className="space-y-6 mt-10"
                    onSubmit={handleSubmit}>
                    <div>
                        <label htmlFor="username"
                            className="mb-2 text-slate-900 font-medium text-sm inline-block dark:text-slate-50">
                            Email
                        </label>
                        <input
                            type="text"
                            value={username}
                            onChange={(event) =>
                                setUsername(event.target.value)
                            }
                            className="px-3 py-2.5 text-sm text-slate-900 rounded-md bg-white w-full outline-1 -outline-offset-1 outline-slate-300 focus:outline-2 focus:-outline-offset-2 focus:outline-blue-600 dark:text-slate-50 dark:bg-neutral-700 dark:outline-neutral-600"
                        />
                    </div>
                    <div className="relative">
                        <label htmlFor="password"
                            className="mb-2 text-slate-900 font-medium text-sm inline-block dark:text-slate-50">
                            Senha
                        </label>
                        <button type="button" id="togglePassword" aria-label="Show password" aria-pressed="false"
                            className="absolute top-1 right-2 p-0.5 flex cursor-pointer focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-600 rounded">
                            <svg xmlns="http://www.w3.org/2000/svg"
                                className="size-[18px] fill-slate-400 text-slate-400 overflow-visible" viewBox="0 0 128 128">
                                <path
                                    d="M64 104C22.127 104 1.367 67.496.504 65.943a4 4 0 0 1 0-3.887C1.367 60.504 22.127 24 64 24s62.633 36.504 63.496 38.057a4 4 0 0 1 0 3.887C126.633 67.496 105.873 104 64 104zM8.707 63.994C13.465 71.205 32.146 96 64 96c31.955 0 50.553-24.775 55.293-31.994C114.535 56.795 95.854 32 64 32 32.045 32 13.447 56.775 8.707 63.994zM64 88c-13.234 0-24-10.766-24-24s10.766-24 24-24 24 10.766 24 24-10.766 24-24 24zm0-40c-8.822 0-16 7.178-16 16s7.178 16 16 16 16-7.178 16-16-7.178-16-16-16z">
                                </path>
                                <path id="eyeStrike" className="bloxk" d="M10.586 10.586l106.828 106.828" stroke="currentColor"
                                    stroke-width="10" stroke-linecap="round"></path>
                            </svg>
                        </button>

                        <input
                            type="password"
                            value={password}
                            onChange={(event) =>
                                setPassword(event.target.value)
                            }
                            className="px-3 py-2.5 text-sm text-slate-900 rounded-md bg-white w-full outline-1 -outline-offset-1 outline-slate-300 focus:outline-2 focus:-outline-offset-2 focus:outline-blue-600 dark:text-slate-50 dark:bg-neutral-700 dark:outline-neutral-600" 
                        />
                    </div>

                    {error && (
                        <p>{error}</p>
                    )}

                    <button type="submit"
                     className="w-full py-2 px-3.5 text-sm rounded-md font-semibold cursor-pointer tracking-wide text-white border border-blue-600 bg-blue-600 hover:bg-blue-700 transition-all focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500">
                        Entrar
                    </button>
                </form>
            </div>
        </main>
    );
}