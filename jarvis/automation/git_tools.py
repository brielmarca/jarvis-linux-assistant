from jarvis.automation.linux import run_cmd
from jarvis.core.logger import JarvisLogger


log = JarvisLogger()


def git_run(command: str, repo_path: str | None = None) -> str:
    cmd_list = ["bash", "-c", f"cd {repo_path or '.'} && {command}"]
    code, out, err = run_cmd(cmd_list, timeout=15)
    if code == 0:
        return out.strip()[:1000] or "Git command completed"
    return f"Git error: {err[:200]}"


def git_status(repo_path: str | None = None) -> str:
    return git_run("git status --short", repo_path)


def git_log(repo_path: str | None = None, count: int = 10) -> str:
    return git_run(f"git log --oneline -{count}", repo_path)


def git_branch(repo_path: str | None = None) -> str:
    return git_run("git branch -a", repo_path)


def git_diff(repo_path: str | None = None) -> str:
    return git_run("git diff", repo_path)


def git_commit(repo_path: str | None = None, message: str = "update") -> str:
    return git_run(f'git commit -m "{message}"', repo_path)


def git_push(repo_path: str | None = None) -> str:
    return git_run("git push", repo_path)


def git_pull(repo_path: str | None = None) -> str:
    return git_run("git pull", repo_path)


def git_stash(repo_path: str | None = None) -> str:
    return git_run("git stash", repo_path)


def git_pop(repo_path: str | None = None) -> str:
    return git_run("git stash pop", repo_path)


def is_git_available() -> bool:
    code, _, _ = run_cmd(["which", "git"], timeout=3)
    return code == 0
