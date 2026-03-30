#!/usr/bin/env node
/**
 * Plugin Waste Detector - Detect unused Claude plugins by cross-referencing
 * enabledPlugins against project file signals.
 *
 * Usage: node plugin_waste_detector.js [--project-dir path]
 */

const fs = require("fs");
const path = require("path");
const os = require("os");

// Signal map: plugin name -> files/patterns that indicate the plugin is needed
const PLUGIN_SIGNALS = {
  "frontend-design": {
    files: ["package.json", "tsconfig.json", "next.config.js", "next.config.mjs", "vite.config.ts", "vite.config.js"],
    patterns: ["*.tsx", "*.jsx", "*.vue", "*.svelte"],
    description: "Frontend/UI development",
    estimatedTokens: 2000,
  },
  "pyright": {
    files: ["pyproject.toml", "setup.py", "setup.cfg", "requirements.txt", "Pipfile"],
    patterns: ["*.py"],
    description: "Python type checking",
    estimatedTokens: 1500,
  },
  "eslint": {
    files: [".eslintrc.js", ".eslintrc.json", ".eslintrc.yml", ".eslintrc.cjs", "eslint.config.js", "eslint.config.mjs"],
    patterns: ["*.ts", "*.js", "*.tsx", "*.jsx"],
    description: "JavaScript/TypeScript linting",
    estimatedTokens: 1200,
  },
  "prettier": {
    files: [".prettierrc", ".prettierrc.json", ".prettierrc.js", "prettier.config.js"],
    patterns: [],
    description: "Code formatting",
    estimatedTokens: 800,
  },
  "docker": {
    files: ["Dockerfile", "docker-compose.yml", "docker-compose.yaml", ".dockerignore"],
    patterns: ["Dockerfile.*"],
    description: "Docker containerization",
    estimatedTokens: 1500,
  },
  "terraform": {
    files: ["main.tf", "variables.tf", "terraform.tfvars"],
    patterns: ["*.tf"],
    description: "Infrastructure as code",
    estimatedTokens: 2000,
  },
  "prisma": {
    files: ["prisma/schema.prisma"],
    patterns: ["*.prisma"],
    description: "Prisma ORM",
    estimatedTokens: 1500,
  },
  "drizzle": {
    files: ["drizzle.config.ts", "drizzle.config.js"],
    patterns: [],
    description: "Drizzle ORM",
    estimatedTokens: 1500,
  },
  "tailwind": {
    files: ["tailwind.config.js", "tailwind.config.ts", "tailwind.config.cjs"],
    patterns: [],
    description: "Tailwind CSS",
    estimatedTokens: 1000,
  },
  "rust": {
    files: ["Cargo.toml", "Cargo.lock"],
    patterns: ["*.rs"],
    description: "Rust development",
    estimatedTokens: 2000,
  },
  "go": {
    files: ["go.mod", "go.sum"],
    patterns: ["*.go"],
    description: "Go development",
    estimatedTokens: 2000,
  },
  "java": {
    files: ["pom.xml", "build.gradle", "build.gradle.kts"],
    patterns: ["*.java", "*.kt"],
    description: "Java/Kotlin development",
    estimatedTokens: 2000,
  },
  "testing": {
    files: ["jest.config.js", "jest.config.ts", "vitest.config.ts", "pytest.ini", "conftest.py", ".mocharc.yml"],
    patterns: ["*.test.*", "*.spec.*", "test_*.py"],
    description: "Testing frameworks",
    estimatedTokens: 1500,
  },
  "graphql": {
    files: ["schema.graphql", "codegen.yml", "codegen.ts"],
    patterns: ["*.graphql", "*.gql"],
    description: "GraphQL",
    estimatedTokens: 1500,
  },
  "n8n": {
    files: ["governance/n8n-governance"],
    patterns: ["*.n8n.json"],
    description: "n8n workflow automation",
    estimatedTokens: 3000,
  },
};

function parseArgs() {
  const args = { projectDir: process.cwd() };
  const argv = process.argv.slice(2);
  for (let i = 0; i < argv.length; i++) {
    if (argv[i] === "--project-dir" && argv[i + 1]) {
      args.projectDir = path.resolve(argv[i + 1]);
      i++;
    } else if (argv[i] === "--help" || argv[i] === "-h") {
      console.log("Usage: node plugin_waste_detector.js [--project-dir path]");
      process.exit(0);
    }
  }
  return args;
}

function fileExists(dir, filePath) {
  return fs.existsSync(path.join(dir, filePath));
}

function findByPattern(dir, pattern) {
  // Simple glob: convert *.ext to regex, search top-level + src/
  const regex = new RegExp("^" + pattern.replace(/\./g, "\\.").replace(/\*/g, ".*") + "$");
  const dirsToCheck = [dir, path.join(dir, "src"), path.join(dir, "lib"), path.join(dir, "app")];
  for (const d of dirsToCheck) {
    try {
      const entries = fs.readdirSync(d, { withFileTypes: true });
      for (const entry of entries) {
        if (entry.isFile() && regex.test(entry.name)) {
          return true;
        }
      }
    } catch {
      // Directory doesn't exist
    }
  }
  return false;
}

function loadSettings() {
  const settingsPath = path.join(os.homedir(), ".claude", "settings.json");
  try {
    const data = fs.readFileSync(settingsPath, "utf-8");
    return JSON.parse(data);
  } catch {
    return null;
  }
}

function main() {
  const args = parseArgs();
  const settings = loadSettings();

  console.log("=".repeat(70));
  console.log("PLUGIN WASTE DETECTOR");
  console.log("=".repeat(70));
  console.log(`Project: ${args.projectDir}`);

  if (!settings) {
    console.log("\nERROR: Could not read ~/.claude/settings.json");
    process.exit(1);
  }

  const enabledPlugins = settings.enabledPlugins || settings.enabled_plugins || [];
  const permissions = settings.permissions || {};
  // Also check for MCP tools or other plugin indicators
  const allPluginKeys = [...new Set([...enabledPlugins, ...Object.keys(permissions)])];

  if (allPluginKeys.length === 0) {
    console.log("\nNo enabled plugins found in settings.json.");
    console.log("Checked keys: enabledPlugins, enabled_plugins, permissions");
    console.log("\nNote: Your settings.json structure may differ. Available keys:");
    console.log(" ", Object.keys(settings).join(", "));
    process.exit(0);
  }

  console.log(`\nEnabled plugins/permissions: ${allPluginKeys.length}`);
  console.log();

  let totalWaste = 0;
  const needed = [];
  const wasted = [];
  const unknown = [];

  for (const plugin of allPluginKeys) {
    const pluginLower = plugin.toLowerCase();
    // Find matching signal definition
    let signalKey = null;
    for (const [key] of Object.entries(PLUGIN_SIGNALS)) {
      if (pluginLower.includes(key) || key.includes(pluginLower)) {
        signalKey = key;
        break;
      }
    }

    if (!signalKey) {
      unknown.push(plugin);
      continue;
    }

    const signals = PLUGIN_SIGNALS[signalKey];
    let found = false;

    // Check files
    for (const f of signals.files) {
      if (fileExists(args.projectDir, f)) {
        found = true;
        break;
      }
    }

    // Check patterns
    if (!found) {
      for (const p of signals.patterns) {
        if (findByPattern(args.projectDir, p)) {
          found = true;
          break;
        }
      }
    }

    if (found) {
      needed.push({ plugin, signalKey, signals });
    } else {
      wasted.push({ plugin, signalKey, signals });
      totalWaste += signals.estimatedTokens;
    }
  }

  if (needed.length > 0) {
    console.log(`--- NEEDED (${needed.length}) ---`);
    for (const n of needed) {
      console.log(`  OK  ${n.plugin} (${n.signals.description})`);
    }
    console.log();
  }

  if (wasted.length > 0) {
    console.log(`--- WASTED (${wasted.length}) ---`);
    for (const w of wasted) {
      console.log(`  !!  ${w.plugin} (~${w.signals.estimatedTokens} tokens)`);
      console.log(`      ${w.signals.description} - no signal files found`);
      console.log(`      Looked for: ${w.signals.files.slice(0, 3).join(", ")}`);
    }
    console.log();
  }

  if (unknown.length > 0) {
    console.log(`--- UNKNOWN (${unknown.length}) ---`);
    for (const u of unknown) {
      console.log(`  ??  ${u} (no signal map defined)`);
    }
    console.log();
  }

  console.log("-".repeat(70));
  console.log(`Needed: ${needed.length} | Wasted: ${wasted.length} | Unknown: ${unknown.length}`);
  console.log(`Estimated wasted tokens: ${totalWaste.toLocaleString()}`);

  if (wasted.length > 0) {
    console.log("\nTo disable wasted plugins, remove them from ~/.claude/settings.json");
  }
}

main();
