import LoginForm from "@/app/components/loginForm";

export default function LoginPage() {
    return (
        <main className="min-h-screen flex flex-col items-center justify-center">
            <div
                className="p-6 rounded-lg bg-white border border-slate-300 shadow-xs md:p-8 dark:bg-neutral-800 dark:border-neutral-700">
                <h1 className="text-slate-900 text-center text-3xl font-bold dark:text-slate-50">Login</h1>
                <LoginForm />

            </div>


        </main>
    );
}