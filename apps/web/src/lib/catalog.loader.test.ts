import { describe, expect, it } from "vitest";
import { readFileSync, readdirSync, statSync } from "node:fs";
import { resolve } from "node:path";

const projectRoot = resolve(import.meta.dirname, "..");
const dataDir = resolve(projectRoot, "data");
const indexSource = readFileSync(resolve(dataDir, "catalogIndex.ts"), "utf8");
const loaderSource = readFileSync(resolve(projectRoot, "lib/catalog.ts"), "utf8");

const quotedChunkNames = (source: string) =>
  new Set(Array.from(source.matchAll(/"([^\"]+_verified_resources\\.csv)"/g), ([, name]) => name));

describe("generated catalog chunk wiring", () => {
  it("keeps every generated verified chunk physically present", () => {
    const indexChunks = quotedChunkNames(indexSource);
    const physicalChunks = new Set(
      readdirSync(dataDir).filter((name) => name.endsWith("_verified_resources.csv") && statSync(resolve(dataDir, name)).isFile()),
    );

    expect([...indexChunks].filter((name) => !physicalChunks.has(name))).toEqual([]);
  });

  it("registers every generated chunk in the runtime lazy loader", () => {
    const indexChunks = quotedChunkNames(indexSource);
    const loaderChunks = quotedChunkNames(loaderSource);

    expect([...indexChunks].filter((name) => !loaderChunks.has(name))).toEqual([]);
  });
});
