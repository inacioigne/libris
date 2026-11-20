"use client";

import { useState } from "react";

import { VocabularyCombobox } from "@/components/forms/VocabularyCombobox";
import type {
  WorkProfile,
  WorkProfileField,
  WorkProfileVocabularies,
} from "@/lib/cataloging/work-profile";

type FieldValue = string | string[];
type FieldValues = Record<string, FieldValue>;

type FieldRendererProps = {
  field: WorkProfileField;
  onChange: (value: FieldValue) => void;
  value: FieldValue;
  vocabularies: WorkProfileVocabularies;
};

type FieldRenderer = (props: FieldRendererProps) => React.ReactNode;

const inputClasses =
  "mt-2 w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-gray-900 shadow-sm focus:border-teal-600 focus:ring-2 focus:ring-teal-600/20 focus:outline-none dark:border-gray-700 dark:bg-gray-900 dark:text-white";

const fieldRenderers: Record<string, FieldRenderer> = {
  text: ({ field, onChange, value }) => (
    <input
      aria-required={field.required}
      className={inputClasses}
      id={field.id}
      name={field.id}
      onChange={(event) => onChange(event.target.value)}
      required={field.required}
      type="text"
      value={typeof value === "string" ? value : ""}
    />
  ),
  "vocabulary-select": ({ field, onChange, value, vocabularies }) => {
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
        onChange={onChange}
        repeatable={field.repeatable}
        required={field.required}
        terms={vocabulary?.status === "loaded" ? vocabulary.vocabulary.terms : []}
        value={value}
      />
    );
  },
};

function ProfileField({
  field,
  onChange,
  value,
  vocabularies,
}: FieldRendererProps) {
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
        renderField({ field, onChange, value, vocabularies })
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
  const [values, setValues] = useState<FieldValues>({});

  function updateField(fieldId: string, value: FieldValue) {
    setValues((currentValues) => ({
      ...currentValues,
      [fieldId]: value,
    }));
  }

  return (
    <form className="space-y-8">
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
              onChange={(value) => updateField(field.id, value)}
              value={values[field.id] ?? (field.repeatable ? [] : "")}
              vocabularies={vocabularies}
            />
          ))}
        </fieldset>
      ))}
    </form>
  );
}
