#!/usr/bin/env node

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import { z } from "zod";

// Configuration
const config = {
  host: process.env.JIRA_HOST || "",
  email: process.env.JIRA_EMAIL || "",
  apiToken: process.env.JIRA_API_TOKEN || "",
  personalAccessToken: process.env.JIRA_PERSONAL_ACCESS_TOKEN || "",
  usePAT: process.env.JIRA_USE_PAT === "true",
  defaultProject: process.env.JIRA_DEFAULT_PROJECT || "",
};

// Validate configuration
if (!config.host) {
  throw new Error("JIRA_HOST is required");
}

if (!config.usePAT && (!config.email || !config.apiToken)) {
  throw new Error("JIRA_EMAIL and JIRA_API_TOKEN are required for Cloud");
}

if (config.usePAT && !config.personalAccessToken) {
  throw new Error("JIRA_PERSONAL_ACCESS_TOKEN is required when JIRA_USE_PAT=true");
}

// Base URL
const baseUrl = config.host.startsWith("http")
  ? config.host
  : `https://${config.host}`;

// Auth header
function getAuthHeader(): string {
  if (config.usePAT) {
    return `Bearer ${config.personalAccessToken}`;
  }
  const credentials = Buffer.from(`${config.email}:${config.apiToken}`).toString(
    "base64"
  );
  return `Basic ${credentials}`;
}

// API request helper
async function jiraRequest<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${baseUrl}/rest/api/3${endpoint}`;

  const response = await fetch(url, {
    ...options,
    headers: {
      Authorization: getAuthHeader(),
      "Content-Type": "application/json",
      Accept: "application/json",
      ...options.headers,
    },
  });

  if (!response.ok) {
    const error = await response.text();
    throw new Error(`Jira API error (${response.status}): ${error}`);
  }

  if (response.status === 204) {
    return {} as T;
  }

  return response.json();
}

// Agile API request helper
async function agileRequest<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${baseUrl}/rest/agile/1.0${endpoint}`;

  const response = await fetch(url, {
    ...options,
    headers: {
      Authorization: getAuthHeader(),
      "Content-Type": "application/json",
      Accept: "application/json",
      ...options.headers,
    },
  });

  if (!response.ok) {
    const error = await response.text();
    throw new Error(`Jira Agile API error (${response.status}): ${error}`);
  }

  return response.json();
}

// Input schemas
const IssueKeySchema = z.object({
  issueKey: z.string().describe("Issue key (e.g., PROJ-123)"),
});

const SearchSchema = z.object({
  jql: z.string().describe("JQL query"),
  maxResults: z.number().default(50).describe("Maximum results to return"),
  fields: z
    .array(z.string())
    .optional()
    .describe("Fields to include in response"),
});

const CreateIssueSchema = z.object({
  project: z.string().describe("Project key"),
  issueType: z.string().describe("Issue type (Bug, Task, Story, etc.)"),
  summary: z.string().describe("Issue summary/title"),
  description: z.string().optional().describe("Issue description"),
  priority: z.string().optional().describe("Priority name"),
  labels: z.array(z.string()).optional().describe("Labels"),
  assignee: z.string().optional().describe("Assignee account ID"),
});

const UpdateIssueSchema = z.object({
  issueKey: z.string(),
  summary: z.string().optional(),
  description: z.string().optional(),
  priority: z.string().optional(),
  labels: z.array(z.string()).optional(),
  assignee: z.string().optional(),
});

const TransitionSchema = z.object({
  issueKey: z.string(),
  transition: z.string().describe("Transition name or ID"),
});

const CommentSchema = z.object({
  issueKey: z.string(),
  body: z.string().describe("Comment body (supports Jira markdown)"),
});

const ProjectSchema = z.object({
  projectKey: z.string(),
});

const SprintSchema = z.object({
  boardId: z.number(),
  state: z.enum(["active", "future", "closed"]).default("active"),
});

const AssignSchema = z.object({
  issueKey: z.string(),
  assignee: z.string().describe("Account ID, email, or 'unassigned'"),
});

// Create MCP server
const server = new Server(
  {
    name: "jira-bridge",
    version: "1.0.0",
  },
  {
    capabilities: {
      tools: {},
    },
  }
);

// List available tools
server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: [
    {
      name: "get_issue",
      description: "Get details of a Jira issue by its key",
      inputSchema: {
        type: "object",
        properties: {
          issueKey: {
            type: "string",
            description: "Issue key (e.g., PROJ-123)",
          },
        },
        required: ["issueKey"],
      },
    },
    {
      name: "search_issues",
      description: "Search for Jira issues using JQL",
      inputSchema: {
        type: "object",
        properties: {
          jql: { type: "string", description: "JQL query" },
          maxResults: {
            type: "number",
            description: "Maximum results (default: 50)",
          },
          fields: {
            type: "array",
            items: { type: "string" },
            description: "Fields to include",
          },
        },
        required: ["jql"],
      },
    },
    {
      name: "create_issue",
      description: "Create a new Jira issue",
      inputSchema: {
        type: "object",
        properties: {
          project: { type: "string", description: "Project key" },
          issueType: {
            type: "string",
            description: "Issue type (Bug, Task, Story, etc.)",
          },
          summary: { type: "string", description: "Issue title" },
          description: { type: "string", description: "Issue description" },
          priority: { type: "string", description: "Priority name" },
          labels: {
            type: "array",
            items: { type: "string" },
            description: "Labels",
          },
          assignee: { type: "string", description: "Assignee account ID" },
        },
        required: ["project", "issueType", "summary"],
      },
    },
    {
      name: "update_issue",
      description: "Update an existing Jira issue",
      inputSchema: {
        type: "object",
        properties: {
          issueKey: { type: "string", description: "Issue key" },
          summary: { type: "string" },
          description: { type: "string" },
          priority: { type: "string" },
          labels: { type: "array", items: { type: "string" } },
          assignee: { type: "string" },
        },
        required: ["issueKey"],
      },
    },
    {
      name: "transition_issue",
      description: "Transition an issue to a new status",
      inputSchema: {
        type: "object",
        properties: {
          issueKey: { type: "string", description: "Issue key" },
          transition: {
            type: "string",
            description: "Transition name or ID",
          },
        },
        required: ["issueKey", "transition"],
      },
    },
    {
      name: "add_comment",
      description: "Add a comment to an issue",
      inputSchema: {
        type: "object",
        properties: {
          issueKey: { type: "string", description: "Issue key" },
          body: {
            type: "string",
            description: "Comment body (supports Jira markdown)",
          },
        },
        required: ["issueKey", "body"],
      },
    },
    {
      name: "get_transitions",
      description: "Get available workflow transitions for an issue",
      inputSchema: {
        type: "object",
        properties: {
          issueKey: { type: "string", description: "Issue key" },
        },
        required: ["issueKey"],
      },
    },
    {
      name: "get_project",
      description: "Get project details",
      inputSchema: {
        type: "object",
        properties: {
          projectKey: { type: "string", description: "Project key" },
        },
        required: ["projectKey"],
      },
    },
    {
      name: "get_sprint",
      description: "Get sprint information for a board",
      inputSchema: {
        type: "object",
        properties: {
          boardId: { type: "number", description: "Board ID" },
          state: {
            type: "string",
            enum: ["active", "future", "closed"],
            description: "Sprint state filter",
          },
        },
        required: ["boardId"],
      },
    },
    {
      name: "assign_issue",
      description: "Assign an issue to a user",
      inputSchema: {
        type: "object",
        properties: {
          issueKey: { type: "string", description: "Issue key" },
          assignee: {
            type: "string",
            description: "Account ID, email, or 'unassigned'",
          },
        },
        required: ["issueKey", "assignee"],
      },
    },
  ],
}));

// Handle tool calls
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  try {
    switch (name) {
      case "get_issue": {
        const { issueKey } = IssueKeySchema.parse(args);
        const issue = await jiraRequest<Record<string, unknown>>(
          `/issue/${issueKey}?expand=transitions`
        );

        // Simplify response
        const fields = issue.fields as Record<string, unknown>;
        return {
          content: [
            {
              type: "text",
              text: JSON.stringify(
                {
                  key: issue.key,
                  summary: fields.summary,
                  status: (fields.status as Record<string, unknown>)?.name,
                  type: (fields.issuetype as Record<string, unknown>)?.name,
                  priority: (fields.priority as Record<string, unknown>)?.name,
                  assignee: (fields.assignee as Record<string, unknown>)
                    ?.displayName,
                  reporter: (fields.reporter as Record<string, unknown>)
                    ?.displayName,
                  created: fields.created,
                  updated: fields.updated,
                  description: fields.description,
                  labels: fields.labels,
                },
                null,
                2
              ),
            },
          ],
        };
      }

      case "search_issues": {
        const { jql, maxResults, fields } = SearchSchema.parse(args);

        const result = await jiraRequest<{
          issues: Array<{
            key: string;
            fields: Record<string, unknown>;
          }>;
          total: number;
        }>("/search", {
          method: "POST",
          body: JSON.stringify({
            jql,
            maxResults,
            fields: fields || [
              "summary",
              "status",
              "priority",
              "assignee",
              "issuetype",
            ],
          }),
        });

        const simplified = result.issues.map((issue) => ({
          key: issue.key,
          summary: issue.fields.summary,
          status: (issue.fields.status as Record<string, unknown>)?.name,
          type: (issue.fields.issuetype as Record<string, unknown>)?.name,
          priority: (issue.fields.priority as Record<string, unknown>)?.name,
          assignee: (issue.fields.assignee as Record<string, unknown>)
            ?.displayName,
        }));

        return {
          content: [
            {
              type: "text",
              text: JSON.stringify(
                {
                  total: result.total,
                  returned: simplified.length,
                  issues: simplified,
                },
                null,
                2
              ),
            },
          ],
        };
      }

      case "create_issue": {
        const input = CreateIssueSchema.parse(args);

        const issueData: Record<string, unknown> = {
          fields: {
            project: { key: input.project },
            issuetype: { name: input.issueType },
            summary: input.summary,
          },
        };

        const fields = issueData.fields as Record<string, unknown>;

        if (input.description) {
          fields.description = {
            type: "doc",
            version: 1,
            content: [
              {
                type: "paragraph",
                content: [{ type: "text", text: input.description }],
              },
            ],
          };
        }

        if (input.priority) {
          fields.priority = { name: input.priority };
        }

        if (input.labels) {
          fields.labels = input.labels;
        }

        if (input.assignee) {
          fields.assignee = { accountId: input.assignee };
        }

        const result = await jiraRequest<{ key: string; self: string }>(
          "/issue",
          {
            method: "POST",
            body: JSON.stringify(issueData),
          }
        );

        return {
          content: [
            {
              type: "text",
              text: JSON.stringify(
                {
                  created: true,
                  key: result.key,
                  url: `${baseUrl}/browse/${result.key}`,
                },
                null,
                2
              ),
            },
          ],
        };
      }

      case "update_issue": {
        const input = UpdateIssueSchema.parse(args);

        const updateData: { fields: Record<string, unknown> } = { fields: {} };

        if (input.summary) {
          updateData.fields.summary = input.summary;
        }

        if (input.description) {
          updateData.fields.description = {
            type: "doc",
            version: 1,
            content: [
              {
                type: "paragraph",
                content: [{ type: "text", text: input.description }],
              },
            ],
          };
        }

        if (input.priority) {
          updateData.fields.priority = { name: input.priority };
        }

        if (input.labels) {
          updateData.fields.labels = input.labels;
        }

        if (input.assignee) {
          updateData.fields.assignee = { accountId: input.assignee };
        }

        await jiraRequest(`/issue/${input.issueKey}`, {
          method: "PUT",
          body: JSON.stringify(updateData),
        });

        return {
          content: [
            {
              type: "text",
              text: JSON.stringify(
                {
                  updated: true,
                  key: input.issueKey,
                  url: `${baseUrl}/browse/${input.issueKey}`,
                },
                null,
                2
              ),
            },
          ],
        };
      }

      case "transition_issue": {
        const { issueKey, transition } = TransitionSchema.parse(args);

        // Get available transitions
        const transitions = await jiraRequest<{
          transitions: Array<{ id: string; name: string }>;
        }>(`/issue/${issueKey}/transitions`);

        // Find matching transition
        const match = transitions.transitions.find(
          (t) =>
            t.id === transition ||
            t.name.toLowerCase() === transition.toLowerCase()
        );

        if (!match) {
          return {
            content: [
              {
                type: "text",
                text: JSON.stringify(
                  {
                    error: "Transition not found",
                    available: transitions.transitions.map((t) => ({
                      id: t.id,
                      name: t.name,
                    })),
                  },
                  null,
                  2
                ),
              },
            ],
            isError: true,
          };
        }

        await jiraRequest(`/issue/${issueKey}/transitions`, {
          method: "POST",
          body: JSON.stringify({ transition: { id: match.id } }),
        });

        return {
          content: [
            {
              type: "text",
              text: JSON.stringify(
                {
                  transitioned: true,
                  key: issueKey,
                  to: match.name,
                },
                null,
                2
              ),
            },
          ],
        };
      }

      case "add_comment": {
        const { issueKey, body } = CommentSchema.parse(args);

        await jiraRequest(`/issue/${issueKey}/comment`, {
          method: "POST",
          body: JSON.stringify({
            body: {
              type: "doc",
              version: 1,
              content: [
                {
                  type: "paragraph",
                  content: [{ type: "text", text: body }],
                },
              ],
            },
          }),
        });

        return {
          content: [
            {
              type: "text",
              text: JSON.stringify(
                {
                  added: true,
                  key: issueKey,
                },
                null,
                2
              ),
            },
          ],
        };
      }

      case "get_transitions": {
        const { issueKey } = IssueKeySchema.parse(args);

        const result = await jiraRequest<{
          transitions: Array<{ id: string; name: string; to: { name: string } }>;
        }>(`/issue/${issueKey}/transitions`);

        return {
          content: [
            {
              type: "text",
              text: JSON.stringify(
                {
                  issueKey,
                  transitions: result.transitions.map((t) => ({
                    id: t.id,
                    name: t.name,
                    toStatus: t.to.name,
                  })),
                },
                null,
                2
              ),
            },
          ],
        };
      }

      case "get_project": {
        const { projectKey } = ProjectSchema.parse(args);

        const project = await jiraRequest<Record<string, unknown>>(
          `/project/${projectKey}`
        );

        return {
          content: [
            {
              type: "text",
              text: JSON.stringify(
                {
                  key: project.key,
                  name: project.name,
                  description: project.description,
                  lead: (project.lead as Record<string, unknown>)?.displayName,
                  issueTypes: (project.issueTypes as Array<Record<string, unknown>>)?.map(
                    (t) => t.name
                  ),
                },
                null,
                2
              ),
            },
          ],
        };
      }

      case "get_sprint": {
        const { boardId, state } = SprintSchema.parse(args);

        const result = await agileRequest<{
          values: Array<{
            id: number;
            name: string;
            state: string;
            startDate: string;
            endDate: string;
            goal: string;
          }>;
        }>(`/board/${boardId}/sprint?state=${state}`);

        return {
          content: [
            {
              type: "text",
              text: JSON.stringify(
                {
                  boardId,
                  sprints: result.values.map((s) => ({
                    id: s.id,
                    name: s.name,
                    state: s.state,
                    startDate: s.startDate,
                    endDate: s.endDate,
                    goal: s.goal,
                  })),
                },
                null,
                2
              ),
            },
          ],
        };
      }

      case "assign_issue": {
        const { issueKey, assignee } = AssignSchema.parse(args);

        const accountId = assignee === "unassigned" ? null : assignee;

        await jiraRequest(`/issue/${issueKey}/assignee`, {
          method: "PUT",
          body: JSON.stringify({ accountId }),
        });

        return {
          content: [
            {
              type: "text",
              text: JSON.stringify(
                {
                  assigned: true,
                  key: issueKey,
                  assignee: accountId || "unassigned",
                },
                null,
                2
              ),
            },
          ],
        };
      }

      default:
        return {
          content: [{ type: "text", text: `Unknown tool: ${name}` }],
          isError: true,
        };
    }
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    return {
      content: [{ type: "text", text: `Error: ${message}` }],
      isError: true,
    };
  }
});

// Start server
async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("Jira Bridge MCP server started");
}

main().catch((error) => {
  console.error("Failed to start server:", error);
  process.exit(1);
});
