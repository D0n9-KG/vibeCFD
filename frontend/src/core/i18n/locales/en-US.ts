import {
  CompassIcon,
  GraduationCapIcon,
  ImageIcon,
  MicroscopeIcon,
  PenLineIcon,
  ShapesIcon,
  SparklesIcon,
  VideoIcon,
} from "lucide-react";

import type { Translations } from "./types";

export const enUS: Translations = {
  // Locale meta
  locale: {
    localName: "English",
  },

  // Common
  common: {
    home: "Home",
    settings: "Settings",
    delete: "Delete",
    rename: "Rename",
    open: "Open",
    share: "Share",
    openInNewWindow: "Open in new window",
    close: "Close",
    more: "More",
    search: "Search",
    download: "Download",
    thinking: "Thinking",
    artifacts: "Artifacts",
    public: "Public",
    custom: "Custom",
    notAvailableInDemoMode: "Not available in demo mode",
    loading: "Loading...",
    version: "Version",
    lastUpdated: "Last updated",
    code: "Code",
    preview: "Preview",
    cancel: "Cancel",
    save: "Save",
    install: "Install",
    create: "Create",
    export: "Export",
    exportAsMarkdown: "Export as Markdown",
    exportAsJSON: "Export as JSON",
    exportSuccess: "Conversation exported",
    messages: "Messages",
    todos: "Todos",
    status: "Status",
    panel: "Panel",
    active: "Active",
    waiting: "Waiting",
    ready: "Ready",
    running: "Running",
    interrupted: "Interrupted",
    done: "Done",
    messageCount: (count: number) => `${count} message${count === 1 ? "" : "s"}`,
    artifactCount: (count: number) => `${count} artifact${count === 1 ? "" : "s"}`,
    todoCount: (count: number) => `${count} todo${count === 1 ? "" : "s"}`,
    threadCount: (count: number) => `${count} thread${count === 1 ? "" : "s"}`,
    agentCount: (count: number) => `${count} agent${count === 1 ? "" : "s"}`,
    toolGroupCount: (count: number) => `${count} tool group${count === 1 ? "" : "s"}`,
  },

  // Welcome
  welcome: {
    greeting: "Hello, again!",
    description:
      "Welcome to VibeCFD, an industrial research workspace for simulation orchestration, evidence delivery, and skill-driven engineering workflows.",

    createYourOwnSkill: "Create Your Own Skill",
    createYourOwnSkillDescription:
      "Create your own skill to extend VibeCFD. Use the Skill Studio workflow to shape reusable domain knowledge, validation rules, and release-ready skill packages.",
  },

  // Clipboard
  clipboard: {
    copyToClipboard: "Copy to clipboard",
    copiedToClipboard: "Copied to clipboard",
    failedToCopyToClipboard: "Failed to copy to clipboard",
    linkCopied: "Link copied to clipboard",
  },

  // Input Box
  inputBox: {
    placeholder: "Enter task requirements, constraints, or collaboration instructions",
    createSkillPrompt:
      "We're going to build a new skill step by step with `skill-creator`. To start, what do you want this skill to do?",
    addAttachments: "Add attachments",
    mode: "Mode",
    flashMode: "Flash",
    flashModeDescription: "Fast and efficient, but may not be accurate",
    reasoningMode: "Reasoning",
    reasoningModeDescription:
      "Reasoning before action, balance between time and accuracy",
    proMode: "Pro",
    proModeDescription:
      "Reasoning, planning and executing, get more accurate results, may take more time",
    ultraMode: "Ultra",
    ultraModeDescription:
      "Pro mode with subagents to divide work; best for complex multi-step tasks",
    reasoningEffort: "Reasoning Effort",
    reasoningEffortMinimal: "Minimal",
    reasoningEffortMinimalDescription: "Retrieval + Direct Output",
    reasoningEffortLow: "Low",
    reasoningEffortLowDescription: "Simple Logic Check + Shallow Deduction",
    reasoningEffortMedium: "Medium",
    reasoningEffortMediumDescription:
      "Multi-layer Logic Analysis + Basic Verification",
    reasoningEffortHigh: "High",
    reasoningEffortHighDescription:
      "Full-dimensional Logic Deduction + Multi-path Verification + Backward Check",
    searchModels: "Search models...",
    surpriseMe: "Surprise",
    surpriseMePrompt: "Surprise me",
    followupLoading: "Generating follow-up questions...",
    followupConfirmTitle: "Send suggestion?",
    followupConfirmDescription:
      "You already have text in the input. Choose how to send it.",
    followupConfirmAppend: "Append & send",
    followupConfirmReplace: "Replace & send",
    suggestions: [
      {
        suggestion: "Write",
        prompt: "Write a blog post about the latest trends on [topic]",
        icon: PenLineIcon,
      },
      {
        suggestion: "Research",
        prompt:
          "Conduct a deep dive research on [topic], and summarize the findings.",
        icon: MicroscopeIcon,
      },
      {
        suggestion: "Collect",
        prompt: "Collect data from [source] and create a report.",
        icon: ShapesIcon,
      },
      {
        suggestion: "Learn",
        prompt: "Learn about [topic] and create a tutorial.",
        icon: GraduationCapIcon,
      },
    ],
    suggestionsCreate: [
      {
        suggestion: "Webpage",
        prompt: "Create a webpage about [topic]",
        icon: CompassIcon,
      },
      {
        suggestion: "Image",
        prompt: "Create an image about [topic]",
        icon: ImageIcon,
      },
      {
        suggestion: "Video",
        prompt: "Create a video about [topic]",
        icon: VideoIcon,
      },
      {
        type: "separator",
      },
      {
        suggestion: "Skill",
        prompt:
          "We're going to build a new skill step by step with `skill-creator`. To start, what do you want this skill to do?",
        icon: SparklesIcon,
      },
    ],
  },

  // Sidebar
  sidebar: {
    newChat: "New chat",
    chats: "Chats",
    recentChats: "Recent chats",
    demoChats: "Demo chats",
    agents: "Agents",
    skillStudio: "Skill Studio",
  },

  // Agents
  agents: {
    title: "Agents",
    description:
      "Keep custom agents inside the same workspace system as simulation, Skill Studio, and chat surfaces.",
    newAgent: "New Agent",
    listDescription:
      "Open a dedicated agent chat or continue refining your current catalog.",
    catalogLabel: "Workspace catalog",
    emptyTitle: "No custom agents yet",
    emptyDescription:
      "Create your first custom agent with a specialized system prompt.",
    chat: "Chat",
    delete: "Delete",
    deleteConfirm:
      "Are you sure you want to delete this agent? This action cannot be undone.",
    deleteSuccess: "Agent deleted",
    newChat: "New chat",
    createPageTitle: "Design your Agent",
    createPageDescription:
      "Move from naming to bootstrap chat inside the same workspace rhythm instead of dropping into a detached setup wizard.",
    buildPathLabel: "Build path",
    createPageSubtitle:
      "Describe the agent you want — I'll help you create it through conversation.",
    nameStepTitle: "Name your new Agent",
    nameStepHint:
      "Letters, digits, and hyphens only — stored lowercase (e.g. code-reviewer)",
    nameStepPlaceholder: "e.g. code-reviewer",
    nameStepContinue: "Continue",
    nameStepInvalidError:
      "Invalid name — use only letters, digits, and hyphens",
    nameStepAlreadyExistsError: "An agent with this name already exists",
    nameStepCheckError: "Could not verify name availability — please try again",
    nameStepBootstrapMessage:
      "The new custom agent name is {name}. Let's bootstrap it's **SOUL**.",
    chatStepNote:
      "Bootstrap the agent in chat, then review the generated result.",
    plannedIdentityLabel: "Planned identity",
    waitingForConfirmedName: "Waiting for a confirmed agent name.",
    bootstrapThreadLabel: "Bootstrap thread",
    agentCreated: "Agent created!",
    startChatting: "Start chatting",
    backToGallery: "Back to agents",
    collaborationDescription:
      "Agent-specific collaboration stays in the main thread while capabilities, status, and recovery actions stay reachable from the shared workspace support panel.",
    profileLabel: "Agent profile",
    profileFallbackDescription:
      "This dedicated agent chat keeps the collaboration surface focused on a single persona and capability envelope.",
    actionsLabel: "Workspace actions",
    sessionSnapshotLabel: "Session snapshot",
    toolGroupsLabel: "Tool groups",
    capabilitiesLabel: "Capabilities",
    agentProfileRefreshError: "The agent profile could not be refreshed.",
  },

  // Breadcrumb
  breadcrumb: {
    workspace: "Workspace",
    chats: "Chats",
  },

  // Workspace
  workspace: {
    officialWebsite: "VibeCFD official website",
    githubTooltip: "View the DeerFlow runtime repository on GitHub",
    settingsAndMore: "Settings and more",
    visitGithub: "View the DeerFlow runtime repository on GitHub",
    reportIssue: "Report a issue",
    contactUs: "Contact us",
    about: "About VibeCFD",
    toggleChatRail: "Toggle chat rail",
    toggleWorkspacePanel: "Toggle workspace panel",
    showWorkspaceViews: "Show workspace views",
    hideWorkspaceViews: "Hide workspace views",
    openGraphFilters: "Open graph filters",
    backToOverview: "Back to overview",
    retryUpdate: "Retry update",
    openRuntimeWorkbench: "Open runtime workbench",
    noArtifactSelectedTitle: "No artifact selected",
    noArtifactSelectedDescription: "Select an artifact to view its details",
  },

  workspaceStates: {
    "first-run": {
      label: "First run",
      title: "No workspace context is ready yet",
      message:
        "Start a new simulation, Skill Studio thread, or conversation to build the first recoverable workspace context.",
    },
    "permissions-error": {
      label: "Permissions error",
      title: "This workspace is missing a required permission",
      message:
        "Review browser, local runtime, or file-access permissions before continuing with the current workflow.",
    },
    "data-interrupted": {
      label: "Data interrupted",
      title: "The latest workspace data is temporarily unavailable",
      message:
        "Keep the current context, then retry the update or return to overview to inspect the latest confirmed state.",
    },
    "update-failed": {
      label: "Update failed",
      title: "The workspace could not refresh this view",
      message:
        "The last available state is still preserved. Retry the update, or return to overview and confirm whether the current object is still running.",
    },
  },

  // Conversation
  conversation: {
    noMessages: "No messages yet",
    startConversation: "Start a conversation to see messages here",
  },

  // Chats
  chats: {
    searchChats: "Search chats",
    overviewDescription:
      "Search, reopen, and continue active conversations without leaving the shared workspace shell.",
    emptySearchTitle: "No matching conversations",
    emptySearchDescription:
      "Try a different keyword or clear the filter to inspect the latest workspace threads.",
    listDescription:
      "Resume a conversation or open a workbench-backed thread from the same shared workspace shell.",
    recentlyUpdated: "Recently updated",
    threadMetaLabel: "Workspace thread",
    threadSummaryDescription:
      "Keep the message flow centered while workspace context and recovery actions stay reachable through the shared support panel.",
    workspaceContextLabel: "Workspace context",
    workspaceContextDescription:
      "Shared conversation controls, runtime handoffs, and quick recovery actions stay here instead of hiding in a separate mini-product shell.",
    runtimeHandoffLabel: "Runtime handoff",
    runtimeHandoffDescription:
      "This thread already carries submarine runtime data or artifacts. Jump straight into the dedicated workbench when you need the live cockpit view.",
    conversationFirstTitle: "Conversation-first surface",
    conversationFirstDescription:
      "When a thread grows into a runtime-backed workflow, the matching workbench entry will appear here instead of forcing the chat view to absorb those controls.",
    sessionSnapshotLabel: "Session snapshot",
  },

  // Page titles (document title)
  pages: {
    appName: "VibeCFD",
    chats: "Chats",
    newChat: "New chat",
    untitled: "Untitled",
  },

  // Tool calls
  toolCalls: {
    moreSteps: (count: number) => `${count} more step${count === 1 ? "" : "s"}`,
    lessSteps: "Less steps",
    executeCommand: "Execute command",
    presentFiles: "Present files",
    needYourHelp: "Need your help",
    useTool: (toolName: string) => `Use "${toolName}" tool`,
    searchFor: (query: string) => `Search for "${query}"`,
    searchForRelatedInfo: "Search for related information",
    searchForRelatedImages: "Search for related images",
    searchForRelatedImagesFor: (query: string) =>
      `Search for related images for "${query}"`,
    searchOnWebFor: (query: string) => `Search on the web for "${query}"`,
    viewWebPage: "View web page",
    listFolder: "List folder",
    readFile: "Read file",
    writeFile: "Write file",
    clickToViewContent: "Click to view file content",
    writeTodos: "Update to-do list",
    skillInstallTooltip: "Install skill and make it available to DeerFlow",
  },

  // Subtasks
  uploads: {
    uploading: "Uploading...",
    uploadingFiles: "Uploading files, please wait...",
  },

  subtasks: {
    subtask: "Subtask",
    executing: (count: number) =>
      `Executing ${count === 1 ? "" : count + " "}subtask${count === 1 ? "" : "s in parallel"}`,
    in_progress: "Running subtask",
    completed: "Subtask completed",
    failed: "Subtask failed",
  },

  // Token Usage
  tokenUsage: {
    title: "Token Usage",
    input: "Input",
    output: "Output",
    total: "Total",
  },
  
  // Shortcuts
  shortcuts: {
    searchActions: "Search actions...",
    noResults: "No results found.",
    actions: "Actions",
    keyboardShortcuts: "Keyboard Shortcuts",
    keyboardShortcutsDescription: "Navigate DeerFlow faster with keyboard shortcuts.",
    openCommandPalette: "Open Command Palette",
    toggleSidebar: "Toggle Sidebar",
  },

  // Settings
  settings: {
    title: "Settings",
    description: "Adjust how VibeCFD looks and behaves for you.",
    sections: {
      appearance: "Appearance",
      memory: "Memory",
      tools: "Tools",
      skills: "Skills",
      notification: "Notification",
      about: "About",
    },
    memory: {
      title: "Memory",
      description:
        "VibeCFD keeps recoverable workspace context in the background so simulation, skill, and chat surfaces stay connected across longer-running work.",
      empty: "No memory data to display.",
      rawJson: "Raw JSON",
      markdown: {
        overview: "Overview",
        userContext: "User context",
        work: "Work",
        personal: "Personal",
        topOfMind: "Top of mind",
        historyBackground: "History",
        recentMonths: "Recent months",
        earlierContext: "Earlier context",
        longTermBackground: "Long-term background",
        updatedAt: "Updated at",
        facts: "Facts",
        empty: "(empty)",
        table: {
          category: "Category",
          confidence: "Confidence",
          confidenceLevel: {
            veryHigh: "Very high",
            high: "High",
            normal: "Normal",
            unknown: "Unknown",
          },
          content: "Content",
          source: "Source",
          createdAt: "CreatedAt",
          view: "View",
        },
      },
    },
    appearance: {
      themeTitle: "Theme",
      themeDescription:
        "Choose how the interface follows your device or stays fixed.",
      system: "System",
      light: "Light",
      dark: "Dark",
      systemDescription: "Match the operating system preference automatically.",
      lightDescription: "Bright palette with higher contrast for daytime.",
      darkDescription: "Dim palette that reduces glare for focus.",
      languageTitle: "Language",
      languageDescription: "Switch between languages.",
    },
    tools: {
      title: "Tools",
      description: "Manage the configuration and enabled status of MCP tools.",
    },
    skills: {
      title: "Agent Skills",
      description:
        "Manage the configuration and enabled status of the agent skills.",
      createSkill: "Create skill",
      emptyTitle: "No agent skill yet",
      emptyDescription:
        "Put your agent skill folders under the `/skills/custom` folder in the VibeCFD root so they can be reviewed inside Skill Studio.",
      emptyButton: "Create Your First Skill",
    },
    notification: {
      title: "Notification",
      description:
        "VibeCFD only sends completion notifications while the window is inactive, which keeps long-running simulation and review work less distracting.",
      requestPermission: "Request notification permission",
      deniedHint:
        "Notification permission was denied. You can enable it in your browser's site settings to receive completion alerts.",
      testButton: "Send test notification",
      testTitle: "VibeCFD",
      testBody: "This is a test notification.",
      notSupported: "Your browser does not support notifications.",
      disableNotification: "Disable notification",
    },
    acknowledge: {
      emptyTitle: "Acknowledgements",
      emptyDescription: "Credits and acknowledgements will show here.",
    },
  },
};
