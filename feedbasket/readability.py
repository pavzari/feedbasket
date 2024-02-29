import logging

from aiohttp import ClientSession
from bs4 import BeautifulSoup

from feedbasket import config

log = logging.getLogger(__name__)


async def extract_content_readability(url):
    async with ClientSession() as session:
        headers = {"User-Agent": config.USER_AGENT}
        try:
            async with session.get(
                url,
                raise_for_status=True,
                timeout=config.GET_TIMEOUT,
                headers=headers,
            ) as response:

                html = await response.text()
                soup = BeautifulSoup(html, "html.parser")
                return soup.get_text()

        except Exception as e:
            log.error("Could not fetch entry html: %s", url, e)
            return None


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
