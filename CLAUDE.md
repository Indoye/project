# CLAUDE.md — AI Assistant Guide for Afridaara

## Project Overview

**Afridaara** is an educational Linux distribution initiative focused on Senegal. The project aims to provide a free, offline-capable educational platform containing the full Senegalese school curriculum (CI through Terminale) for students, teachers, and school administrators.

This repository is a **documentation repository** — not a software code project. It contains Markdown documentation, guides, and assets describing the distribution concept and customization tools.

## Repository Structure

```
project/
├── CLAUDE.md                              # This file
├── README.md                              # Main project documentation (French)
├── LICENSE                                # GNU General Public License v3
├── assets/
│   └── img/
│       └── Ubuntu-Builder.png             # Screenshot for Ubuntu-Builder guide
└── outils/
    └── personnaliser/
        └── Ubuntu-Builder.md              # Guide for customizing Ubuntu
```

## Technology Stack

- **Base OS**: Ubuntu Linux (free, open-source)
- **Educational variant**: Edubuntu
- **Documentation format**: Markdown
- **Language**: French (primary content language)
- **License**: GNU General Public License v3

## Key Conventions

### Language
- All project content is written in **French**
- Commit messages have historically been in French
- When contributing documentation, maintain French as the primary language

### Documentation Format
- Use Markdown (`.md`) for all documentation files
- Follow the existing heading hierarchy in each file
- Include code blocks for shell commands using triple backticks

### File Organization
- Place tool guides under `outils/personnaliser/`
- Place images and visual assets under `assets/img/`
- Link images using relative paths (e.g., `../../assets/img/filename.png`)

### Versioning
- The project intends to follow [SemVer](http://semver.org/) for versioning
- Version tags should be applied to releases

## Development Workflow

Since this is a documentation-only repository, the workflow is:

1. **Edit or add Markdown files** in the appropriate directory
2. **Add images/assets** under `assets/img/` if needed
3. **Update README.md** if new sections or tools are added
4. **Commit with a descriptive message** (preferably in French to match project convention)
5. **Push to remote**

### Common Git Commands

```bash
# Clone the repository
git clone <repo-url>

# Create a feature branch
git checkout -b feature/my-feature

# Stage and commit changes
git add .
git commit -m "Description of changes"

# Push changes
git push -u origin feature/my-feature
```

## Content Areas

### README.md
The main entry point describing:
- Mission and goals of Afridaara
- Target audience (students, teachers, administrators)
- Built-on Ubuntu rationale
- List of included software (to be completed)
- Customization tools

### Ubuntu-Builder Guide (`outils/personnaliser/Ubuntu-Builder.md`)
A step-by-step guide covering:
- Installing Ubuntu-Builder via PPA
- Loading an ISO source
- Customizing a distribution via GUI
- Building a custom ISO

## Notes for AI Assistants

- **No code to execute**: There are no scripts, tests, or build systems. Do not attempt to run code.
- **No package managers**: No `npm`, `pip`, `cargo`, or similar tools are used.
- **No environment files**: There are no `.env` files or secrets to manage.
- **Content is in French**: When editing documentation, preserve the French language and tone.
- **Documentation gaps**: The README contains placeholder sections (Prerequisites, Installing, Running tests, Deployment) that are not yet filled in — this is intentional and reflects the early state of the project.
- **License inconsistency**: The README footer references an MIT License, but the actual `LICENSE` file contains GNU GPL v3. This is a known inconsistency in the original documentation.
- **Contributors**: Original contributors include Mamadou Diagne and Seydina Issa PATE (2017).

## What to Work On

When asked to contribute to this repository, appropriate tasks include:

1. **Filling in README placeholders** — Prerequisites, Installing, Deployment sections
2. **Adding new tool guides** under `outils/personnaliser/`
3. **Creating curriculum documentation** describing included educational content
4. **Adding a software list** to the "Logiciels" section of README
5. **Improving existing guides** for clarity and completeness
6. **Translating documentation** to other languages (English, Wolof, etc.)
