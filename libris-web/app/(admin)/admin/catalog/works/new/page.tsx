import { Suspense } from "react";

import { WorkCatalogingForm } from "@/components/forms/WorkCatalogingForm";
import {
  requestDefaultWorkProfile,
  requestVocabulary,
  type WorkProfileVocabularies,
} from "@/lib/cataloging/work-profile";

async function WorkProfile() {
  const profile = await requestDefaultWorkProfile();
  const vocabularyIds = [
    ...new Set(
      profile.sections.flatMap((section) =>
        section.fields
          .filter((field) => field.widget === "vocabulary-select")
          .map((field) => field.vocabulary)
          .filter((vocabulary): vocabulary is string => Boolean(vocabulary)),
      ),
    ),
  ];
  const entries = await Promise.all(
    vocabularyIds.map(async (vocabulary) => {
      try {
        return [
          vocabulary,
          { status: "loaded", vocabulary: await requestVocabulary(vocabulary) },
        ] as const;
      } catch (error) {
        console.error(`Falha ao carregar o vocabulario ${vocabulary}.`, error);
        return [
          vocabulary,
          {
            message: `Não foi possível carregar o vocabulário “${vocabulary}”.`,
            status: "error",
          },
        ] as const;
      }
    }),
  );
  const vocabularies = Object.fromEntries(entries) as WorkProfileVocabularies;

  return <WorkCatalogingForm profile={profile} vocabularies={vocabularies} />;
}

export default function Page() {
  return (
    <Suspense fallback={<p>Carregando perfil de catalogação…</p>}>
      <div className="p-5">
        <WorkProfile />

      </div>
      
    </Suspense>
  );
}
