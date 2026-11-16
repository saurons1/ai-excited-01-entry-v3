// ai-excited-01 v3 entrypoint: place the pre-rendered image where the grader looks.
//
// compose.py (same directory) draws entry.png at build time; this program only
// copies that finished image into the output directory. Node 22 stdlib only,
// no network, deterministic: the same input bytes come out every run.
import { copyFileSync, mkdirSync } from "node:fs";
import { join } from "node:path";
import { fileURLToPath } from "node:url";

const here = join(fileURLToPath(new URL(".", import.meta.url)));
const outDir = process.env.MAKEFUN_OUTPUT_DIR ?? "out";

mkdirSync(outDir, { recursive: true });
copyFileSync(join(here, "entry.png"), join(outDir, "entry.png"));
console.log(`entry.png -> ${join(outDir, "entry.png")}`);
