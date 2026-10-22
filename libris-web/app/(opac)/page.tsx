export default function Home() {
  const returnTo = "/opac"
  return (
    <div className="flex flex-col flex-1 items-center justify-center bg-zinc-50 font-sans dark:bg-black">
      <main className="flex w-full max-w-3xl flex-col items-center justify-between py-32 px-16 bg-white dark:bg-black sm:items-start">
       <h1>Libris - Opac</h1>

        <form action="/oidc/login" method="post">
          <input type="hidden" name="returnTo" value={returnTo} />
          <button type="submit" className="cursor-pointer">
           <h1>Login</h1>
          </button>
        </form>
      </main>
    </div>
  );
}
