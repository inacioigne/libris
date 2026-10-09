export const locales = ["pt", "en"] as const;
export type Locale = (typeof locales)[number];
export function isLocale(value: string): value is Locale {
  return locales.some((locale) => locale === value);
}
export const messages = {
  pt: {
    language: "Português", tagline: "Conhecimento conectado.",
    title: "Uma nova base para a gestão de bibliotecas.",
    description: "Libris é um sistema integrado de gestão bibliotecária, concebido com BIBFRAME e dados conectados desde o início.",
    stage: "Estrutura inicial · 0.1.0", about: "Fundamentos do projeto",
    semantic: "Catálogo semântico", semanticText: "Arquitetura preparada para Work, Instance e Item do BIBFRAME 2.0.",
    modular: "Arquitetura modular", modularText: "Domínios bem definidos para evoluir com as necessidades das bibliotecas.",
    accessible: "Acesso inclusivo", accessibleText: "Uma base responsiva, com navegação por teclado e suporte a português e inglês.",
    note: "Esta etapa estabelece a infraestrutura. Catalogação, circulação e pesquisa ainda não estão implementadas.",
    languages: "Escolher idioma", skip: "Ir para o conteúdo", footer: "Libris · Gestão bibliotecária e Linked Data",
  },
  en: {
    language: "English", tagline: "Connected knowledge.",
    title: "A new foundation for library management.",
    description: "Libris is an integrated library system designed around BIBFRAME and linked data from the start.",
    stage: "Initial scaffold · 0.1.0", about: "Project foundations",
    semantic: "Semantic catalog", semanticText: "An architecture prepared for BIBFRAME 2.0 Work, Instance and Item.",
    modular: "Modular architecture", modularText: "Clear domain boundaries that can evolve with libraries’ needs.",
    accessible: "Inclusive access", accessibleText: "A responsive foundation with keyboard navigation and Portuguese and English support.",
    note: "This stage establishes infrastructure. Cataloging, circulation and search are not implemented yet.",
    languages: "Choose language", skip: "Skip to content", footer: "Libris · Library management and Linked Data",
  },
} satisfies Record<Locale, Record<string, string>>;
