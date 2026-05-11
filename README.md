# Minecraft ModPack CLI
## Enhance your ModPack creation with a simple CLI tool

<div align="center">
    <img alt="license" title="License" src="https://custom-icon-badges.demolab.com/github/license/Dtar380/MinecraftModpackCLI?style=for-the-badge&logo=law&logoColor=white&labelColor=1155BA&color=236AD3" height=30>
    <img alt="stars" title="stars" src="https://custom-icon-badges.demolab.com/github/stars/Dtar380/MinecraftModpackCLI?style=for-the-badge&logo=star&logoColor=white&label=STARS&labelColor=9133D4&color=A444E0" height=30>
    <img alt="downloads" title="downloads" src="https://img.shields.io/pypi/dm/minecraftmodpackCLI?style=for-the-badge&logo=download&logoColor=white&label=Downloads&labelColor=488207&color=55960C" height=30>
    <img alt="open issues" title="open issues" src="https://custom-icon-badges.demolab.com/github/issues/Dtar380/MinecraftModpackCLI?style=for-the-badge&logo=issue-opened&logoColor=white&label=open%20issues&labelColor=CE4630&color=E05D44" height=30>
</div>

**Minecraft ModPack CLI** is a Python CLI to help you build, validate, and export Minecraft modpacks from a local mods folder.
It uses Modrinth metadata to resolve dependencies, creates manifests, and can download missing mods when exporting or building.

<!-- omit in toc -->
## :bookmark_tabs: **Table of Contents**
- [Minecraft ModPack CLI](#minecraft-modpack-cli)
  - [Enhance your ModPack creation with a simple CLI tool](#enhance-your-modpack-creation-with-a-simple-cli-tool)
  - [:blue\_heart: **Main Features**](#blue_heart-main-features)
  - [:arrow\_down: **Installation**](#arrow_down-installation)
  - [:rocket: Quick start](#rocket-quick-start)
  - [:wrench: **Tips \& Troubleshooting**](#wrench-tips--troubleshooting)
  - [:memo:  **Working On**](#memo--working-on)
  - [:open\_file\_folder: **Kown Issues**](#open_file_folder-kown-issues)
  - [:scroll: **License**](#scroll-license)
  - [:money\_with\_wings: **Sponsorship**](#money_with_wings-sponsorship)

## :blue_heart: **Main Features**
- **Resolve Modrinth metadata** from local mods
- **Dependency resolution** (including required libraries)
- **Manifest generation** for your modpack
- **Export packs** with auto-download of missing mods
- **Validation** against existing manifests
- **Simple CLI UX** with spinners and logging

## :arrow_down: **Installation**

**Prerequisites:**
- Python 3.13+
- Internet access for Modrinth API

**Recommended:**
```shell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install minecraftmodpackcli
```
**From source (Poetry):**
```shell
git clone https://github.com/Dtar380/MinecraftModpackCLI.git
cd MinecraftModpackCLI
poetry install
```
> [!NOTE]
> If using Poetry, run commands with: `poetry run MinecraftDockerCLI`

## :rocket: Quick start
## :wrench: **Tips & Troubleshooting**
- Ensure Docker Desktop is running and you can run `docker ps` without errors before invoking the CLI.
- On Windows, run PowerShell as Administrator or ensure your user has permissions for Docker.
- If `data.json` is missing, run `builder create` first to scaffold services.

## :memo:  **Working On**
Currently working on the MVP

Already Planned releases
| VERSION | INCLUDES                              |
| ------- | ------------------------------------- |
| 0.4.0   | UI/UX improvements                    |
| 0.5.0   | User Configurations (TOML format)     |
| 0.6.0   | Add more commands and supported files |
| 0.7.0   | Allow custom mods                     |
| 0.8.0   | Improved code base                    |
| 0.9.0   | Implement tests                       |
| 1.0.0   | Bug Fix, docs and Release             |

Feel free to open Feature Requests at [issues](https://github.com/Dtar380/WorkspaceAutomation/issues/new/choose).

## :open_file_folder: **Kown Issues**
There is no known issues on the project, you can submit yours to [issues](https://github.com/Dtar380/MinecraftDockerCLI/issues/new/choose).

## :scroll: **License**
This project is distributed under the MIT license.
See the [LICENSE](LICENSE).

## :money_with_wings: **Sponsorship**
You can support me and the project with a donation to my Ko-Fi.
