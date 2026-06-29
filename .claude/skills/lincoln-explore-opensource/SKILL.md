---
name: lincoln-explore-opensource
description: Use during product design when the requirement can be solved or informed by existing open-source projects.
version: 1.0.0
---

# Lincoln Explore Open Source

## Purpose

Research existing open-source projects that solve a similar problem, score them against Lincoln criteria, and produce a recommendation document.

## When to Use

- `oss-first-design` workflow template is active.
- `product-design-docs` stage identifies a subproblem that could be delegated to an existing library/tool.
- PM says "看看有没有开源方案".

## Inputs

- Requirement keywords
- Target technology stack
- Constraints (license, self-host vs SaaS, language)

## Outputs

- `docs/research/{change_name}-oss-options.md`

## Rules

- Prefer active projects with clear documentation.
- Score on business fit, technical fit, license, maintenance, and integration cost.
- Do not download or execute third-party code.
- Present at least 2 options plus a "build from scratch" baseline.
