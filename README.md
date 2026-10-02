# Timothy Gilbert · Digital Portfolio

Welcome! This repository contains the source for my Quarto-based portfolio, which covers Shiny apps, data tools built for ecological field teams, and five interactive browser experiences.

## 🏡 Live Site

👉 [View my portfolio here](https://tgilbert14.github.io/timothy-gilbert-portfolio/)

## 📁 Structure

- `_quarto.yml` – Site configuration: navigation, styling, metadata
- `index.qmd` – Homepage: introduction, featured work, skills, interactive websites, and field background
- `work.qmd` – Six selected projects and five browser experiences, led by Living X-Ray and Two Futures
- `about.qmd` – Professional background, field experience, and contact information
- `dashboards.qmd` – Featured Shiny apps
- `projects.qmd` – Other apps, scripts, and automation tools
- `field-notes.qmd` – "Flora Wall": Arizona fieldwork photo band + masonry plant wall (lightbox)
- `ecoplot.qmd` – EcoPlot Mobile flagship: capabilities, field→report flow, screenshots
- `resume.qmd` – Embedded résumé with highlights and download link
- `styles.css` – Original site-wide navy "desert night" theme
- `revamp.css` – Presentation layer for the home, work, and about pages
- `_foot.html` – Site-wide JS: scroll reveals, parallax, plant-wall lightbox
- `assets/` – All images (incl. `assets/photos/`), icons, and PDF files

## ⚙️ Tech Stack

Built using:

- [Quarto](https://quarto.org/) for site generation
- R packages: `shiny`, `ggplot2`, `tidyverse`, `DBI`, `plotly`, `RSQLite`
- Hosted via GitHub Pages

## Sprite Fusion launcher

Every page has a compact top-right shortcut to [Destroy Any Website](https://www.spritefusion.com/games/destroy-any-website), a game by Hugo Duprez / Sprite Fusion. It stays visible outside the mobile navigation menu and takes the current tab directly to `https://destroy.spritefusion.com/?url=tgilbert14.github.io%2Ftimothy-gilbert-portfolio%2F`. Home and Work use the same direct link on the official badge and include an original miniature target for local practice feedback. No game code is embedded or copied. JavaScript is optional for launching; reduced motion keeps the practice feedback static.

The game's production `frame-ancestors` policy excludes GitHub Pages, so the integration uses its documented native badge link. Source checks and the exact policy observed on 2026-10-02 are recorded in `release-pass.json`.

## 📦 Projects Featured

Check out tools on my GitHub like:

- [NCAA Recruitment Trend Visualizer](https://github.com/tgilbert14/UA-recruits-)
- [Electron-Bundled Shiny Desktop App](https://github.com/tgilbert14/R-Local-Storage-SQL-exe)
- [VGS Batch Importer App](https://github.com/tgilbert14/VGS-Batch-Importer-App)
- [NEON Small Mammal Tracker](https://github.com/tgilbert14/NEON-Small-Mammal-Tracker-App)
- [NEON Water Chemistry Viewer](https://github.com/tgilbert14/NEON-WaterChemistry-Analyte-Viewer-App)
- [The Long Saturday](https://github.com/tgilbert14/old-pueblo)
- [27 Miles to Canada](https://github.com/tgilbert14/ddl-27-miles)
- [The Orrery](https://github.com/tgilbert14/ddl-orrery)

Each app/script is built to support ecological field teams, research workflows, or dynamic data storytelling.

## 📝 License & Contributions

This portfolio is open for inspiration — feel free to fork or adapt. If you're working on similar tech in conservation, health science, or field data design, let's connect!

## 📬 Contact

Email: [tsgilbert@arizona.edu](mailto:tsgilbert@arizona.edu)  
GitHub: [@tgilbert14](https://github.com/tgilbert14)
