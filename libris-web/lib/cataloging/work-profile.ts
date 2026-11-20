import "server-only";

import { connection } from "next/server";

import { getApiOrigin } from "@/lib/api/origin";

const BIBFRAME_WORK_CLASS =
  "http://id.loc.gov/ontologies/bibframe/Work" as const;

export type WorkProfileField = {
  id: string;
  label: string;
  path: string[];
  repeatable?: boolean;
  required: boolean;
  vocabulary?: string;
  widget: string;
};

export type WorkProfileSection = {
  fields: WorkProfileField[];
  id: string;
  label: string;
};

export type WorkProfile = {
  id: string;
  name: string;
  sections: WorkProfileSection[];
  targetClass: typeof BIBFRAME_WORK_CLASS;
  version: string;
};

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function isNonEmptyString(value: unknown): value is string {
  return typeof value === "string" && value.trim().length > 0;
}

function isHttpUrl(value: unknown): value is string {
  if (!isNonEmptyString(value)) return false;

  try {
    const url = new URL(value);
    return url.protocol === "http:" || url.protocol === "https:";
  } catch {
    return false;
  }
}

function parseField(value: unknown): WorkProfileField {
  if (!isRecord(value)) {
    throw new Error("A API retornou um campo invalido no perfil de Work.");
  }

  const { id, label, path, repeatable, required, vocabulary, widget } = value;
  if (
    !isNonEmptyString(id) ||
    !isNonEmptyString(label) ||
    !isNonEmptyString(widget) ||
    typeof required !== "boolean" ||
    !Array.isArray(path) ||
    path.length === 0 ||
    !path.every(isHttpUrl) ||
    (repeatable !== undefined && typeof repeatable !== "boolean") ||
    (vocabulary !== undefined && !isNonEmptyString(vocabulary))
  ) {
    throw new Error("A API retornou um campo invalido no perfil de Work.");
  }

  return {
    id,
    label,
    path,
    required,
    widget,
    ...(repeatable === undefined ? {} : { repeatable }),
    ...(vocabulary === undefined ? {} : { vocabulary }),
  };
}

function parseSection(value: unknown): WorkProfileSection {
  if (!isRecord(value)) {
    throw new Error("A API retornou uma secao invalida no perfil de Work.");
  }

  const { fields, id, label } = value;
  if (
    !isNonEmptyString(id) ||
    !isNonEmptyString(label) ||
    !Array.isArray(fields)
  ) {
    throw new Error("A API retornou uma secao invalida no perfil de Work.");
  }

  return { fields: fields.map(parseField), id, label };
}

export function parseWorkProfile(value: unknown): WorkProfile {
  if (!isRecord(value)) {
    throw new Error("A API retornou um perfil de Work invalido.");
  }

  const { id, name, sections, targetClass, version } = value;
  if (
    !isNonEmptyString(id) ||
    !isNonEmptyString(version) ||
    !isNonEmptyString(name) ||
    targetClass !== BIBFRAME_WORK_CLASS ||
    !Array.isArray(sections)
  ) {
    throw new Error("A API retornou um perfil de Work invalido.");
  }

  return {
    id,
    name,
    sections: sections.map(parseSection),
    targetClass,
    version,
  };
}

export async function requestDefaultWorkProfile(): Promise<WorkProfile> {
  await connection();

  const response = await fetch(
    new URL(
      "/api/v1/bibliographic/profile/work-default.v1.json",
      getApiOrigin(),
    ),
    { cache: "no-store" },
  );

  if (!response.ok) {
    throw new Error(`A API de catalogacao retornou ${response.status}.`);
  }

  return parseWorkProfile(await response.json());
}
