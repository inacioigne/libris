import {
  adminPermission,
  requireAdminPageAccess,
} from "../../../../page-access";

export default async function Page() {
  await requireAdminPageAccess(
    {
      anyOf: [
        adminPermission.bibliographicCreate,
        adminPermission.systemAdmin,
      ],
    },
    "/admin/catalog/works/new",
  );

  return <h1>NOVA CATALOGAÇÃO</h1>;
}
