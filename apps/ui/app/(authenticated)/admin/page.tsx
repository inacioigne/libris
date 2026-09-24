import { cookies } from "next/headers";
import { redirect } from "next/navigation";

export default async function Page() {

  const cookieStore = await cookies();

  const token = cookieStore.get(
    "access_token"
  );

  if (!token) {
    redirect("/login");
  }

  return (
    <main style={{ padding: '2rem', fontFamily: 'sans-serif' }}>
      <h1>Admin</h1>
      <p>Essa é uma página inicial básica dentro do app autenticado.</p>
    </main>
  );
}
