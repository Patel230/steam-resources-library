import { describe, expect, it } from "vitest";
import { lazyChunksForCountries, loadCatalogChunks } from "./catalog";

const EDITORIAL_CHUNK = "thailand_chula_icpc2024_editorials_verified_resources.csv";
const NOIPH_2020_GYM_CHUNK = "philippines_noiph2020_gym_verified_resources.csv";
const NOIPH_2020_ELIMINATIONS_CHUNK = "philippines_noiph2020_eliminations_verified_resources.csv";
const KKU_2010_ASSESSMENTS_CHUNK = "thailand_kku_2010_assessments_verified_resources.csv";
const KKU_2014_2013_EXAMS_CHUNK = "thailand_kku_2014_2013_exams_verified_resources.csv";
const KKU_2012_HOMEWORK_CHUNK = "thailand_kku_2012_homework_verified_resources.csv";
const KKU_2011_ASSESSMENTS_CHUNK = "thailand_kku_2011_assessments_verified_resources.csv";
const KKU_2009_HOMEWORK_CHUNK = "thailand_kku_2009_homework_verified_resources.csv";
const CHULA_2007_PRACTICE_CHUNK = "thailand_chula_2007_practice_verified_resources.csv";
const MAHIDOL_MUIC_MATH_CHUNK = "thailand_mahidol_muic_math_verified_resources.csv";
const SRI_LANKA_OUSL_CHUNK = "sri_lanka_ousl_verified_resources.csv";

describe("Sri Lanka OUSL Engineering Mathematics catalog chunk", () => {
  it("keeps both audited public English finals discoverable through lazy loading", async () => {
    expect(lazyChunksForCountries(["Sri Lanka"])).toContain(SRI_LANKA_OUSL_CHUNK);
    const catalog = await loadCatalogChunks([SRI_LANKA_OUSL_CHUNK]);
    const ouslRecords = catalog.filter((row) => row.country === "Sri Lanka" && row.track === "EM");
    expect(ouslRecords).toHaveLength(2);
    expect(ouslRecords.every((row) => row.language === "English")).toBe(true);
    expect(ouslRecords.every((row) => row.free_resource?.toLowerCase() === "yes")).toBe(true);
    expect(ouslRecords.every((row) => row.priority === "A")).toBe(true);
  });
});

describe("Thailand Chulalongkorn 2024 editorial catalog chunk", () => {
  it("registers the two verified English solution PDFs for Thailand lazy loading", async () => {
    expect(lazyChunksForCountries(["Thailand"])).toContain(EDITORIAL_CHUNK);

    const catalog = await loadCatalogChunks([EDITORIAL_CHUNK]);
    const editorials = catalog.filter((row) => row.resource_url.includes("icpc-2024.cp.eng.chula.ac.th/2024/editorials/"));

    expect(editorials).toHaveLength(2);
    expect(editorials.map((row) => row.language)).toEqual(["English", "English"]);
    expect(editorials.every((row) => row.resource_class === "Solutions" && row.free_resource === "yes")).toBe(true);
  });
});

describe("Philippines NOI.PH 2020 Finals Gym catalog chunk", () => {
  it("registers the two organiser-linked public English contest archives for Philippines lazy loading", async () => {
    expect(lazyChunksForCountries(["Philippines"])).toContain(NOIPH_2020_GYM_CHUNK);

    const catalog = await loadCatalogChunks([NOIPH_2020_GYM_CHUNK]);
    const archives = catalog.filter((row) => row.resource_url.includes("codeforces.com/gym/10268"));

    expect(archives).toHaveLength(2);
    expect(archives.map((row) => row.language)).toEqual(["English", "English"]);
    expect(archives.every((row) => row.resource_class.includes("contest problem archive") && row.free_resource?.toLowerCase() === "yes")).toBe(true);
  });
});

describe("Philippines NOI.PH 2020 Online Eliminations catalog chunk", () => {
  it("registers the organiser-posted public English 17-problem archive for Philippines lazy loading", async () => {
    expect(lazyChunksForCountries(["Philippines"])).toContain(NOIPH_2020_ELIMINATIONS_CHUNK);

    const catalog = await loadCatalogChunks([NOIPH_2020_ELIMINATIONS_CHUNK]);
    const archives = catalog.filter((row) => row.resource_url === "https://codeforces.com/group/Sw3sdIlMPV/contest/266012");

    expect(archives).toHaveLength(1);
    expect(archives[0]?.language).toBe("English");
    expect(archives[0]?.resource_class).toBe("National programming Olympiad contest problem archive");
    expect(archives[0]?.free_resource).toBe("Yes");
  });
});

describe("Thailand Khon Kaen 2010 assessment catalog chunk", () => {
  it("registers only the six independently verified English assignments and past quizzes for Thailand lazy loading", async () => {
    expect(lazyChunksForCountries(["Thailand"])).toContain(KKU_2010_ASSESSMENTS_CHUNK);

    const catalog = await loadCatalogChunks([KKU_2010_ASSESSMENTS_CHUNK]);
    const assessments = catalog.filter((row) => row.resource_url.includes("classes/188200_2010_1/"));

    expect(assessments).toHaveLength(6);
    expect(assessments.map((row) => row.language)).toEqual(Array(6).fill("English"));
    expect(assessments.every((row) => /homework problem set|past quiz/.test(row.resource_class) && row.free_resource === "Yes")).toBe(true);
  });
});

describe("Thailand Khon Kaen 2014-indexed 2013 assessment catalog chunk", () => {
  it("registers only the three independently verified English 2013 past assessments for Thailand lazy loading", async () => {
    expect(lazyChunksForCountries(["Thailand"])).toContain(KKU_2014_2013_EXAMS_CHUNK);

    const catalog = await loadCatalogChunks([KKU_2014_2013_EXAMS_CHUNK]);
    const assessments = catalog.filter((row) => row.resource_url.includes("classes/198200_2014_1/Exams/") && row.resource_url.includes("2013_1.pdf"));

    expect(assessments).toHaveLength(3);
    expect(assessments.map((row) => row.language)).toEqual(Array(3).fill("English"));
    expect(assessments.every((row) => row.resource_class === "University past examination questions" && row.free_resource === "Yes")).toBe(true);
  });
});

describe("Thailand Khon Kaen 2012 homework catalog chunk", () => {
  it("registers eleven independently verified English assignments and solutions for Thailand lazy loading", async () => {
    expect(lazyChunksForCountries(["Thailand"])).toContain(KKU_2012_HOMEWORK_CHUNK);

    const catalog = await loadCatalogChunks([KKU_2012_HOMEWORK_CHUNK]);
    const homework = catalog.filter((row) => row.resource_url.includes("classes/188200_2012_1/HW/"));

    expect(homework).toHaveLength(11);
    expect(homework.map((row) => row.language)).toEqual(Array(11).fill("English"));
    expect(homework.every((row) => row.resource_class.includes("assignment") && row.free_resource === "Yes")).toBe(true);
  });
});

describe("Thailand Khon Kaen 2011 assessment catalog chunk", () => {
  it("registers only the eight independently verified English assignments, solutions, and quizzes for Thailand lazy loading", async () => {
    expect(lazyChunksForCountries(["Thailand"])).toContain(KKU_2011_ASSESSMENTS_CHUNK);

    const catalog = await loadCatalogChunks([KKU_2011_ASSESSMENTS_CHUNK]);
    const assessments = catalog.filter((row) => row.resource_url.includes("classes/188200_2011_1/HW/") || row.resource_url.includes("classes/188200_2011_1/exams/"));

    expect(assessments).toHaveLength(8);
    expect(assessments.map((row) => row.language)).toEqual(Array(8).fill("English"));
    expect(assessments.every((row) => /University (assignment|quiz) (questions|solutions)/.test(row.resource_class) && row.free_resource === "Yes")).toBe(true);
  });
});

describe("Thailand Khon Kaen 2009 homework catalog chunk", () => {
  it("registers the seven directly linked independently verified English assignments and solution for Thailand lazy loading", async () => {
    expect(lazyChunksForCountries(["Thailand"])).toContain(KKU_2009_HOMEWORK_CHUNK);

    const catalog = await loadCatalogChunks([KKU_2009_HOMEWORK_CHUNK]);
    const homework = catalog.filter((row) => row.resource_url.includes("classes/188200/HW/"));

    expect(homework).toHaveLength(7);
    expect(homework.map((row) => row.language)).toEqual(Array(7).fill("English"));
    expect(homework.every((row) => /University assignment (questions|solutions)/.test(row.resource_class) && row.free_resource === "Yes")).toBe(true);
  });
});

describe("Thailand Chulalongkorn 2007 practice-problem catalog chunk", () => {
  it("registers the two independently verified English discrete-mathematics practice sets for Thailand lazy loading", async () => {
    expect(lazyChunksForCountries(["Thailand"])).toContain(CHULA_2007_PRACTICE_CHUNK);

    const catalog = await loadCatalogChunks([CHULA_2007_PRACTICE_CHUNK]);
    const practiceSets = catalog.filter((row) => row.resource_url.includes("cp.eng.chula.ac.th/~atiwong/2143110/2007-2-Practice"));

    expect(practiceSets).toHaveLength(2);
    expect(practiceSets.map((row) => row.language)).toEqual(["English", "English"]);
    expect(practiceSets.every((row) => row.resource_class === "University practice problem set" && row.free_resource === "Yes")).toBe(true);
  });
});


describe("Thailand Mahidol MUIC mathematics sample catalog chunk", () => {
  it("registers only the independently verified English substantive mathematics sample", async () => {
    expect(lazyChunksForCountries(["Thailand"])).toContain(MAHIDOL_MUIC_MATH_CHUNK);
    const catalog = await loadCatalogChunks([MAHIDOL_MUIC_MATH_CHUNK]);
    const samples = catalog.filter((row) => row.resource_url.includes("muic-www-assets.muic.io/example_of_mathematics_"));
    expect(samples).toHaveLength(1);
    expect(samples[0]?.language).toBe("English");
    expect(samples[0]?.track).toBe("EM");
    expect(samples[0]?.resource_class).toBe("question");
    expect(samples[0]?.free_resource?.toLowerCase()).toBe("yes");
  });
});
