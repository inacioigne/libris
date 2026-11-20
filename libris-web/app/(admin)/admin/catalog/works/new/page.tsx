import { Suspense } from "react";

import { WorkCatalogingForm } from "@/components/forms/WorkCatalogingForm";
import { requestDefaultWorkProfile } from "@/lib/cataloging/work-profile";

async function WorkProfile() {
  const profile = await requestDefaultWorkProfile();

  return <WorkCatalogingForm profile={profile} />;
}

export default function Page() {
  return (
    <Suspense fallback={<p>Carregando perfil de catalogação…</p>}>
      <WorkProfile />
    </Suspense>
  );
}
