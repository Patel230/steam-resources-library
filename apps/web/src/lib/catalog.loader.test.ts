import { describe, expect, it } from "vitest";
import { readFileSync, readdirSync, statSync } from "node:fs";
import { resolve } from "node:path";

const projectRoot = resolve(import.meta.dirname, "..");
const dataDir = resolve(projectRoot, "data");
const indexSource = readFileSync(resolve(dataDir, "catalogIndex.ts"), "utf8");

const indexChunkNames = () => {
  const names = Array.from(indexSource.matchAll(/"([a-z0-9_]+_verified_resources\.csv)"/g), (match) => match[1]!);
  if (!names.length) throw new Error("No chunk names found in catalogIndex.ts — parser out of sync with generator");
  return new Set(names);
};

const loaderChunkNames = () => {
  const loadersSection = indexSource.slice(indexSource.indexOf("export const csvChunkLoaders"));
  const names = Array.from(loadersSection.matchAll(/"([a-z0-9_]+_verified_resources\.csv)": \(\) => import/g), (match) => match[1]!);
  if (!names.length) throw new Error("No loader entries found in catalogIndex.ts — generator output changed");
  return new Set(names);
};

describe("generated catalog chunk wiring", () => {
  it("keeps every generated verified chunk physically present", () => {
    const indexChunks = indexChunkNames();
    const physicalChunks = new Set(
      readdirSync(dataDir).filter((name) => name.endsWith("_verified_resources.csv") && statSync(resolve(dataDir, name)).isFile()),
    );
    expect(physicalChunks.size).toBeGreaterThan(0);

    expect([...indexChunks].filter((name) => !physicalChunks.has(name))).toEqual([]);
    expect([...physicalChunks].filter((name) => !indexChunks.has(name))).toEqual([]);
  });

  it("registers every generated chunk in the runtime lazy loader", () => {
    const indexChunks = indexChunkNames();
    const loaderChunks = loaderChunkNames();

    expect([...indexChunks].filter((name) => !loaderChunks.has(name))).toEqual([]);
    expect([...loaderChunks].filter((name) => !indexChunks.has(name))).toEqual([]);
  });
});
