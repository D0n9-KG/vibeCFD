import fs from "node:fs/promises";
import os from "node:os";
import path from "node:path";

import type { Model } from "@/core/models/types";

type RawConfigModel = Partial<Model> & {
  use?: string;
};

const CONFIG_PATH = path.resolve(process.cwd(), "..", "config.yaml");

function stripInlineComment(line: string) {
  let quotedBy: '"' | "'" | null = null;
  let result = "";

  for (let index = 0; index < line.length; index += 1) {
    const char = line[index];
    const previous = index > 0 ? line[index - 1] : "";

    if ((char === '"' || char === "'") && previous !== "\\") {
      if (quotedBy === char) {
        quotedBy = null;
      } else {
        quotedBy ??= char;
      }
    }

    if (char === "#" && quotedBy === null) {
      break;
    }

    result += char;
  }

  return result.trimEnd();
}

function parseScalar(rawValue: string) {
  const value = rawValue.trim();
  if (value === "true") return true;
  if (value === "false") return false;
  if (
    (value.startsWith('"') && value.endsWith('"')) ||
    (value.startsWith("'") && value.endsWith("'"))
  ) {
    return value.slice(1, -1);
  }
  if (value === "null") {
    return null;
  }
  return value;
}

function parseModelsBlock(source: string): RawConfigModel[] {
  const lines = source.split(/\r?\n/);
  const models: RawConfigModel[] = [];
  let inModels = false;
  let currentModel: RawConfigModel | null = null;

  const flush = () => {
    if (!currentModel?.name || !currentModel.model) {
      currentModel = null;
      return;
    }

    models.push({
      id: currentModel.name,
      name: currentModel.name,
      model: currentModel.model,
      display_name: currentModel.display_name ?? currentModel.name,
      description: currentModel.description ?? null,
      supports_thinking:
        typeof currentModel.supports_thinking === "boolean"
          ? currentModel.supports_thinking
          : false,
      supports_reasoning_effort:
        typeof currentModel.supports_reasoning_effort === "boolean"
          ? currentModel.supports_reasoning_effort
          : false,
      use: currentModel.use,
    });
    currentModel = null;
  };

  for (const rawLine of lines) {
    const line = stripInlineComment(rawLine);
    const trimmed = line.trim();

    if (!inModels) {
      if (trimmed === "models:") {
        inModels = true;
      }
      continue;
    }

    if (!trimmed) {
      continue;
    }

    const indent = (/^ */.exec(rawLine))?.[0].length ?? 0;
    if (indent === 0) {
      flush();
      break;
    }

    if (trimmed.startsWith("- ")) {
      flush();
      currentModel = {};

      const entry = trimmed.slice(2);
      const separatorIndex = entry.indexOf(":");
      if (separatorIndex === -1) {
        continue;
      }

      const key = entry.slice(0, separatorIndex).trim();
      const value = entry.slice(separatorIndex + 1).trim();
      if (value.length > 0) {
        currentModel[key as keyof RawConfigModel] =
          parseScalar(value) as never;
      }
      continue;
    }

    if (currentModel == null || indent < 4) {
      continue;
    }

    const separatorIndex = trimmed.indexOf(":");
    if (separatorIndex === -1) {
      continue;
    }

    const key = trimmed.slice(0, separatorIndex).trim();
    const value = trimmed.slice(separatorIndex + 1).trim();
    if (value.length === 0) {
      continue;
    }

    currentModel[key as keyof RawConfigModel] = parseScalar(value) as never;
  }

  flush();
  return models;
}

async function readJSONFile(filePath: string) {
  try {
    const raw = await fs.readFile(filePath, "utf8");
    return JSON.parse(raw) as Record<string, unknown>;
  } catch {
    return null;
  }
}

async function loadOpenAICredential() {
  const envKey = process.env.OPENAI_API_KEY?.trim();
  if (envKey) {
    return true;
  }

  const authPath =
    process.env.CODEX_AUTH_PATH?.trim() ??
    path.join(os.homedir(), ".codex", "auth.json");
  const authData = await readJSONFile(authPath);
  if (!authData) {
    return false;
  }

  const authKey =
    typeof authData.OPENAI_API_KEY === "string"
      ? authData.OPENAI_API_KEY
      : typeof authData.openai_api_key === "string"
        ? authData.openai_api_key
        : "";

  return authKey.trim().length > 0;
}

async function loadClaudeCredential() {
  if (process.env.ANTHROPIC_API_KEY?.trim()) {
    return true;
  }

  const credentialsPath =
    process.env.CLAUDE_CODE_CREDENTIALS_PATH?.trim() ??
    path.join(os.homedir(), ".claude", ".credentials.json");
  const credentials = await readJSONFile(credentialsPath);
  const oauth =
    credentials &&
    typeof credentials.claudeAiOauth === "object" &&
    credentials.claudeAiOauth !== null
      ? (credentials.claudeAiOauth as Record<string, unknown>)
      : null;

  if (oauth && typeof oauth.accessToken === "string" && oauth.accessToken.trim()) {
    return true;
  }

  const settingsPath = path.join(os.homedir(), ".claude", "settings.json");
  const settings = await readJSONFile(settingsPath);
  const env =
    settings && typeof settings.env === "object" && settings.env !== null
      ? (settings.env as Record<string, unknown>)
      : null;
  const token =
    typeof env?.CLAUDE_CODE_OAUTH_TOKEN === "string"
      ? env.CLAUDE_CODE_OAUTH_TOKEN
      : typeof env?.ANTHROPIC_AUTH_TOKEN === "string"
        ? env.ANTHROPIC_AUTH_TOKEN
        : "";

  return token.trim().length > 0;
}

async function applyAvailability(models: RawConfigModel[]): Promise<Model[]> {
  const openAIAvailable = await loadOpenAICredential();
  const claudeAvailable = await loadClaudeCredential();

  return models.map((model) => {
    if (model.use?.startsWith("deerflow.models.openai_cli_provider:")) {
      return {
        ...model,
        is_available: openAIAvailable,
        availability_reason: openAIAvailable
          ? null
          : "OpenAI / Codex API credentials are not configured in this environment.",
      } as Model;
    }

    if (
      model.use?.startsWith("deerflow.models.claude_provider:") ||
      model.use?.startsWith("langchain_anthropic:")
    ) {
      return {
        ...model,
        is_available: claudeAvailable,
        availability_reason: claudeAvailable
          ? null
          : "Anthropic / Claude credentials are not configured in this environment.",
      } as Model;
    }

    return {
      ...model,
      is_available: true,
      availability_reason: null,
    } as Model;
  });
}

function fallbackModels(): RawConfigModel[] {
  return [
    {
      id: "gpt-5.4",
      name: "gpt-5.4",
      model: "gpt-5.4",
      display_name: "GPT-5.4 (Codex / OpenAI)",
      supports_thinking: true,
      supports_reasoning_effort: true,
      use: "deerflow.models.openai_cli_provider:OpenAICliChatModel",
    },
    {
      id: "claude-sonnet-4-6",
      name: "claude-sonnet-4-6",
      model: "claude-sonnet-4-6",
      display_name: "Claude Sonnet 4.6",
      supports_thinking: true,
      supports_reasoning_effort: false,
      use: "deerflow.models.claude_provider:ClaudeChatModel",
    },
  ];
}

export async function loadConfiguredModels(): Promise<Model[]> {
  try {
    const source = await fs.readFile(CONFIG_PATH, "utf8");
    const parsedModels = parseModelsBlock(source);
    if (parsedModels.length > 0) {
      return applyAvailability(parsedModels);
    }
  } catch {
    // Fall through to the hard-coded fallback that mirrors the checked-in config.
  }

  return applyAvailability(fallbackModels());
}

export function parseModelsFromSource(source: string) {
  return parseModelsBlock(source);
}
