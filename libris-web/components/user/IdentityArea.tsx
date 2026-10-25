import { requestIdentity } from "@/lib/auth/request";
import { LoginForm } from "./LoginForm";
import UserMenu from "./UserMenu";

export async function IdentityArea() {
  const identity = await requestIdentity();

  if (!identity) {
    return <LoginForm />;
  }

  return <UserMenu identity={identity} />;
}
