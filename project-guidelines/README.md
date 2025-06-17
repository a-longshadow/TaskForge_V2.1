# TaskForge Project Guidelines & Agreements

**Version:** 1.0  
**Date:** 2024  
**Status:** ACTIVE

## Overview

This folder contains all binding agreements and guidelines for the TaskForge V2.1 project development. All AI agents, developers, and contributors MUST follow these guidelines.

## Structure

```
project-guidelines/
├── README.md                    # This file - overview and index
├── CORE_ARCHITECTURE.md         # Original system architecture (UPDATED for Django)
├── GUARDIAN_SYSTEM.md           # Guardian safeguards and knowledge management
├── MODULAR_DESIGN.md           # Module independence and communication
├── AI_AGENT_PROTOCOLS.md       # AI agent governance and approval gates
├── DEPLOYMENT_STRATEGY.md      # Deployment and rollback procedures (UPDATED for Django)
├── IMPLEMENTATION_PHASES.md    # Staged development approach
├── PROJECT_SKELETON.md         # Complete Django project structure
└── DEVELOPMENT_WORKFLOW.md     # Step-by-step development process
```

## Key Principles

### 1. **Guardian-First Development**
- ALL code changes must go through Guardian system
- Zero regressions tolerance
- Complete AI knowledge persistence across devices/sessions

### 2. **Modular Independence**
- Each stage/module completely unpluggable
- Independent failure isolation
- Event-based communication between modules

### 3. **Final Approval Gate**
- Human approval required for ALL code changes
- Comprehensive impact reports before any modifications
- Auto-Guardian generates reports, waits for explicit approval

### 4. **Knowledge Continuity**
- Living knowledge repository maintained automatically
- AI agent has complete project understanding at all times
- Cross-device migration protocols

## Usage

1. **Before Starting Development:** Read all files in this folder
2. **Before Any Changes:** Validate against these guidelines
3. **During Development:** Reference specific guideline files
4. **After Changes:** Update relevant guideline files if needed

## Compliance

These guidelines are **MANDATORY** for:
- All AI agents working on the project
- All human developers
- All deployment procedures
- All testing protocols

**Violation of these guidelines will result in immediate halt of development activities.** 