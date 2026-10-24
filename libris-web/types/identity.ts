export type Identity = {
  actorId: string;
  displayName: string | null;
  pictureUrl: string | null;
  permissions: string[];
  roles: string[];
};