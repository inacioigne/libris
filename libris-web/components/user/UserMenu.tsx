"use client";

import { useCallback, useEffect, useId, useRef, useState } from "react";
import { IoChevronDown, IoSettingsOutline } from "react-icons/io5";
import Image from "next/image";

import type { Identity } from "@/types/identity";
import Link from "next/link";
import { GiExitDoor } from "react-icons/gi";

type UserMenuProps = {
  identity: Identity;
};

export default function UserMenu({ identity }: UserMenuProps) {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownId = useId();
  const dropdownRef = useRef<HTMLDivElement>(null);

  const toggleDropdown = () => {
    setIsOpen((open) => !open);
  };
  const closeDropdown = useCallback(() => {
    setIsOpen(false);
  }, []);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(event.target as Node) &&
        !(event.target as HTMLElement).closest(".dropdown-toggle")
      ) {
        closeDropdown();
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [closeDropdown]);
  return (
    <div className="relative">
      <button
        type="button"
        onClick={toggleDropdown}
        aria-expanded={isOpen}
        aria-controls={isOpen ? dropdownId : undefined}
        className="dropdown-toggle flex items-center text-gray-700 dark:text-gray-400 cursor-pointer"
      >
        {identity.pictureUrl && (
          <Image
            src={identity.pictureUrl}
            alt={"User"}
            width={44}
            height={44}
            className="me-3 h-11 shrink-0 overflow-hidden rounded-full object-cover"
          />
        )}
        <span className="me-1 block text-theme-sm font-medium">
          {identity.displayName}
        </span>
        <IoChevronDown
          className={`size-5 text-gray-500 transition-transform duration-200 dark:text-gray-400 ${
            isOpen ? "rotate-180" : ""
          }`}
        />
      </button>
      {isOpen && (
        <div
          id={dropdownId}
          ref={dropdownRef}
          className="absolute mt-4.25 flex w-65 flex-col rounded-2xl border border-gray-200 bg-white p-3 text-gray-700 shadow-lg transition-colors ltr:right-0 rtl:right-auto rtl:left-0 dark:border-gray-800 dark:bg-gray-900 dark:text-gray-200 dark:shadow-black/30"
        >
          <div>
            <span className="block pl-2 text-theme-sm font-medium text-gray-700 dark:text-gray-400">
              {identity.displayName}
            </span>
          </div>
          <ul className="flex flex-col gap-1 border-gray-200 pt-4 pb-3 dark:border-gray-800">
            {identity.roles.includes("libris-admin") && (
              <li>
                <Link
                  href={`/admin`}
                  onClick={closeDropdown}
                  className="flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-100 hover:no-underline! focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-teal-600 dark:text-gray-400 dark:hover:bg-gray-800"
                >
                  <IoSettingsOutline
                    aria-hidden="true"
                    className="size-5 shrink-0"
                  />
                  <span>Área administrativa</span>
                </Link>
              </li>
            )}
            <li className="mt-1 border-t">
              <form action="/oidc/logout" method="post">
                <button
                  type="submit"
                  // onClick={closeDropdown}
                  className="flex items-center gap-3 rounded-lg mt-4 px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-100 hover:no-underline! focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-teal-600 dark:text-gray-400 dark:hover:bg-gray-800"
                >
                  <GiExitDoor className="size-5 shrink-0" />
                  <span>Sair</span>
                </button>
              </form>
            </li>
          </ul>
        </div>
      )}
    </div>
  );
}
