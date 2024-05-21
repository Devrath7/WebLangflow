import platform
import socket
import sys
import time
from pathlib import Path
from typing import Optional

import httpx
import typer
from dotenv import load_dotenv
from multiprocess import Process  # type: ignore
from packaging import version as pkg_version
from rich import box
from rich import print as rprint
from rich.console import Console
from rich.panel import Panel

from src.main import create_app
from langflow.utils.logger import logger

console = Console()

app = typer.Typer(no_args_is_help=True)


@app.command()
def run(
    host: str = typer.Option("127.0.0.1", help="Host to bind the server to.", envvar="LANGFLOW_DISCORD_HOST"),
    workers: int = typer.Option(1, help="Number of worker processes.", envvar="LANGFLOW_DISCORD_WORKERS"),
    timeout: int = typer.Option(300, help="Worker timeout in seconds."),
    port: int = typer.Option(7880, help="Port to listen on.", envvar="LANGFLOW_DISCORD_PORT"),
    # .env file param
    env_file: Path = typer.Option(None, help="Path to the .env file containing environment variables."),
    log_level: str = typer.Option("critical", help="Logging level.", envvar="LANGFLOW_LOG_LEVEL"),
    log_file: Path = typer.Option(
        "logs/langflow.log", help="Path to the log file.", envvar="LANGFLOW_DISCORD_LOG_FILE"
    ),
    dev: bool = typer.Option(False, help="Run in development mode (may contain bugs)"),
):
    """
    Run the Langflow Discord extension.
    """

    if env_file:
        load_dotenv(env_file, override=True)

    print("will setup app", flush=True)
    app = create_app()
    # check if port is being used
    if is_port_in_use(port, host):
        port = get_free_port(port)

    options = {
        "bind": f"{host}:{port}",
        "workers": 1,
        "timeout": timeout,
    }

    # Define an env variable to know if we are just testing the server
    if "pytest" in sys.modules:
        return
    try:
        if platform.system() in ["Windows"]:
            # Run using uvicorn on MacOS and Windows
            # Windows doesn't support gunicorn
            # MacOS requires an env variable to be set to use gunicorn
            process = run_on_windows(host, port, log_level, options, app)
        else:
            # Run using gunicorn on Linux
            process = run_on_mac_or_linux(host, port, log_level, options, app)

        if process:
            process.join()
    except KeyboardInterrupt:
        pass


def wait_for_server_ready(host, port):
    """
    Wait for the server to become ready by polling the health endpoint.
    """
    status_code = 0
    while status_code != 200:
        try:
            status_code = httpx.get(f"http://{host}:{port}/health").status_code
        except Exception:
            time.sleep(1)


def run_discord_on_mac_or_linux(host, port, log_level, options, app):
    webapp_process = Process(target=run_discord, args=(host, port, log_level, options, app))
    webapp_process.start()
    wait_for_server_ready(host, port)

    print_banner(host, port)
    return webapp_process


def run_on_mac_or_linux(host, port, log_level, options, app):
    webapp_process = Process(target=run_langflow, args=(host, port, log_level, options, app))
    webapp_process.start()
    wait_for_server_ready(host, port)

    print_banner(host, port)
    return webapp_process


def run_on_windows(host, port, log_level, options, app):
    """
    Run the Langflow server on Windows.
    """
    print_banner(host, port)
    run_langflow(host, port, log_level, options, app)
    return None


def is_port_in_use(port, host="localhost"):
    """
    Check if a port is in use.

    Args:
        port (int): The port number to check.
        host (str): The host to check the port on. Defaults to 'localhost'.

    Returns:
        bool: True if the port is in use, False otherwise.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex((host, port)) == 0


def get_free_port(port):
    """
    Given a used port, find a free port.

    Args:
        port (int): The port number to check.

    Returns:
        int: A free port number.
    """
    while is_port_in_use(port):
        port += 1
    return port


def version_is_prerelease(version: str):
    """
    Check if a version is a pre-release version.
    """
    return "a" in version or "b" in version or "rc" in version


def get_letter_from_version(version: str):
    """
    Get the letter from a pre-release version.
    """
    if "a" in version:
        return "a"
    if "b" in version:
        return "b"
    if "rc" in version:
        return "rc"
    return None


def build_new_version_notice(current_version: str, package_name: str):
    """
    Build a new version notice.
    """
    # The idea here is that we want to show a notice to the user
    # when a new version of Langflow is available.
    # The key is that if the version the user has is a pre-release
    # e.g 0.0.0a1, then we find the latest version that is pre-release
    # otherwise we find the latest stable version.
    # we will show the notice either way, but only if the version
    # the user has is not the latest version.
    if version_is_prerelease(current_version):
        # curl -s "https://pypi.org/pypi/langflow/json" | jq -r '.releases | keys | .[]' | sort -V | tail -n 1
        # this command will give us the latest pre-release version
        package_info = httpx.get(f"https://pypi.org/pypi/{package_name}/json").json()
        # 4.0.0a1 or 4.0.0b1 or 4.0.0rc1
        # find which type of pre-release version we have
        # could be a1, b1, rc1
        # we want the a, b, or rc and the number
        suffix_letter = get_letter_from_version(current_version)
        number_version = current_version.split(suffix_letter)[0]
        latest_version = sorted(
            package_info["releases"].keys(),
            key=lambda x: x.split(suffix_letter)[-1] and number_version in x,
        )[-1]
        if version_is_prerelease(latest_version) and latest_version != current_version:
            return (
                True,
                f"A new pre-release version of {package_name} is available: {latest_version}",
            )
    else:
        latest_version = httpx.get(f"https://pypi.org/pypi/{package_name}/json").json()["info"]["version"]
        if not version_is_prerelease(latest_version):
            return (
                False,
                f"A new version of {package_name} is available: {latest_version}",
            )
    return False, ""


def is_prerelease(version: str) -> bool:
    return "a" in version or "b" in version or "rc" in version


def fetch_latest_version(package_name: str, include_prerelease: bool) -> Optional[str]:
    response = httpx.get(f"https://pypi.org/pypi/{package_name}/json")
    versions = response.json()["releases"].keys()
    valid_versions = [v for v in versions if include_prerelease or not is_prerelease(v)]
    if not valid_versions:
        return None  # Handle case where no valid versions are found
    return max(valid_versions, key=lambda v: pkg_version.parse(v))


def build_version_notice(current_version: str, package_name: str) -> str:
    latest_version = fetch_latest_version(package_name, is_prerelease(current_version))
    if latest_version and pkg_version.parse(current_version) < pkg_version.parse(latest_version):
        release_type = "pre-release" if is_prerelease(latest_version) else "version"
        return f"A new {release_type} of {package_name} is available: {latest_version}"
    return ""


def generate_pip_command(package_names, is_pre_release):
    """
    Generate the pip install command based on the packages and whether it's a pre-release.
    """
    base_command = "pip install"
    if is_pre_release:
        return f"{base_command} {' '.join(package_names)} -U --pre"
    else:
        return f"{base_command} {' '.join(package_names)} -U"


def stylize_text(text: str, to_style: str, is_prerelease: bool) -> str:
    color = "#42a7f5" if is_prerelease else "#6e42f5"
    # return "".join(f"[{color}]{char}[/]" for char in text)
    styled_text = f"[{color}]{to_style}[/]"
    return text.replace(to_style, styled_text)


def print_banner(host: str, port: int):
    notices = []
    package_names = []  # Track package names for pip install instructions
    is_pre_release = False  # Track if any package is a pre-release
    package_name = ""

    try:
        from langflow.version import __version__ as langflow_version  # type: ignore

        is_pre_release |= is_prerelease(langflow_version)  # Update pre-release status
        notice = build_version_notice(langflow_version, "langflow")
        notice = stylize_text(notice, "langflow", is_pre_release)
        if notice:
            notices.append(notice)
        package_names.append("langflow")
        package_name = "Langflow"
    except ImportError:
        langflow_version = None

    # Attempt to handle langflow-base similarly
    if langflow_version is None:  # This means langflow.version was not imported
        try:
            from importlib import metadata

            langflow_base_version = metadata.version("langflow-base")
            is_pre_release |= is_prerelease(langflow_base_version)  # Update pre-release status
            notice = build_version_notice(langflow_base_version, "langflow-base")
            notice = stylize_text(notice, "langflow-base", is_pre_release)
            if notice:
                notices.append(notice)
            package_names.append("langflow-base")
            package_name = "Langflow Base"
        except ImportError as e:
            logger.exception(e)
            raise e

    # Generate pip command based on the collected data
    pip_command = generate_pip_command(package_names, is_pre_release)

    # Add pip install command to notices if any package needs an update
    if notices:
        notices.append(f"Run '{pip_command}' to update.")

    styled_notices = [f"[bold]{notice}[/bold]" for notice in notices if notice]
    styled_package_name = stylize_text(package_name, package_name, any("pre-release" in notice for notice in notices))

    title = f"[bold]Welcome to :chains: {styled_package_name}[/bold]\n"
    info_text = "Collaborate, and contribute at our [bold][link=https://github.com/langflow-ai/langflow]GitHub Repo[/link][/bold] :rocket:"
    access_link = f"Access [link=http://{host}:{port}]http://{host}:{port}[/link]"

    panel_content = "\n\n".join([title, *styled_notices, info_text, access_link])
    panel = Panel(panel_content, box=box.ROUNDED, border_style="blue", expand=False)
    rprint(panel)


def run_langflow(host, port, log_level, options, app):
    """
    Run Langflow server on localhost
    """
    try:
        if platform.system() in ["Windows"]:
            # Run using uvicorn on MacOS and Windows
            # Windows doesn't support gunicorn
            # MacOS requires an env variable to be set to use gunicorn
            import uvicorn

            uvicorn.run(
                app,
                host=host,
                port=port,
                log_level=log_level.lower(),
                loop="asyncio",
            )
        else:
            from langflow.server import LangflowApplication

            LangflowApplication(app, options).run()
    except KeyboardInterrupt:
        pass
    except Exception as e:
        logger.exception(e)
        sys.exit(1)


def run_discord(host, port, log_level, options, app):
    """
    Run Discord server on localhost
    """
    try:
        if platform.system() in ["Windows"]:
            # Run using uvicorn on MacOS and Windows
            # Windows doesn't support gunicorn
            # MacOS requires an env variable to be set to use gunicorn
            import uvicorn

            uvicorn.run(
                app,
                host=host,
                port=port,
                log_level=log_level.lower(),
                loop="asyncio",
            )
        else:
            from langflow.server import LangflowApplication

            LangflowApplication(app, options).run()
    except KeyboardInterrupt:
        pass
    except Exception as e:
        logger.exception(e)
        sys.exit(1)


def main():
    app()


if __name__ == "__main__":
    main()
