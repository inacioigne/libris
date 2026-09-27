"use client";
import { useState } from "react";
import Image from "next/image";
import Link from "next/link";


export default function DashboardLayout({ children }: LayoutProps<"/">) {

    const [isOpen, setIsOpen] = useState(false);

    return (
        <div className="flex min-h-screen w-full bg-background">
            {/* Side nav */}
            <div className="w-44 shrink-0">
                <aside className="sticky top-0 flex h-screen w-44 flex-col border-r border-border bg-slate-100 dark:bg-slate-900">
                    {/* user  */}
                    <div className="flex h-16 items-center border-b border-border px-2">
                        <div className="flex w-full items-center justify-between rounded-md px-2 py-1 hover:bg-slate-200 dark:hover:bg-slate-800">
                            <div className="flex items-center">
                                <Image
                                    src="/avatar-icon.jpg"
                                    alt="User"
                                    className="mr-2 rounded-full"
                                    width={36}
                                    height={36}
                                />
                                <div className="flex flex-col">
                                    <span className="text-sm font-medium">Name</span>
                                    <span className="text-xs text-muted-foreground">Agent Admin</span>
                                </div>
                            </div>
                        </div>
                    </div>
                    <nav className="flex flex-grow flex-col gap-y-1 p-2">
                        <Link
                            href={"/admin"}
                            className="flex items-center rounded-md px-2 py-1.5 hover:bg-slate-200 dark:hover:bg-slate-800">
                            <span className="text-sm text-slate-700 dark:text-slate-300">
                                Dashboard
                            </span>

                        </Link>

                    </nav>
                    <div className="relative my-2 flex flex-col items-center justify-center gap-y-2 px-4 py-4">
                        <div className="dot-matrix absolute left-0 top-0 -z-10 h-full w-full" />
                        <span className="text-xs text-muted-foreground">Libris App</span>
                    </div>
                </aside>

            </div>
            <div className="flex min-w-0 flex-1 flex-col">
                    {/* Top Navbar */}
                    <div className="sticky top-0 z-30 flex h-16 shrink-0 items-center justify-between border-b border-border bg-background px-6">
                        <h1 className="text-2xl font-medium">Dashboard</h1>
                    </div>
                    {/* Dashboard */}
                    <main className="flex-1 overflow-auto p-6">
                        {children}
                    </main>
                {/* </div> */}
            </div>
        </div>
    )
}