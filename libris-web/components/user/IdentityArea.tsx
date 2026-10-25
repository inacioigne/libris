import type { Identity } from "@/types/identity";
import { LoginForm } from "./LoginForm";
import UserMenu from "./UserMenu";

type IdentityAreaProps = {
  identity: Identity | null;
};

export function IdentityArea({ identity }: IdentityAreaProps) {
  if (!identity) {
    return <LoginForm />;
  }

  return <UserMenu identity={identity} />;
}
