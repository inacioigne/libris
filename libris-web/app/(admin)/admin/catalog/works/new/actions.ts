"use server";

import { cookies } from "next/headers";

import { getApiOrigin } from "@/lib/api/origin";
import { getOidcLoginConfiguration, refreshAccessToken } from "@/lib/auth/oidc";
import {
  destroySession,
  getAccessToken,
  SESSION_COOKIE_NAME,
} from "@/lib/auth/session";

export type DraftPayload = {
  profileId: string;
  profileVersion: string;
  values: Record<string, string | string[]>;
};

export type DraftSubmissionState = {
  message: string;
  status: "idle" | "error" | "success";
};

function validPayload(value: unknown): value is DraftPayload {
  if (typeof value !== "object" || value === null || Array.isArray(value)) {
    return false;
  }
  const payload = value as Partial<DraftPayload>;
  return (
    typeof payload.profileId === "string" &&
    payload.profileId.length > 0 &&
    typeof payload.profileVersion === "string" &&
    payload.profileVersion.length > 0 &&
    typeof payload.values === "object" &&
    payload.values !== null &&
    !Array.isArray(payload.values) &&
    Object.values(payload.values).every(
      (fieldValue) =>
        typeof fieldValue === "string" ||
        (Array.isArray(fieldValue) &&
          fieldValue.every((item) => typeof item === "string")),
    )
  );
}

export async function submitWorkDraft(
  _previousState: DraftSubmissionState,
  payload: unknown,
): Promise<DraftSubmissionState> {
  void _previousState;
  if (!validPayload(payload)) {
    return { message: "Os dados do rascunho são inválidos.", status: "error" };
  }

  const cookieStore = await cookies();
  const sessionId = cookieStore.get(SESSION_COOKIE_NAME)?.value;
  if (!sessionId) {
    return {
      message: "Sua sessão expirou. Entre novamente para tentar de novo.",
      status: "error",
    };
  }

  let accessToken: string | null;
  try {
    const config = getOidcLoginConfiguration();
    accessToken = await getAccessToken(sessionId, (refreshToken) =>
      refreshAccessToken(config, refreshToken),
    );
  } catch (error) {
    console.error("Falha ao validar a sessão para enviar rascunho.", error);
    return {
      message: "Não foi possível validar sua sessão. Tente novamente.",
      status: "error",
    };
  }
  if (!accessToken) {
    return {
      message: "Sua sessão expirou. Entre novamente para tentar de novo.",
      status: "error",
    };
  }

  let response: Response;
  try {
    response = await fetch(
      new URL("/api/v1/bibliographic/drafts", getApiOrigin()),
      {
        body: JSON.stringify(payload),
        cache: "no-store",
        headers: {
          Authorization: `Bearer ${accessToken}`,
          "Content-Type": "application/json",
        },
        method: "POST",
      },
    );
  } catch (error) {
    console.error("Falha de comunicação ao enviar rascunho.", error);
    return {
      message: "Não foi possível comunicar com a API. Tente novamente.",
      status: "error",
    };
  }

  if (response.status === 401) {
    destroySession(sessionId);
    return {
      message: "Sua sessão expirou. Entre novamente para tentar de novo.",
      status: "error",
    };
  }
  if (response.status === 403) {
    return {
      message: "Você não tem permissão para enviar rascunhos.",
      status: "error",
    };
  }
  if (response.status === 422) {
    return {
      message:
        "A API rejeitou os dados do rascunho. Revise os campos e tente novamente.",
      status: "error",
    };
  }
  if (!response.ok) {
    return {
      message: "Não foi possível enviar o rascunho. Tente novamente.",
      status: "error",
    };
  }

  const result: unknown = await response.json().catch(() => null);
  if (
    typeof result !== "object" ||
    result === null ||
    !("message" in result) ||
    result.message !== "Rascunho enviado com sucesso."
  ) {
    return {
      message: "A API retornou uma resposta inesperada.",
      status: "error",
    };
  }
  return { message: result.message, status: "success" };
}
