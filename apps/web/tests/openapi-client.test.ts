import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { test } from "node:test";

import { catalogographicClient, createCatalogographicClient } from "../src/generated/catalogographic-client";

test("generated catalog client exposes typed OpenAPI operations and core catalog schemas", async () => {
  const generated = await readFile(new URL("../src/generated/catalogographic-openapi.ts", import.meta.url), "utf8");
  assert.match(generated, /export interface paths/);
  assert.match(generated, /"\/api\/v1\/catalog\/works"/);
  assert.match(generated, /WorkRead/);
  assert.match(generated, /WorkCreate/);
  assert.equal(typeof catalogographicClient.GET, "function");
  assert.equal(typeof createCatalogographicClient("https://example.test").GET, "function");
});
