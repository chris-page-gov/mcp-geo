import path from "path";
import { fileURLToPath, pathToFileURL } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "../../../..");

export const UI_FILES = [
  "boundary_explorer.html",
  "geography_selector.html",
  "statistics_dashboard.html",
  "simple_map.html",
  "feature_inspector.html",
  "route_planner.html",
];

export function uiFileUrl(name) {
  return pathToFileURL(path.resolve(repoRoot, "ui", name)).href;
}
