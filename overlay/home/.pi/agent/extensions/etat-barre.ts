// Note dans la barre quickshell si pi travaille : running au début d'un tour, done quand il est au repos.
import { spawn } from "node:child_process";
import { homedir } from "node:os";
import { join } from "node:path";

const script = join(homedir(), ".config/quickshell/ii/scripts/claude/agent-state.sh");

function noter(etat: string) {
  spawn(script, [etat], { stdio: "ignore", detached: false }).on("error", () => {});
}

export default function (pi: any) {
  pi.on("agent_start", () => noter("running"));
  pi.on("agent_settled", () => noter("done"));
}
