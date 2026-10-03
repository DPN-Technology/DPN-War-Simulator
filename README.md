<!-- DPN-REPO-HERO:START -->
<p align="center">
  <img src=".github/readme-hero.svg" alt="DPN War Simulator" width="100%">
</p>

<p align="center">
  <img alt="DPN Technology" src="https://img.shields.io/badge/DPN-Technology-111111?style=flat-square&logo=github">
  <img alt="Development" src="https://img.shields.io/badge/Development-Active-FF5A36?style=flat-square">
  <img alt="Organization" src="https://img.shields.io/badge/Organization-DPN--Technology-FF5A36?style=flat-square">
</p>

<!-- DPN-REPO-HERO:END -->

<!-- DPN-LIVE-STATUS:START -->
<p align="center">
  <img alt="Latest release" src="https://img.shields.io/github/v/release/DPN-Technology/DPN-War-Simulator?display_name=tag&sort=semver&style=flat-square&label=release">
  <img alt="Last commit" src="https://img.shields.io/github/last-commit/DPN-Technology/DPN-War-Simulator?style=flat-square&label=last%20commit">
  <img alt="Open issues" src="https://img.shields.io/github/issues/DPN-Technology/DPN-War-Simulator?style=flat-square">
  <img alt="Repository size" src="https://img.shields.io/github/repo-size/DPN-Technology/DPN-War-Simulator?style=flat-square">
</p>
<!-- DPN-LIVE-STATUS:END -->

<!-- DPN-REPO-SHOWCASE:START -->
<p align="center"><img src=".github/repo-showcase.svg" alt="DPN War Simulator capabilities" width="100%"></p>

<p align="center">
  <a href="https://github.com/DPN-Technology/DPN-War-Simulator/releases"><strong>Releases</strong></a>
  &nbsp;•&nbsp;
  <a href="https://github.com/DPN-Technology/DPN-War-Simulator/issues"><strong>Issues</strong></a>
  &nbsp;•&nbsp;
  <a href="https://github.com/DPN-Technology/DPN-War-Simulator/pulls"><strong>Pull Requests</strong></a>
</p>
<!-- DPN-REPO-SHOWCASE:END -->

<!-- DPN-REPO-DETAILS:START -->

## Product Architecture

```mermaid
flowchart LR
  P[Player / Career] --> U[Desktop / UE5 Presentation]
  U --> S[Simulation Systems]
  S --> C[Combat / Ships / Vehicles]
  S --> W[World / AI / Crew]
  S --> D[(Career & Scenario Data)]
  A[3D Asset Pipeline] --> U
```

## Feature Matrix

| Area | What this repository covers |
| --- | --- |
| **Simulation** | First-person, shipboard and large-scale war systems |
| **Naval / Vehicle** | Ship physics, survivability, air and ground operations |
| **Career** | Academy, crew, service record and historical progression |
| **Content Pipeline** | 3D assets, UE5 migration and historical references |

## Visual Evidence

<table>
<tr>
<td align="center"><img src="assets3d/Enterprise_CV6_1942_Midway_preview.png" alt="USS Enterprise preview" width="100%"><br><sub>USS Enterprise preview</sub></td>
<td align="center"><img src="assets3d/Enterprise_CV6_1942_InteriorModules_preview.png" alt="Interior modules preview" width="100%"><br><sub>Interior modules preview</sub></td>
<td align="center"><img src="assets3d/Enterprise_CV6_1942_Midway_top.png" alt="Top profile" width="100%"><br><sub>Top profile</sub></td>
</tr>
</table>

> Visuals above are repository-native assets or verified project captures already committed within the DPN organization. No synthetic runtime screenshot is presented as a real capture.

## Install & Run

| | |
| --- | --- |
| **Primary target** | Windows / UE5 |
| **Fast path** | Use `RUN_GAME.bat` for the current launcher or `OPEN_UE5_PROJECT.bat` for Unreal development. |
| **Setup reference** | [Open setup documentation](START_HERE.txt) |

## Security, Architecture & Release

| Resource | Purpose |
| --- | --- |
| [Security policy](SECURITY.md) | Vulnerability reporting, protected-data guidance and security expectations |
| [Architecture](docs/ARCHITECTURE.md) | System boundaries, major components and engineering model |
| [Release process](RELEASE_PROCESS.md) | How versioned releases are prepared and validated |
| [GitHub Releases](https://github.com/DPN-Technology/DPN-War-Simulator/releases) | Published versions and downloadable release artifacts |

> **Repository presentation rule:** status, release and security claims in this README should stay tied to repository evidence. Visual polish must not imply a capability is production-ready when the underlying project documentation says otherwise.

<!-- DPN-REPO-DETAILS:END -->

<!-- DPN-ECOSYSTEM:START -->

## DPN Ecosystem

**Category:** Simulation & Interactive

[**DPN Tool Die Simulator**](https://github.com/DPN-Technology/DPN-Tool-Die-Simulator) · [**MemeSpace**](https://github.com/DPN-Technology/MemeSpace) · [**DPN Website**](https://github.com/DPN-Technology/DPN-Website)

<details>
<summary><strong>Explore the broader DPN Technology platform</strong></summary>

| Control & Infrastructure | Business Operations | Development & AI | Simulation & Interactive |
| --- | --- | --- | --- |
| [DPN Operational Control](https://github.com/DPN-Technology/DPN-Operational-Control) | [DPN One](https://github.com/DPN-Technology/DPN-One) | [DPN AI](https://github.com/DPN-Technology/DPN-AI) | [DPN War Simulator](https://github.com/DPN-Technology/DPN-War-Simulator) |
| [DPN Executive Control System](https://github.com/DPN-Technology/DPN-Executive-Control-System) | [DPN Human Resources](https://github.com/DPN-Technology/DPN-Human-Resources-Software) | [Death the Developer](https://github.com/DPN-Technology/DPN-Death-the-Developer) | [Tool & Die Simulator](https://github.com/DPN-Technology/DPN-Tool-Die-Simulator) |
| [DPN WatchTower](https://github.com/DPN-Technology/DPN-Watch-Tower) | [DPN Workforce](https://github.com/DPN-Technology/DPN-Workforce-Time-Management-System) | [DPN Website](https://github.com/DPN-Technology/DPN-Website) | [MemeSpace](https://github.com/DPN-Technology/MemeSpace) |
| [DPN Network Mapper](https://github.com/DPN-Technology/DPN-Network-Mapper) | [DPN Service Desk](https://github.com/DPN-Technology/DPN-Service-Desk) | [DPN FiveM Resources](https://github.com/DPN-Technology/DPN-QB-FiveM-Scripts) | [DPN Aqua Labs](https://github.com/DPN-Technology/DPN-Aqua-Labs-Point-of-Sale-System) |

</details>

<!-- DPN-ECOSYSTEM:END -->

<p align="center"><img src="assets/dpn-war-simulator-brand.jpg" alt="DPN War Simulator" width="720"></p>
<h1 align="center">DPN War Simulator</h1>
<p align="center"><strong>Developed by DPN Technology</strong></p>

<p align="center">
  <img alt="Version" src="https://img.shields.io/badge/Version-v2.7-7c3aed?style=for-the-badge">
  <img alt="Status" src="https://img.shields.io/badge/Status-Active%20Development-16a34a?style=for-the-badge">
  <img alt="Repository" src="https://img.shields.io/badge/Repository-Private-111827?style=for-the-badge">
  <img alt="Publisher" src="https://img.shields.io/badge/Publisher-DPN%20Technology-6d28d9?style=for-the-badge">
  <a href="https://github.com/DPN-Technology/DPN-War-Simulator/actions/workflows/ci.yml"><img alt="CI" src="https://img.shields.io/badge/CI-Automated-2563eb?style=for-the-badge"></a>
</p>

> **Release:** v2.7  
> **Focus:** Large-scale 3D war simulation · First-person gameplay · Ships · Vehicles · Open-world systems

[Overview](#overview) · [Development Priorities](#development-priorities) · [Architecture](docs/ARCHITECTURE.md) · [Roadmap](ROADMAP.md) · [Release Notes](RELEASE_NOTES.md) · [Security](SECURITY.md) · [Contributing](CONTRIBUTING.md)

## Overview

DPN War Simulator is DPN Technology's large-scale 3D war simulation project focused on immersive first-person gameplay, realistic vehicles and ships, seamless environments, combat systems, damage simulation, AI, and an expanding open world.

The project is being developed as a simulation platform rather than a collection of disconnected scenes. The long-term architecture is intended to support continuous traversal, interactive ship interiors, physical movement, vehicle systems, combat, crew/AI behavior, world simulation, and production-quality assets in one cohesive runtime.

## Development Priorities

- Realistic environments and production-quality 3D assets
- Seamless traversal through ships, decks, rooms, and world spaces
- Advanced ship and vehicle physics
- First-person interaction and combat systems
- AI, damage, crew, and world simulation
- Performance profiling and optimization
- Automated simulation tests and asset-pipeline validation
- Reproducible releases, CI, SBOMs, and supply-chain evidence

## Engineering & Validation

The repository includes automated GitHub Actions validation for Python compilation, simulation tests, and the 3D asset pipeline. The asset-pipeline job validates core dependencies such as NumPy, trimesh, Pillow, and Matplotlib by creating test geometry and rendered assets during CI.

Development changes should preserve testability and avoid committing runtime credentials, generated secrets, databases, or other machine-local state.

## Release v2.7

The current GitHub release is **v2.7**. Release automation publishes the source archive and supporting integrity/supply-chain artifacts, including release manifests, dependency inventory, checksums, and SBOM data.

## Project Documentation

Detailed project information is maintained in the repository documentation:

- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — system and gameplay architecture
- [`docs/README.md`](docs/README.md) — documentation index
- [`ROADMAP.md`](ROADMAP.md) — development roadmap
- [`RELEASE_NOTES.md`](RELEASE_NOTES.md) — release history and current release notes
- [`SECURITY.md`](SECURITY.md) — security reporting and project security expectations
- [`CONTRIBUTING.md`](CONTRIBUTING.md) — development contribution standards
- [`SUPPLY_CHAIN.md`](SUPPLY_CHAIN.md) — software supply-chain controls
- [`PORTFOLIO.md`](PORTFOLIO.md) — connected DPN Technology software portfolio

## Repository Standards

This project follows the broader DPN repository baseline: controlled releases, automated CI, issue/PR workflows, security documentation, architecture documentation, release history, supply-chain evidence, and product-specific branding.

---

<p align="center"><strong>DPN Technology</strong><br>We Develop what doesn't exist. We Pioneer what comes next. We Navigate the future.</p>
