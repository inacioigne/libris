import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import { FaBookOpen } from "react-icons/fa";


export default async function Page() {

    const cookieStore = await cookies();

    const token = cookieStore.get(
        "access_token"
    );

    if (!token) {
        redirect("/login");
    }



    return (
        <div className="grid grid-cols-12 gap-4 md:gap-6">
            <div className="col-span-12 space-y-6 xl:col-span-7">
                <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 md:gap-6">
                    <div className="rounded-2xl border border-gray-200 bg-white p-5 md:p-6 dark:border-gray-800 dark:bg-white/3">
                        <div className="flex items-center gap-4">
                            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-gray-100 dark:bg-gray-800">
                                <FaBookOpen />
                            </div>
                            <h1>Monograph</h1></div>
                    </div>
                </div>
            </div>
        </div>
    );
}
