import Link from "next/link";
import UserArea from "../user/UserArea";
import { ThemeToggleButton } from "../shared/ThemeToggleButton";

export default function Header() {
  return (
    <header className="sticky top-0 z-99999 flex w-full border-gray-200 bg-white xl:border-b dark:border-gray-800 dark:bg-gray-900">
      <div className="flex grow flex-col items-center justify-between xl:flex-row xl:px-6">
        <div className="flex w-full items-center justify-between gap-2 border-b border-gray-200 px-3 py-3 sm:gap-4 xl:justify-normal xl:border-b-0 xl:px-0 xl:py-4 dark:border-gray-800">
          <Link href={`/`}>
            <div className="text-3xl font-bold tracking-tight">
              libris
              <span className="text-teal-700 dark:text-teal-300">.</span>
            </div>
          </Link>
        </div>

          <div className="flex items-center gap-4 2xsm:gap-3">

          <div className="cursor-pointer">
            <ThemeToggleButton />
          </div>
          <UserArea />
        </div>
      </div>
    </header>
  );
}
