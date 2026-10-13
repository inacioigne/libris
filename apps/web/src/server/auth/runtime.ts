import "server-only";
import { readConfig } from "./config";
import { OpenIdProvider } from "./oidc";
import { AuthService } from "./service";
import { createPool, PostgresAuthStore } from "./store";

// Only the connection pool and public provider metadata are process-local.
// All session/transaction state is persisted in PostgreSQL.
let service: AuthService | undefined;
export function authService(): AuthService {
  if (!service) {

    // console.log("[AUTH] Iniciando AuthService...");
    // try {
    //   const config = readConfig();
    // } catch (error) {
    //   console.error("[AUTH] Erro ao ler configurações:", error);
    //   throw error;
    // }
    
    const config = readConfig();
    service = new AuthService(
      config,
      new PostgresAuthStore(createPool(config), config),
      new OpenIdProvider(config),
    );
  }
  return service;
}
