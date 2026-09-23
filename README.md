<!-- ================================================================= -->
<!-- KEERTHANA R — ANIMATED GITHUB PROFILE                             -->
<!-- ================================================================= -->

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/keerthana2k7/keerthana2k7/main/dark.svg">
  <source media="(prefers-color-scheme: light)" srcset="https://raw.githubusercontent.com/keerthana2k7/keerthana2k7/main/light.svg">
  <img alt="Keerthana R Profile Banner" src="https://raw.githubusercontent.com/keerthana2k7/keerthana2k7/main/light.svg" width="100%">
</picture>

<br/><br/>

<!-- ================================================================= -->
<!-- STATS CARDS (Self-Hosted Instance)                                -->
<!-- ================================================================= -->

<div align="center">
  <img width="100%" src="https://streak-stats.demolab.com/?user=keerthana2k7&hide_border=true&background=0A101F&stroke=22D3EE&ring=A78BFA&fire=10B981&currStreakLabel=22D3EE&sideLabels=94A3B8&currStreakNum=F8FAFC&sideNums=F8FAFC&dates=64748B&titleColor=22D3EE&card_width=1180" alt="GitHub Streak" />
  <br/><br/>
  <img width="49%" src="https://YOUR-INSTANCE.vercel.app/api?username=keerthana2k7&show_icons=true&count_private=true&include_all_commits=true&hide_rank=true&hide_border=true&title_color=22D3EE&icon_color=A78BFA&text_color=94A3B8&bg_color=0A101F&card_width=500" alt="GitHub Stats" />
  <img width="49%" src="https://YOUR-INSTANCE.vercel.app/api/top-langs/?username=keerthana2k7&layout=compact&langs_count=8&hide_border=true&title_color=22D3EE&text_color=94A3B8&bg_color=0A101F&card_width=500" alt="Top Languages" />
</div>

<br/>

<!-- ================================================================= -->
<!-- CONTRIBUTION SNAKE ANIMATION                                      -->
<!-- ================================================================= -->

<div align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/keerthana2k7/keerthana2k7/output/github-snake-dark.svg" />
    <source media="(prefers-color-scheme: light)" srcset="https://raw.githubusercontent.com/keerthana2k7/keerthana2k7/output/github-snake.svg" />
    <img alt="Snake eating contributions" src="https://raw.githubusercontent.com/keerthana2k7/keerthana2k7/output/github-snake.svg" width="100%" />
  </picture>
</div>

<br/>

<!-- ================================================================= -->
<!-- SOCIAL & CONTACT BADGES                                           -->
<!-- ================================================================= -->

<div align="center">
  <a href="https://www.linkedin.com/in/keerthana-r/">
    <img src="https://img.shields.io/badge/LinkedIn-0A66C2?style=for-the-badge&logo=linkedin&logoColor=white" alt="LinkedIn" />
  </a>
  &nbsp;&nbsp;
  <a href="mailto:keerthana.rajvanitha@gmail.com">
    <img src="https://img.shields.io/badge/Email-0A101F?style=for-the-badge&logo=gmail&logoColor=10B981&labelColor=0A101F" alt="Email" />
  </a>
  &nbsp;&nbsp;
  <a href="https://github.com/keerthana2k7">
    <img src="https://img.shields.io/badge/GitHub-0A101F?style=for-the-badge&logo=github&logoColor=22D3EE&labelColor=0A101F" alt="GitHub" />
  </a>
</div>

<br/><hr/>

### 🛠️ Setup & Deployment Guide

Follow this checklist to finish connecting your animated profile:

1. **Profile Repository**:
   - Create a repository named exactly matching your username: `keerthana2k7/keerthana2k7` set to **Public** at [github.com/new](https://github.com/new).
   - Push `dark.svg`, `light.svg`, `.github/workflows/snake.yml`, and this `README.md` to branch `main`.

2. **Enable Actions Workflow Permissions**:
   - Navigate to repository **Settings** &rarr; **Actions** &rarr; **General**.
   - Scroll to **Workflow permissions** &rarr; select **Read and write permissions** &rarr; click **Save**.
   - *(Note: Configure this inside the repository settings `github.com/keerthana2k7/keerthana2k7/settings/actions`, not your account-level settings).*

3. **Self-Host `github-readme-stats` on Vercel**:
   - Create a GitHub Classic Token: Go to `github.com/settings/tokens` &rarr; **Tokens (classic)** &rarr; **Generate new token (classic)**.
     - Note: `readme-stats`, Expiration: `No expiration`, Scopes: tick `repo` (all).
     - Copy the token immediately and keep it private.
   - Fork [`anuraghazra/github-readme-stats`](https://github.com/anuraghazra/github-readme-stats).
   - Log into [Vercel](https://vercel.com/) with GitHub &rarr; Add New Project &rarr; Import your fork.
   - Under Environment Variables: Add `PAT_1` = your personal access token.
   - Deploy, wait for the build to finish, and copy your deployed domain (e.g. `your-instance.vercel.app`).
   - In `README.md`, replace `YOUR-INSTANCE` in both stats URLs with your deployed domain.
   - *(Note on `hide_rank=true`: Default ranking is heavily weighted toward stars/followers. Hiding rank highlights actual code and commit activity honestly).*

4. **Trigger Contribution Snake**:
   - Go to your repo's **Actions** tab &rarr; select **Generate Snake Animation** &rarr; click **Run workflow**.
   - Once the action completes with a green checkmark, it creates the orphan `output` branch hosting `github-snake.svg` and `github-snake-dark.svg`.
