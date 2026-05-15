import os
import re
import requests
from datetime import datetime, timezone

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
USERNAME = "JG-OLIVEIRA"

HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json",
}

LANG_COLORS = {
    "Java": "#b07219",
    "Python": "#3572A5",
    "JavaScript": "#f1e05a",
    "TypeScript": "#2b7489",
    "HCL": "#844FBA",
    "Shell": "#89e051",
    "Dockerfile": "#384d54",
    "HTML": "#e34c26",
    "CSS": "#563d7c",
}

LANG_BADGES = {
    "Java":       "Java-ED8B00?logo=openjdk&logoColor=white",
    "HCL":        "Terraform-7B42BC?logo=terraform&logoColor=white",
    "Python":     "Python-3776AB?logo=python&logoColor=white",
    "JavaScript": "JavaScript-F7DF1E?logo=javascript&logoColor=black",
    "TypeScript": "TypeScript-3178C6?logo=typescript&logoColor=white",
    "Shell":      "Shell-121011?logo=gnu-bash&logoColor=white",
    "Dockerfile": "Docker-2496ED?logo=docker&logoColor=white",
    "HTML":       "HTML5-E34F26?logo=html5&logoColor=white",
    "CSS":        "CSS3-1572B6?logo=css3&logoColor=white",
}

def get_repos():
    url = f"https://api.github.com/users/{USERNAME}/repos"
    params = {"sort": "updated", "per_page": 100, "type": "public"}
    resp = requests.get(url, headers=HEADERS, params=params)
    repos = resp.json()
    # Filter forks, sort by stars then updated
    repos = [r for r in repos if not r.get("fork")]
    repos.sort(key=lambda r: (-r.get("stargazers_count", 0), r.get("updated_at", "")), reverse=False)
    repos.sort(key=lambda r: r.get("updated_at", ""), reverse=True)
    return repos

def get_recent_activity():
    url = f"https://api.github.com/users/{USERNAME}/events/public"
    resp = requests.get(url, headers=HEADERS, params={"per_page": 10})
    events = resp.json()
    activity = []
    seen = set()
    for event in events:
        etype = event.get("type", "")
        repo = event.get("repo", {}).get("name", "")
        if repo in seen:
            continue
        seen.add(repo)
        created_at = event.get("created_at", "")
        dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
        date_str = dt.strftime("%d/%m/%Y")

        if etype == "PushEvent":
            commits = event.get("payload", {}).get("commits", [])
            msg = commits[0].get("message", "")[:60] if commits else "push"
            activity.append(f"📦 **Push** em [`{repo}`](https://github.com/{repo}) — _{msg}_ · `{date_str}`")
        elif etype == "CreateEvent":
            ref_type = event.get("payload", {}).get("ref_type", "")
            activity.append(f"✨ **Criou** {ref_type} em [`{repo}`](https://github.com/{repo}) · `{date_str}`")
        elif etype == "PullRequestEvent":
            action = event.get("payload", {}).get("action", "")
            activity.append(f"🔀 **Pull Request** {action} em [`{repo}`](https://github.com/{repo}) · `{date_str}`")
        elif etype == "IssuesEvent":
            action = event.get("payload", {}).get("action", "")
            activity.append(f"🐛 **Issue** {action} em [`{repo}`](https://github.com/{repo}) · `{date_str}`")
        elif etype == "WatchEvent":
            activity.append(f"⭐ **Star** em [`{repo}`](https://github.com/{repo}) · `{date_str}`")
        elif etype == "ForkEvent":
            activity.append(f"🍴 **Fork** de [`{repo}`](https://github.com/{repo}) · `{date_str}`")

        if len(activity) >= 5:
            break
    return activity

def build_repo_card(repo):
    name = repo["name"]
    url = repo["html_url"]
    desc = repo.get("description") or "Sem descrição."
    lang = repo.get("language") or "—"
    stars = repo.get("stargazers_count", 0)
    updated = repo.get("updated_at", "")
    if updated:
        dt = datetime.fromisoformat(updated.replace("Z", "+00:00"))
        updated_str = dt.strftime("%d/%m/%Y")
    else:
        updated_str = "—"

    badge = LANG_BADGES.get(lang)
    lang_badge = f"![{lang}](https://img.shields.io/badge/{badge}&style=flat-square)" if badge else f"`{lang}`"

    stars_badge = f"![Stars](https://img.shields.io/github/stars/JG-OLIVEIRA/{name}?style=flat-square&color=F97316&labelColor=0d1117)"

    return (
        f"### 🔗 [{name}]({url})\n"
        f"> {desc}\n\n"
        f"{lang_badge} {stars_badge} · 🕒 Atualizado em `{updated_str}`\n"
    )

def update_readme(repos, activity):
    with open("README.md", "r", encoding="utf-8") as f:
        content = f.read()

    # --- Update REPOS section ---
    repo_lines = "\n".join(build_repo_card(r) for r in repos[:6])
    now = datetime.now(timezone.utc).strftime("%d/%m/%Y às %H:%M UTC")
    repos_block = f"\n{repo_lines}\n\n> 🤖 Atualizado automaticamente em **{now}**\n"
    content = re.sub(
        r"(<!-- REPOS:START -->).*?(<!-- REPOS:END -->)",
        f"\\1{repos_block}\\2",
        content,
        flags=re.DOTALL,
    )

    # --- Update ACTIVITY section ---
    if activity:
        act_lines = "\n".join(f"- {a}" for a in activity)
        act_block = f"\n{act_lines}\n"
    else:
        act_block = "\n- Nenhuma atividade recente encontrada.\n"
    content = re.sub(
        r"(<!-- ACTIVITY:START -->).*?(<!-- ACTIVITY:END -->)",
        f"\\1{act_block}\\2",
        content,
        flags=re.DOTALL,
    )

    with open("README.md", "w", encoding="utf-8") as f:
        f.write(content)

    print(f"✅ README atualizado com {len(repos[:6])} repos e {len(activity)} atividades.")

if __name__ == "__main__":
    print("🔄 Buscando repos...")
    repos = get_repos()
    print(f"   {len(repos)} repos encontrados.")
    print("🔄 Buscando atividade recente...")
    activity = get_recent_activity()
    print("📝 Atualizando README...")
    update_readme(repos, activity)
