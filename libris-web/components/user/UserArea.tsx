import { Suspense } from "react";
import { IdentityArea } from "./IdentityArea";

export default async function UserArea() {
  return (
    <Suspense
      fallback={
        <p className="text-sm text-slate-600" role="status">
          Verificando sessão...
        </p>
      }
    >
      <IdentityArea />
    </Suspense>
  );
}
