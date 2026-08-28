export type EvidenceState =
  | "measured"
  | "provided"
  | "diagnostic"
  | "needs-verification";

export interface Claim {
  id: string;
  statement: string;
  scope: string;
  evidenceState: EvidenceState;
  limitation?: string;
  numerator?: number;
  denominator?: number;
  method?: string;
}

export interface TaskMedia {
  id: string;
  title: string;
  question: string;
  src: string;
  poster: string;
  playback: string;
  duration: string;
  autonomy: string;
  coverage: string;
  caption: string;
  evidenceState: EvidenceState;
}

export const taskMediaRoot =
  "https://github.com/YananZHOU5555/stereopatch/releases/download/media-v1";

export const claims: Claim[] = [
  {
    id: "interface",
    statement:
      "Bind registered metric geometry to RGB patch addresses before action decoding.",
    scope:
      "Frozen DINOv3 and DeFM fields; two asymmetric retrieval blocks; ACT or Diffusion Policy.",
    evidenceState: "provided",
  },
  {
    id: "held-out-placement",
    statement: "80.0% held-out placement success",
    scope: "32/40 trials with two demonstrations per one of 20 spatial anchors.",
    evidenceState: "measured",
    numerator: 32,
    denominator: 40,
    method: "StereoPatch-ACT",
  },
  {
    id: "held-out-picking",
    statement: "81.1% held-out object-picking success",
    scope: "60/74 trials with two demonstrations per one of 37 spatial anchors.",
    evidenceState: "measured",
    numerator: 60,
    denominator: 74,
    method: "StereoPatch-ACT",
  },
  {
    id: "bowl-stereopatch-dp",
    statement: "97.5% bowl-extraction success",
    scope:
      "78/80 trials under the 80-trial bowl protocol; failures: 0 empty and 2 multiple-bowl extractions.",
    evidenceState: "measured",
    numerator: 78,
    denominator: 80,
    method: "StereoPatch-DP",
    limitation:
      "Observed system-level result; it does not isolate representation causality.",
  },
  {
    id: "bowl-pi05-reference",
    statement: "81.3% bowl-extraction success",
    scope:
      "65/80 trials under the 80-trial bowl protocol; failures: 5 empty and 10 multiple-bowl extractions.",
    evidenceState: "measured",
    numerator: 65,
    denominator: 80,
    method: "π0.5-FT",
    limitation:
      "Contextual complete-system reference; policy heads and training stacks differ.",
  },
  {
    id: "boundary",
    statement:
      "The results support an interface-level conclusion, not a unique causal mechanism.",
    scope: "Matched fixed-base protocols under limited demonstrations.",
    evidenceState: "provided",
    limitation:
      "Mobile manipulation, coupled viewpoint change, navigation, and broader workspace variation remain untested.",
  },
];

export const tasks: TaskMedia[] = [
  {
    id: "placement",
    title: "Placement",
    question: "Can a destination learned from sparse anchors generalize to held-out coordinates?",
    src: `${taskMediaRoot}/placement.mp4`,
    poster: "media/video-4k60/placement.jpg",
    playback: "2× playback",
    duration: "01:03.2 full edit",
    autonomy: "Autonomous policy rollout",
    coverage: "Multi-position protocol",
    caption: "Complete multi-position edit; success rates come from the fixed held-out protocol.",
    evidenceState: "provided",
  },
  {
    id: "picking",
    title: "Object picking",
    question: "Can the policy localize a source object outside the demonstrated coordinates?",
    src: `${taskMediaRoot}/picking.mp4`,
    poster: "media/video-4k60/picking.jpg",
    playback: "2× playback",
    duration: "00:58.6 full edit",
    autonomy: "Autonomous policy rollout",
    coverage: "Multi-position protocol",
    caption: "Complete multi-position edit; not an independent evaluation denominator.",
    evidenceState: "provided",
  },
  {
    id: "peg",
    title: "Peg insertion",
    question: "Does a near-patch-scale target remain usable through grasp and insertion?",
    src: `${taskMediaRoot}/peg.mp4`,
    poster: "media/video-4k60/peg.jpg",
    playback: "4× edited playback",
    duration: "00:18.2 full edit",
    autonomy: "Autonomous policy rollout",
    coverage: "Multi-position protocol",
    caption: "Complete multi-position edit; closed-loop comparisons use 72 trials per condition.",
    evidenceState: "provided",
  },
  {
    id: "picnic",
    title: "Picnic-bag packing",
    question: "Can one policy switch task-relevant objects across two manipulation stages?",
    src: `${taskMediaRoot}/picnic.mp4`,
    poster: "media/video-4k60/picnic.jpg",
    playback: "4× edited playback",
    duration: "01:12.6 full edit",
    autonomy: "Autonomous policy rollout",
    coverage: "Multi-position protocol",
    caption: "Complete multi-position edit; stage counts use 24 trials.",
    evidenceState: "provided",
  },
  {
    id: "bowl",
    title: "Bowl extraction",
    question: "Can the policy select contact height when RGB appearance is ambiguous?",
    src: `${taskMediaRoot}/bowl.mp4`,
    poster: "media/video-4k60/bowl.jpg",
    playback: "4× edited playback",
    duration: "01:09.4 full edit",
    autonomy: "Autonomous policy rollout",
    coverage: "Multi-position protocol",
    caption: "Complete multi-position edit; matched bowl comparisons use 80 trials per method.",
    evidenceState: "provided",
  },
  {
    id: "cup",
    title: "Cup transfer",
    question: "Can the policy adjust three-dimensional reach across rack configurations?",
    src: `${taskMediaRoot}/cup.mp4`,
    poster: "media/video-4k60/cup.jpg",
    playback: "4× edited playback",
    duration: "00:21.8 full edit",
    autonomy: "Autonomous policy rollout",
    coverage: "Multi-position protocol",
    caption: "Complete multi-position edit; matched cup comparisons use 20 trials per method.",
    evidenceState: "provided",
  },
];

export const positionResults = [
  {
    task: "Placement",
    splitDenominator: 40,
    combinedDenominator: 80,
    anchorCount: 20,
    matchedHead: "ACT",
    rows: [
      { method: "π0.5-FT", seen: 30, heldOut: 28, combined: 58, tone: "reference", group: "system" },
      { method: "Appearance-only ACT", seen: 4, heldOut: 2, combined: 6, tone: "baseline", group: "matched" },
      { method: "Geometry-only ACT", seen: 18, heldOut: 12, combined: 30, tone: "geometry", group: "matched" },
      { method: "StereoPatch-ACT w/o rel. bias", seen: 29, heldOut: 22, combined: 51, tone: "ablation", group: "matched" },
      { method: "StereoPatch-ACT", seen: 34, heldOut: 32, combined: 66, tone: "fusion", group: "matched" },
    ],
  },
  {
    task: "Object picking",
    splitDenominator: 74,
    combinedDenominator: 148,
    anchorCount: 37,
    matchedHead: "DP",
    rows: [
      { method: "π0.5-FT", seen: 62, heldOut: 51, combined: 113, tone: "reference", group: "system" },
      { method: "Appearance-only DP", seen: 19, heldOut: 4, combined: 23, tone: "baseline", group: "matched" },
      { method: "Geometry-only DP", seen: 34, heldOut: 25, combined: 59, tone: "geometry", group: "matched" },
      { method: "StereoPatch-DP w/o rel. bias", seen: 49, heldOut: 32, combined: 81, tone: "ablation", group: "matched" },
      { method: "StereoPatch-DP", seen: 64, heldOut: 59, combined: 123, tone: "fusion", group: "matched" },
      { method: "StereoPatch-ACT", seen: 66, heldOut: 60, combined: 126, tone: "context", group: "context" },
    ],
  },
];

export const simulationTasks = [
  {
    suite: "RoboMimic",
    task: "ToolHang",
    image: "media/simulation/robomimic_tool_hang.png",
    video: "media/simulation/clips/robomimic_tool_hang.mp4",
    sourceUrl: "https://robomimic.github.io/study/",
  },
  {
    suite: "RoboMimic",
    task: "Square",
    image: "media/simulation/robomimic_square.png",
    video: "media/simulation/clips/robomimic_square.mp4",
    sourceUrl: "https://robomimic.github.io/study/",
  },
  {
    suite: "RoboMimic",
    task: "Transport",
    image: "media/simulation/robomimic_transport.png",
    video: "media/simulation/clips/robomimic_transport.mp4",
    sourceUrl: "https://robomimic.github.io/study/",
  },
  {
    suite: "RoboFactory",
    task: "Lift barrier",
    image: "media/simulation/robofactory_lift_barrier.png",
    video: "media/simulation/clips/robofactory_lift_barrier.mp4",
    sourceUrl: "https://iranqin.github.io/robofactory/",
  },
  { suite: "RoboFactory", task: "Camera align.", image: "media/simulation/robofactory_camera_alignment.png" },
  {
    suite: "RoboFactory",
    task: "3-robot stack",
    image: "media/simulation/robofactory_three_robot_stack.png",
    video: "media/simulation/clips/robofactory_three_robot_stack.mp4",
    sourceUrl: "https://iranqin.github.io/robofactory/",
  },
  { suite: "BEHAVIOR-1K", task: "Open door", image: "media/simulation/behavior_open_door.png" },
  { suite: "BEHAVIOR-1K", task: "Turn on radio", image: "media/simulation/behavior_turn_on_radio.png" },
];

export const simulationRows = [
  { perception: "2-D images", groupSpan: 2, method: "RGB-only DP", values: [53, 74, 92, 79, 71, 11, 21, 32], tone: "baseline" },
  { method: "Multi-view RGB DP", values: [54, 78, 92, 69, 64, 36, 23, 27], tone: "baseline" },
  { perception: "RGB-D / 3-D", groupSpan: 3, method: "RGB-D", values: [56, 79, 94, 73, 81, 13, 26, 39], tone: "raw" },
  { method: "RGBD-3DDA", values: [84, 83, 94, 65, 77, 9, 39, 33], tone: "geometry" },
  { method: "PCD-DP3", values: [40, 69, 63, 52, 79, 31, 27, 29], tone: "geometry" },
  { perception: "Stereo RGB", groupSpan: 1, method: "StereoPolicy-DP", values: [94, 88, 94, 84, 89, 28, 41, 42], tone: "reference" },
  { perception: "Patch-aligned RGB-D", groupSpan: 2, method: "StereoPatch-ACT", values: [96, 90, 94, 100, 95, 42, 51, 63], tone: "fusion", proposed: true },
  { method: "StereoPatch-DP", values: [93, 94, 96, 99, 98, 40, 55, 61], tone: "fusion", proposed: true },
];

export const dataEfficiency = [
  {
    id: "placement",
    title: "Placement · StereoPatch-ACT",
    denominator: 40,
    fullAnchors: 20,
    reducedAnchors: 10,
    curves: [
      { method: "π0.5-FT", tone: "reference", coverage: "Full", values: [14, 28, 31] },
      { method: "StereoPatch", tone: "fusion", coverage: "Full", values: [20, 32, 34] },
      { method: "π0.5-FT", tone: "reference", coverage: "Reduced", values: [6, 22, 25] },
      { method: "StereoPatch", tone: "fusion", coverage: "Reduced", values: [12, 27, 29] },
    ],
  },
  {
    id: "picking",
    title: "Picking · StereoPatch-DP",
    denominator: 74,
    fullAnchors: 37,
    reducedAnchors: 19,
    curves: [
      { method: "π0.5-FT", tone: "reference", coverage: "Full", values: [24, 51, 58] },
      { method: "StereoPatch", tone: "fusion", coverage: "Full", values: [33, 59, 62] },
      { method: "π0.5-FT", tone: "reference", coverage: "Reduced", values: [12, 34, 40] },
      { method: "StereoPatch", tone: "fusion", coverage: "Reduced", values: [21, 43, 46] },
    ],
  },
];

export const pegResults = [
  { method: "RGB-only", grid: "10×20", bar: 13, peg: 4, task: 1, tone: "baseline" },
  { method: "RGB-only", grid: "20×40", bar: 17, peg: 6, task: 3, tone: "baseline" },
  { method: "RGB-only", grid: "30×60", bar: 15, peg: 5, task: 2, tone: "baseline" },
  { method: "Geometry-only", grid: "20×40", bar: 27, peg: 22, task: 15, tone: "geometry" },
  { method: "StereoPatch-DP", grid: "10×20", bar: 25, peg: 19, task: 13, tone: "fusion" },
  { method: "StereoPatch-DP", grid: "20×40", bar: 37, peg: 32, task: 26, tone: "fusion", best: true },
  { method: "StereoPatch-DP", grid: "30×60", bar: 30, peg: 24, task: 18, tone: "fusion" },
];

export const picnicResults = [
  { method: "Appearance-only ACT", drink: 10, bread: 3, task: 1, tone: "baseline" },
  { method: "Geometry-only ACT", drink: 8, bread: 5, task: 2, tone: "geometry" },
  { method: "Unbound RGB–D ACT", drink: 11, bread: 4, task: 2, tone: "reference" },
  { method: "StereoPatch-ACT w/o rel. bias", drink: 13, bread: 6, task: 4, tone: "ablation" },
  { method: "StereoPatch-ACT", drink: 15, bread: 8, task: 7, tone: "fusion", best: true },
];

export const metricAmbiguity = [
  { method: "Appearance-only", bowl: 46, empty: 10, multi: 20, cup: 12, tone: "baseline" },
  { method: "Raw RGB-D", bowl: 53, empty: 8, multi: 14, cup: 14, tone: "raw" },
  { method: "Geometry-only", bowl: 56, empty: 7, multi: 12, cup: 13, tone: "geometry" },
  { method: "Unbound RGB–D", bowl: 59, empty: 6, multi: 10, cup: 15, tone: "reference" },
  { method: "StereoPatch w/o rel. bias", bowl: 64, empty: 5, multi: 8, cup: 16, tone: "ablation" },
  { method: "StereoPatch-ACT", bowl: 69, empty: 3, multi: 5, cup: 18, tone: "fusion" },
];

export const latencyBudgets = [
  { group: "Measured components", method: "FastFS network", p50: 4.13, p95: 4.55, budget: "component", status: "component" },
  { group: "Measured components", method: "FastFS full perception", p50: 9.5, p95: 10.39, budget: "component", status: "component" },
  { group: "Measured components", method: "ACT-only", p50: 17.48, p95: 18.41, budget: "component", status: "component" },
  { group: "Measured components", method: "DP · DDIM-4 only", p50: 19.92, p95: 21.71, budget: "component", status: "component" },
  { group: "Measured components", method: "DP · DDIM-8 only", p50: 27.57, p95: 30.57, budget: "component", status: "component" },
  { group: "Measured components", method: "DP · DDIM-16 only", p50: 39.73, p95: 43.04, budget: "component", status: "component" },
  { group: "Componentwise serial estimates", method: "StereoPatch-ACT", p50: 26.98, p95: 28.8, budget: "30 Hz at p95", status: "within-30" },
  { group: "Componentwise serial estimates", method: "StereoPatch-DP · DDIM-4", p50: 29.42, p95: 32.1, budget: "30 Hz at p95", status: "within-30" },
  { group: "Componentwise serial estimates", method: "StereoPatch-DP · DDIM-8", p50: 37.06, p95: 40.96, budget: "20 Hz at p95", status: "within-20" },
  { group: "Componentwise serial estimates", method: "StereoPatch-DP · DDIM-16", p50: 49.23, p95: 53.43, budget: "p95 > 50 ms", status: "over-20" },
  { group: "Separate system reference", method: "π0.5-FT · no FastFS", p50: 61.8, p95: 63.58, budget: "context only", status: "context" },
];
