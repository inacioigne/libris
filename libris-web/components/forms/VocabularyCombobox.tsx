"use client";

import { useId, useMemo, useRef, useState } from "react";
import { FiChevronDown, FiX } from "react-icons/fi";

import type { VocabularyTerm } from "@/lib/cataloging/work-profile";

type VocabularyComboboxProps = {
  describedBy?: string;
  disabled?: boolean;
  error?: string;
  fieldId: string;
  label: string;
  onChange: (uris: string[]) => void;
  repeatable?: boolean;
  required?: boolean;
  terms: VocabularyTerm[];
  selectedUris: string[];
};

const inputClasses =
  "w-full rounded-lg border border-gray-300 bg-white px-3 py-2 pr-10 text-gray-900 shadow-sm focus:border-teal-600 focus:ring-2 focus:ring-teal-600/20 focus:outline-none disabled:cursor-not-allowed disabled:bg-gray-100 dark:border-gray-700 dark:bg-gray-900 dark:text-white dark:disabled:bg-gray-800";

function normalizeSearch(value: string) {
  return value
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLocaleLowerCase("pt-BR");
}

export function VocabularyCombobox({
  describedBy,
  disabled = false,
  error,
  fieldId,
  label,
  onChange,
  repeatable = false,
  required = false,
  selectedUris,
  terms,
}: VocabularyComboboxProps) {
  const listboxId = `${fieldId}-${useId().replaceAll(":", "")}-listbox`;
  const inputRef = useRef<HTMLInputElement>(null);
  const [activeIndex, setActiveIndex] = useState(-1);
  const [isOpen, setIsOpen] = useState(false);
  const [query, setQuery] = useState("");
  const selectedTerms = selectedUris
    .map((uri) => terms.find((term) => term.uri === uri))
    .filter((term): term is VocabularyTerm => Boolean(term));
  const selectedTerm = repeatable ? undefined : selectedTerms[0];

  const options = useMemo(() => {
    const normalizedQuery = normalizeSearch(query.trim());
    return terms.filter((term) => {
      if (selectedUris.includes(term.uri)) return false;
      if (!normalizedQuery) return true;
      return (
        normalizeSearch(term.label).includes(normalizedQuery) ||
        normalizeSearch(term.code).includes(normalizedQuery)
      );
    });
  }, [query, selectedUris, terms]);

  function openList() {
    if (disabled) return;
    setIsOpen(true);
    setActiveIndex(options.length > 0 ? 0 : -1);
  }

  function closeList() {
    setIsOpen(false);
    setActiveIndex(-1);
  }

  function selectTerm(term: VocabularyTerm) {
    if (repeatable) {
      onChange([...selectedUris, term.uri]);
      setQuery("");
    } else {
      onChange([term.uri]);
      setQuery(term.label);
      closeList();
    }
  }

  function removeTerm(uri: string) {
    const nextValue = selectedUris.filter((selectedUri) => selectedUri !== uri);
    onChange(nextValue);
    if (!repeatable) setQuery("");
    inputRef.current?.focus();
  }

  const displayValue = selectedTerm && !isOpen ? selectedTerm.label : query;
  const activeOptionId =
    isOpen && activeIndex >= 0 && options[activeIndex]
      ? `${listboxId}-option-${activeIndex}`
      : undefined;

  return (
    <div>
      {selectedTerms.length > 0 && repeatable ? (
        <ul
          aria-label={`${label} selecionados`}
          className="mb-2 flex flex-wrap gap-2"
        >
          {selectedTerms.map((term) => (
            <li
              className="inline-flex items-center gap-1 rounded-full bg-teal-50 px-3 py-1 text-sm text-teal-900 ring-1 ring-teal-200 dark:bg-teal-950/50 dark:text-teal-100 dark:ring-teal-800"
              key={term.uri}
            >
              <span>{term.label}</span>
              <span className="text-xs text-teal-700 dark:text-teal-300">
                ({term.code})
              </span>
              <button
                aria-label={`Remover ${term.label} de ${label}`}
                className="ml-1 rounded-full p-0.5 hover:bg-teal-100 focus:ring-2 focus:ring-teal-600 focus:outline-none dark:hover:bg-teal-900"
                onClick={() => removeTerm(term.uri)}
                type="button"
              >
                <FiX aria-hidden="true" />
              </button>
              <input name={fieldId} type="hidden" value={term.uri} />
            </li>
          ))}
        </ul>
      ) : null}

      {!repeatable && selectedTerm ? (
        <input name={fieldId} type="hidden" value={selectedTerm.uri} />
      ) : null}

      <div className="relative">
        <input
          aria-activedescendant={activeOptionId}
          aria-autocomplete="list"
          aria-controls={listboxId}
          aria-describedby={describedBy}
          aria-expanded={isOpen}
          aria-haspopup="listbox"
          aria-invalid={Boolean(error)}
          aria-required={required}
          autoComplete="off"
          className={inputClasses}
          disabled={disabled}
          id={fieldId}
          onBlur={() => window.setTimeout(closeList, 100)}
          onChange={(event) => {
            if (selectedTerm) onChange([]);
            setQuery(event.target.value);
            setIsOpen(true);
            setActiveIndex(0);
          }}
          onFocus={openList}
          onKeyDown={(event) => {
            if (event.key === "ArrowDown") {
              event.preventDefault();
              if (!isOpen) openList();
              else setActiveIndex((index) => Math.min(index + 1, options.length - 1));
            } else if (event.key === "ArrowUp") {
              event.preventDefault();
              if (!isOpen) openList();
              else setActiveIndex((index) => Math.max(index - 1, 0));
            } else if (
              event.key === "Enter" &&
              isOpen &&
              activeIndex >= 0 &&
              options[activeIndex]
            ) {
              event.preventDefault();
              selectTerm(options[activeIndex]);
            } else if (event.key === "Escape") {
              event.preventDefault();
              closeList();
              if (selectedTerm) setQuery(selectedTerm.label);
            }
          }}
          placeholder={error ? "Vocabulário indisponível" : "Digite para buscar"}
          ref={inputRef}
          required={required && selectedUris.length === 0}
          role="combobox"
          type="text"
          value={displayValue}
        />

        <button
          aria-label={
            isOpen ? `Fechar opções de ${label}` : `Abrir opções de ${label}`
          }
          className="absolute inset-y-0 right-0 flex w-10 items-center justify-center rounded-r-lg text-gray-500 hover:text-gray-800 focus:ring-2 focus:ring-inset focus:ring-teal-600 focus:outline-none disabled:cursor-not-allowed dark:text-gray-400 dark:hover:text-white"
          disabled={disabled}
          onMouseDown={(event) => event.preventDefault()}
          onClick={() => {
            if (isOpen) closeList();
            else {
              openList();
              inputRef.current?.focus();
            }
          }}
          type="button"
        >
          <FiChevronDown aria-hidden="true" />
        </button>

        {isOpen ? (
          <div
            className="absolute z-20 mt-1 max-h-64 w-full overflow-y-auto rounded-lg border border-gray-200 bg-white py-1 shadow-lg dark:border-gray-700 dark:bg-gray-900"
            id={listboxId}
            role="listbox"
          >
            {options.length > 0 ? (
              options.map((term, index) => (
                <div
                  aria-selected={index === activeIndex}
                  className={`cursor-pointer px-3 py-2 text-sm ${
                    index === activeIndex
                      ? "bg-teal-50 text-teal-950 dark:bg-teal-950 dark:text-teal-50"
                      : "text-gray-900 hover:bg-gray-50 dark:text-white dark:hover:bg-gray-800"
                  }`}
                  id={`${listboxId}-option-${index}`}
                  key={term.uri}
                  onMouseDown={(event) => event.preventDefault()}
                  onMouseEnter={() => setActiveIndex(index)}
                  onClick={() => selectTerm(term)}
                  role="option"
                >
                  <span>{term.label}</span>{" "}
                  <span className="text-xs text-gray-500 dark:text-gray-400">
                    ({term.code})
                  </span>
                </div>
              ))
            ) : (
              <p
                className="px-3 py-2 text-sm text-gray-500 dark:text-gray-400"
                role="status"
              >
                Nenhum termo encontrado.
              </p>
            )}
          </div>
        ) : null}
      </div>

      {!repeatable && selectedTerm && !required ? (
        <button
          className="mt-2 text-sm text-teal-700 underline-offset-2 hover:underline dark:text-teal-300"
          onClick={() => removeTerm(selectedTerm.uri)}
          type="button"
        >
          Limpar seleção de {label}
        </button>
      ) : null}

      {error ? (
        <p className="mt-2 text-sm text-red-700 dark:text-red-300" role="alert">
          {error}
        </p>
      ) : null}
    </div>
  );
}
