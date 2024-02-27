import asyncio
import requests
from bs4 import BeautifulSoup
from feedbasket import config
from aiohttp import ClientConnectorError, ClientResponseError, ClientSession
import logging

log = logging.getLogger(__name__)


def extract_content_readability(url: str) -> str | None:
    # html = await fetch_content(url)
    try:
        r = requests.get(url, timeout=4, headers={"User-Agent": config.USER_AGENT})
        r.raise_for_status()
        html = r.text
    except requests.exceptions.RequestException as errex:
        return None
    if html is None:
        return None
    return clean_content(html)


# async def fetch_content(url):
#     async with ClientSession() as session:
#         headers = {"User-Agent": config.USER_AGENT}
#         try:
#             async with session.get(
#                 url,
#                 raise_for_status=True,
#                 timeout=config.GET_TIMEOUT,
#                 headers=headers,
#             ) as response:

#                 return await response.text()
#         except (ClientResponseError, ClientConnectorError, asyncio.TimeoutError) as e:
#             log.error("Could not fetch entry html: %s", url, e)
#             return None


def clean_content(html_content):
    soup = BeautifulSoup(html_content, "html.parser")
    for script in soup(["script", "style"]):
        script.extract()
    text = soup.get_text()
    lines = (line.strip() for line in text.splitlines())
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    cleaned_text = " ".join(chunk for chunk in chunks if chunk)
    return cleaned_text


#################################

# import asyncio
# import os
# import re
# import logging
# import json
# from asyncio.subprocess import Process
# from aiohttp import ClientConnectorError, ClientResponseError, ClientSession

# from feedbasket import config

# log = logging.getLogger(__name__)


# async def extract_content_readability(url: str) -> str | None:
#     await install_npm_packages()

#     async with ClientSession() as session:
#         headers = {"User-Agent": config.USER_AGENT}

#         try:
#             async with session.get(
#                 url,
#                 raise_for_status=True,
#                 timeout=config.GET_TIMEOUT,
#                 headers=headers,
#             ) as response:

#                 entry_html = await response.text()
#                 return await extract_content(entry_html)

#         except (ClientResponseError, ClientConnectorError, asyncio.TimeoutError):
#             log.error("Could not fetch entry html: %s", url)


# async def check_node_installed() -> bool:
#     try:
#         process: Process = await asyncio.create_subprocess_exec(
#             "node",
#             "--version",
#             stdout=asyncio.subprocess.PIPE,
#             stderr=asyncio.subprocess.PIPE,
#         )
#         await process.communicate()
#         return process.returncode == 0
#     except FileNotFoundError:
#         return False


# async def install_npm_packages() -> None:
#     if await check_node_installed():
#         current_dir = os.path.dirname(os.path.abspath(__file__))
#         javascript_dir = os.path.join(current_dir, "readability")
#         node_modules_dir = os.path.join(javascript_dir, "node_modules")

#         if not os.path.exists(node_modules_dir):
#             log.debug("Installing npm packages...")
#             try:
#                 process: Process = await asyncio.create_subprocess_exec(
#                     "npm",
#                     "install",
#                     cwd=javascript_dir,
#                     stdout=asyncio.subprocess.PIPE,
#                     stderr=asyncio.subprocess.PIPE,
#                 )
#                 await process.communicate()
#                 if process.returncode == 0:
#                     log.debug("Npm install completed.")
#                 else:
#                     log.debug("Failed to install npm packages.")
#             except FileNotFoundError:
#                 log.debug("Failed to install npm packages.")
#     else:
#         log.debug("Node.js runtime not found.")


# async def extract_content(html: str) -> str | None:
#     current_dir = os.path.dirname(os.path.abspath(__file__))
#     js_script_path = os.path.join(current_dir, "readability", "extract_stdout.js")

#     try:
#         process: Process = await asyncio.create_subprocess_exec(
#             "node",
#             js_script_path,
#             html,
#             stdout=asyncio.subprocess.PIPE,
#             stderr=asyncio.subprocess.PIPE,
#         )
#         stdout, sterr = await process.communicate()
#         if sterr:
#             return None  ## !!!!!
#         if stdout:
#             article_data = json.loads(stdout.decode())

#         if article_data:
#             text_content = re.sub(r"\s+", " ", article_data.get("textContent", ""))
#             if not text_content:
#                 log.debug("Content not extracted.")
#                 return None
#             return text_content
#     except FileNotFoundError:
#         log.debug("Failed to extract article.")
#         return None
