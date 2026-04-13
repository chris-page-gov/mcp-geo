# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Purpose

This is a hackathon workspace for the AI Engineering Lab. Individual projects are added here as hackathon work progresses.

## Claude API Configuration

This workspace is pre-configured (via `.claude/settings.local.json`, which is gitignored) to use a custom Anthropic proxy endpoint at `https://licenseportal.aiengineeringlab.co.uk` with European-region model variants. When building applications that call the Claude API directly, use these model IDs:

| Tier   | Model ID                                  |
|--------|-------------------------------------------|
| Sonnet | `eu.anthropic.claude-sonnet-4-6`          |
| Haiku  | `eu.anthropic.claude-haiku-4-5-20251001-v1:0` |
| Opus   | `eu.anthropic.claude-opus-4-6-v1`         |

The `ANTHROPIC_BASE_URL` and `ANTHROPIC_AUTH_TOKEN` environment variables are injected automatically from `.claude/settings.local.json` — no manual export needed when running commands through Claude Code.
