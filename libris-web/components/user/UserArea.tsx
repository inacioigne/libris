import { Suspense } from "react";
import { requestIdentity } from "@/lib/auth/request";
import { IdentityArea } from "./IdentityArea";

async function IdentityAreaLoader() {
  const identity = await requestIdentity();

  return <IdentityArea identity={identity} />;
}

export default function UserArea() {
  return (
    <Suspense
      fallback={
        <p className="text-sm text-slate-600" role="status">
          Verificando sessão...
        </p>
      }
    >
      <IdentityAreaLoader />
    </Suspense>
  );
}
