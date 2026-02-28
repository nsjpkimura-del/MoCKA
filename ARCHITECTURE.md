# MoCKA Architecture Overview

## High-Level Architecture

```mermaid
flowchart TB
    A["INFIELD - Local Sovereign Memory"] -->|Deterministic Phase Data| B["SHA256 Chain"]
    B --> C["Ed25519 Governance"]
    C --> D["Multi-Observer Layer"]

    D --> E["F Node - Continuous"]
    D --> F["J Node - Cold Storage"]
    D --> G["SYSTEM Node - Autonomous"]

    A --> H["OUTFIELD Sync Layer"]
    H --> I["Time-Series Index"]
    H --> J["Cross-Agent Protocol"]

    B --> K["RFC3161 Timestamp Authority"]
    K --> L["Transparency Repo"]
Layer Description
INFIELD

Primary structured records and deterministic reconstruction.

OUTFIELD

Cross-agent synchronization layer.

Audit Backbone

Append-only SHA256 chain with Ed25519 governance.

Observer Layer

Continuous, cold-storage, and autonomous verification nodes.

Transparency

Public proof repository with reproducible verification.
