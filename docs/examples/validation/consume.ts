// Contrato ilustrativo: gerar os tipos completos do OpenAPI antes de integrar o editor.
export type Diagnostic = {
  code: string; // Clientes devem tolerar códigos adicionados posteriormente.
  message: string;
  severity: "Violation" | "Warning" | "Info";
  category: "schema" | "semantic" | "profile" | "identity" | "reference" | "state" | "technical";
  field_ids: readonly string[];
  parameters: Readonly<Record<string, string | number>>;
};

export type ValidationResult = {
  contract_version: "1.0";
  state: "completed" | "failed";
  conforms?: boolean; // Ausente em falha técnica: nunca inferir true por omissão.
  profile_id: string;
  profile_release: string;
  profile_version: string;
  context: "snapshot" | "composed";
  request_id?: string;
  issues: readonly Diagnostic[];
};

export type ProblemDetails = {
  contract_version: "1.0";
  type: string;
  title: string;
  status: number;
  detail?: string;
  instance?: string;
  code: string;
  request_id: string;
  issues: readonly Diagnostic[];
  validation?: ValidationResult;
};

export function distribute(
  issues: readonly Diagnostic[],
  resolveField: (contractFieldId: string) => string | undefined,
): { fields: Map<string, Diagnostic[]>; global: Diagnostic[] } {
  const fields = new Map<string, Diagnostic[]>();
  const global: Diagnostic[] = [];
  for (const issue of issues) {
    const targets = new Set(issue.field_ids.map(resolveField).filter(
      (field): field is string => field !== undefined,
    ));
    if (targets.size === 0) global.push(issue);
    for (const field of targets) fields.set(field, [...(fields.get(field) ?? []), issue]);
  }
  return { fields, global };
}

export function message(
  issue: Diagnostic,
  translate: (code: string, parameters: Diagnostic["parameters"]) => string | undefined,
): string {
  // Traduções futuras entram em apps/web/src/i18n/messages.ts.
  return translate(issue.code, issue.parameters) ?? issue.message;
}

export function blocksWrite(result: ValidationResult): boolean {
  return result.state === "failed" || result.conforms !== true;
}

// Mapear IDs do perfil ou JSON Pointers para os campos reais; não comparar rótulos.
const mapping = new Map([
  ["http://id.loc.gov/ontologies/bibframe/Work/title", "title"],
  ["/title", "title"],
]);
export function workDiagnostics(result: ValidationResult) {
  return distribute(result.issues, (id) => mapping.get(id));
}
