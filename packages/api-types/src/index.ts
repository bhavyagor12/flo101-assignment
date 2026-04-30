/**
 * Public type surface for the FastAPI backend.
 *
 * The `./generated` module is produced from `<repo>/openapi.json` by the
 * `type-gen` script (openapi-typescript). It exports `paths` and
 * `components`. This index pulls out the schemas onto ergonomic names so
 * consumers write `import type { SkillSpec } from "@flo101/api-types"`.
 *
 * If `./generated` is missing (fresh clone before type-gen has run), we
 * fall back to a placeholder so workspace tooling still compiles. Run
 * `make type-gen` (or `pnpm --filter @flo101/api-types type-gen`) to
 * populate it.
 */

// eslint-disable-next-line @typescript-eslint/triple-slash-reference
/// <reference path="./generated.ts" />

import type { components, paths } from "./generated";

export type Schemas = components["schemas"];
export type Paths = paths;

export type SkillSpec = Schemas["SkillSpec"];
export type SynthesizeRequest = Schemas["SynthesizeRequest"];
export type Rubric = Schemas["Rubric"];
export type RubricDimension = Schemas["RubricDimension"];
export type RubricAnchor = Schemas["RubricAnchor"];
export type CapabilityWiring = Schemas["CapabilityWiring"];

export type ArtifactSubmission = Schemas["ArtifactSubmission"];
// Artifact and CorpusChunk are server-internal persisted shapes; they
// don't appear on the API surface, so they're intentionally not exported
// here. Surface them via a route if the UI needs them.

export type CorpusUploadResult = Schemas["CorpusUploadResult"];

export type Evaluation = Schemas["Evaluation"];
export type DimensionScore = Schemas["DimensionScore"];
export type EvidenceItem = Schemas["EvidenceItem"];
export type Gap = Schemas["Gap"];
export type NextStep = Schemas["NextStep"];
export type CapabilityResult = Schemas["CapabilityResult"];

// Enum-like string unions
export type ArtifactKind = Schemas["ArtifactKind"];
export type CapabilityKind = Schemas["CapabilityKind"];
export type CapabilityStatus = Schemas["CapabilityStatus"];
export type EvaluationStatus = Schemas["EvaluationStatus"];
export type EvidenceSource = Schemas["EvidenceSource"];
export type GapSeverity = Schemas["GapSeverity"];
export type SafetyDisposition = Schemas["SafetyDisposition"];
export type StakesClass = Schemas["StakesClass"];
