// Step 6 search runner (HELIX evolution program, 2026-11-18).
//
// Runs ONE task through ONE recipe-file harness and prints the CLI-shaped
// run-record JSON to stdout (only JSON on stdout; errors to stderr with a
// non-zero exit). This file exists because NO CLI command runs a recipe
// file with the prior-step protocol (see DESIGN.md sections 1.1/1.5/P5):
// `helix run` accepts only 5 fixed products, `tui` drops the transcript
// and fixes max-steps by profile, task-parity/server cannot run our tasks
// at max-steps 12 with external scoring.
//
// LINEAGE (every behaviour below is copied from, or proven equivalent to,
// upstream code; no harness behaviour is invented here):
//  1. Recipe parsing/compilation: parseRecipe + compileRecipe from
//     packages/recipes/src/compiler.ts (the same functions the CLI's
//     validate/assemble commands use).
//  2. Assembly: assembleRecipeHarness from packages/recipes/src/harness.ts
//     (the same function the TUI, task-parity, and docs-site server use).
//     Probe P4 (DESIGN 1.4) proved it behaviourally identical to the CLI's
//     hardcoded assemblePiMonoHarness on deterministic fixture turns.
//  3. Provider: createOpenAICompatibleProvider({models: [modelID], baseURL,
//     apiKey}) -- copied argument-for-argument from createCliProvider for
//     kind "openai-compatible" in packages/cli/src/index.ts. No other
//     provider kind is supported.
//  4. Turn: runTurn({text, provider, maxSteps}) with NO maxRetries, NO
//     syntheticContinue, NO sessionID -- exactly as the prior drivers
//     invoked the CLI (profile defaults apply).
//  5. Record emission: summarizeMessage/partToText copied verbatim in logic
//     from packages/cli/src/index.ts; output fields match the CLI run
//     record, PLUS recipeID/recipeFile/blend provenance fields.
//  6. Errors: a thrown exception exits non-zero with no JSON (driver ->
//     INFRA), mirroring the CLI's top-level catch. A RESOLVED turn with
//     result.error set is emitted as a record with exit 0 (driver ->
//     INFRA via the harness-error rule), mirroring the CLI.
//
// Imports use absolute upstream source paths only (the pattern the Phase-0
// probes used); this file lives outside upstream and writes nothing there.
// Usage:
//   tsx runner.mts --recipe <recipe.json> --model <id> --base-url <url>/v1 \
//     --api-key dummy --prompt <text> --max-steps 12 --cwd <ws> --storage-dir <dir>
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { assembleRecipeHarness, harnessComboBlendForRecipe } from "/home/hatch/workspace/helix-eval/upstream/packages/recipes/src/harness.ts";
import { compileRecipe, parseRecipe } from "/home/hatch/workspace/helix-eval/upstream/packages/recipes/src/compiler.ts";
import { createOpenAICompatibleProvider } from "/home/hatch/workspace/helix-eval/upstream/packages/lego-provider/src/openai-compatible.ts";

function fail(message: string, code = 1): never {
  process.stderr.write(`runner: ${message}\n`);
  process.exit(code);
}

function partToText(part: any): string {
  if (part.type === "text" || part.type === "reasoning") return part.text;
  if (part.type === "tool_call") return `[tool:${part.toolName}] ${JSON.stringify(part.input)}`;
  if (part.type === "tool_result") return part.content.map(partToText).filter(Boolean).join("\n");
  if (part.type === "compaction") return part.summary;
  if (part.type === "custom") return part.display ?? "";
  return "";
}

function summarizeMessage(message: any): { role: string; text: string; parts: any[] } {
  return {
    role: message.role,
    text: message.parts.map(partToText).filter(Boolean).join("\n"),
    parts: message.parts,
  };
}

function parseArgs(argv: string[]): {
  recipeFile: string; modelID: string; baseURL: string; apiKey: string;
  prompt: string; maxSteps: number; cwd: string; storageDir: string;
} {
  const out: Record<string, string> = {};
  for (let i = 0; i < argv.length; i++) {
    const arg = argv[i]!;
    if (!arg.startsWith("--")) fail(`unexpected argument: ${arg}`, 2);
    const value = argv[++i];
    if (value === undefined || value.startsWith("--")) fail(`missing value for ${arg}`, 2);
    out[arg.slice(2)] = value;
  }
  for (const key of ["recipe", "model", "base-url", "api-key", "prompt", "max-steps", "cwd", "storage-dir"]) {
    if (!(key in out)) fail(`missing required option --${key}`, 2);
  }
  const maxSteps = Number(out["max-steps"]);
  if (!Number.isInteger(maxSteps) || maxSteps <= 0) fail(`--max-steps must be a positive integer, got: ${out["max-steps"]}`, 2);
  return {
    recipeFile: resolve(out["recipe"]!),
    modelID: out["model"]!,
    baseURL: out["base-url"]!,
    apiKey: out["api-key"]!,
    prompt: out["prompt"]!,
    maxSteps,
    cwd: resolve(out["cwd"]!),
    storageDir: resolve(out["storage-dir"]!),
  };
}

async function main(): Promise<void> {
  const args = parseArgs(process.argv.slice(2));
  let recipe: any;
  try {
    recipe = parseRecipe(JSON.parse(readFileSync(args.recipeFile, "utf8")));
  } catch (error) {
    fail(`invalid recipe file ${args.recipeFile}: ${error instanceof Error ? error.message : String(error)}`);
  }
  // Compile gate: throws on an uncompilable recipe before any assembly.
  compileRecipe(recipe);
  const harness: any = assembleRecipeHarness(recipe, { cwd: args.cwd, storageDir: args.storageDir });
  const provider: any = createOpenAICompatibleProvider({
    models: [args.modelID],
    baseURL: args.baseURL,
    apiKey: args.apiKey,
  });
  const result: any = await harness.runTurn({
    text: args.prompt,
    provider,
    maxSteps: args.maxSteps,
  });
  const output = {
    product: harness.product,
    recipeID: recipe.id,
    recipeFile: args.recipeFile,
    blend: harnessComboBlendForRecipe(recipe) ?? null,
    graph: harness.graph,
    session: result.session,
    blockedTools: result.blockedTools,
    steps: result.steps,
    retries: result.retries,
    syntheticContinues: result.syntheticContinues,
    ...(result.finish ? { finish: result.finish } : {}),
    ...(result.error ? { error: result.error } : {}),
    transcript: result.transcript.map(summarizeMessage),
    assistantParts: result.assistantMessage.parts,
  };
  process.stdout.write(`${JSON.stringify(output, null, 2)}\n`);
}

main().catch((error) => {
  fail(error instanceof Error ? `${error.name}: ${error.message}` : String(error));
});
