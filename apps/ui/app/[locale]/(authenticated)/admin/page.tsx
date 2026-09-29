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
    <div>
      <h1>Admin</h1>
    </div>
  );
}
