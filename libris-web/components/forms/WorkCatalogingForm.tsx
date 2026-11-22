"use client";

import { startTransition, useActionState, useState } from "react";

import {
  submitWorkDraft,
  type DraftPayload,
  type DraftSubmissionState,
} from "@/app/(admin)/admin/catalog/works/new/actions";
import { VocabularyCombobox } from "@/components/forms/VocabularyCombobox";
import type {
  WorkProfile,
  WorkProfileField,
  WorkProfileVocabularies,
} from "@/lib/cataloging/work-profile";

type TextFieldValues = Record<string, string>;

/**
 * Form contract for controlled-vocabulary fields.
 *
 * Values are the semantic URIs returned by the vocabulary API. Search text and
 * display labels never become cataloging values. Non-repeatable fields use the
 * same representation but contain at most one URI.
 *
 */
export type VocabularyFieldValues = Record<string, string[]>;

type ProfileFieldProps = {
  field: WorkProfileField;
  onTextChange: (value: string) => void;
  onVocabularyChange: (uris: string[]) => void;
  textValue: string;
  vocabularyValue: string[];
  vocabularies: WorkProfileVocabularies;
};

type FieldRenderer = (props: ProfileFieldProps) => React.ReactNode;

const inputClasses =
  "mt-2 w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-gray-900 shadow-sm focus:border-teal-600 focus:ring-2 focus:ring-teal-600/20 focus:outline-none dark:border-gray-700 dark:bg-gray-900 dark:text-white";

const initialDraftSubmissionState: DraftSubmissionState = {
  message: "",
  status: "idle",
};

const fieldRenderers: Record<string, FieldRenderer> = {
  text: ({ field, onTextChange, textValue }) => (
    <input
      aria-required={field.required}
      className={inputClasses}
      id={field.id}
      name={field.id}
      onChange={(event) => onTextChange(event.target.value)}
      required={field.required}
      type="text"
      value={textValue}
    />
  ),
  "vocabulary-select": ({
    field,
    onVocabularyChange,
    vocabularyValue,
    vocabularies,
  }) => {
    const vocabulary = field.vocabulary
      ? vocabularies[field.vocabulary]
      : undefined;
    const error =
      vocabulary?.status === "error"
        ? vocabulary.message
        : !vocabulary
          ? "Não foi possível identificar o vocabulário deste campo."
          : undefined;

    return (
      <VocabularyCombobox
        describedBy={`${field.id}-vocabulary`}
        disabled={Boolean(error)}
        error={error}
        fieldId={field.id}
        label={field.label}
        onChange={onVocabularyChange}
        repeatable={field.repeatable}
        required={field.required}
        selectedUris={vocabularyValue}
        terms={vocabulary?.status === "loaded" ? vocabulary.vocabulary.terms : []}
      />
    );
  },
};

function ProfileField({
  field,
  onTextChange,
  onVocabularyChange,
  textValue,
  vocabularyValue,
  vocabularies,
}: ProfileFieldProps) {
  const renderField = fieldRenderers[field.widget];
  const semanticPath = JSON.stringify(field.path);

  return (
    <div
      className="space-y-1"
      data-rdf-path={semanticPath}
      data-repeatable={field.repeatable || undefined}
    >
      <label
        className="block text-sm font-medium text-gray-800 dark:text-gray-200"
        htmlFor={field.id}
      >
        {field.label}
        {field.required ? <span aria-hidden="true"> *</span> : null}
      </label>

      {renderField ? (
        renderField({
          field,
          onTextChange,
          onVocabularyChange,
          textValue,
          vocabularyValue,
          vocabularies,
        })
      ) : (
        <p
          className="rounded-lg border border-red-300 bg-red-50 px-3 py-2 text-sm text-red-800 dark:border-red-900 dark:bg-red-950/40 dark:text-red-200"
          role="alert"
        >
          Não foi possível renderizar “{field.label}”: widget desconhecido “
          {field.widget}”.
        </p>
      )}

      {field.widget === "vocabulary-select" ? (
        <p
          className="text-xs text-gray-500 dark:text-gray-400"
          id={`${field.id}-vocabulary`}
        >
          Vocabulário controlado: {field.vocabulary ?? "não informado"}.
        </p>
      ) : null}
    </div>
  );
}

export function WorkCatalogingForm({
  profile,
  vocabularies,
}: {
  profile: WorkProfile;
  vocabularies: WorkProfileVocabularies;
}) {
  const [textValues, setTextValues] = useState<TextFieldValues>({});
  const [vocabularyValues, setVocabularyValues] =
    useState<VocabularyFieldValues>({});
  const [submission, submitDraft, isPending] = useActionState(
    submitWorkDraft,
    initialDraftSubmissionState,
  );

  function updateTextField(fieldId: string, value: string) {
    setTextValues((currentValues) => ({
      ...currentValues,
      [fieldId]: value,
    }));
  }

  function updateVocabularyField(fieldId: string, uris: string[]) {
    setVocabularyValues((currentValues) => ({
      ...currentValues,
      [fieldId]: uris,
    }));
  }

  function draftPayload(): DraftPayload {
    const values: DraftPayload["values"] = {};
    for (const section of profile.sections) {
      for (const field of section.fields) {
        if (field.widget === "vocabulary-select") {
          const selectedUris = vocabularyValues[field.id] ?? [];
          if (selectedUris.length > 0) values[field.id] = selectedUris;
        } else {
          const text = textValues[field.id] ?? "";
          if (text.length > 0) values[field.id] = text;
        }
      }
    }
    return { profileId: profile.id, profileVersion: profile.version, values };
  }

  return (
    <form
      className="space-y-8"
      onSubmit={(event) => {
        event.preventDefault();
        startTransition(() => submitDraft(draftPayload()));
      }}
    >
      <h1 className="text-2xl font-semibold text-gray-950 dark:text-white">
        {profile.name}
      </h1>

      {profile.sections.map((section) => (
        <fieldset
          className="space-y-5 rounded-xl border border-gray-200 p-5 dark:border-gray-800"
          key={section.id}
        >
          <legend className="px-2 text-lg font-semibold text-gray-900 dark:text-white">
            {section.label}
          </legend>

          {section.fields.map((field) => (
            <ProfileField
              field={field}
              key={field.id}
              onTextChange={(value) => updateTextField(field.id, value)}
              onVocabularyChange={(uris) =>
                updateVocabularyField(field.id, uris)
              }
              textValue={textValues[field.id] ?? ""}
              vocabularyValue={vocabularyValues[field.id] ?? []}
              vocabularies={vocabularies}
            />
          ))}
        </fieldset>
      ))}

      <div className="flex flex-wrap items-center gap-4">
        <button
          className="rounded-lg bg-teal-700 px-4 py-2 font-medium text-white hover:bg-teal-800 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-teal-700 disabled:cursor-not-allowed disabled:opacity-60"
          disabled={isPending}
          formNoValidate
          type="submit"
        >
          {isPending ? "Enviando…" : "Salvar rascunho"}
        </button>
        <p
          aria-live="polite"
          className={
            submission.status === "error"
              ? "text-red-700 dark:text-red-300"
              : "text-teal-800 dark:text-teal-200"
          }
          role={submission.status === "error" ? "alert" : "status"}
        >
          {submission.message}
        </p>
      </div>
    </form>
  );
}
