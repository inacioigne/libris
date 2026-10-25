export default function Loading() {
  return (
    <main
      className="flex w-full flex-1 items-center justify-center bg-white px-6 py-16 dark:bg-black"
      aria-busy="true"
      aria-live="polite"
    >
      <p className="text-sm text-slate-600" role="status">
        Verificando acesso administrativo...
      </p>
    </main>
  );
}
