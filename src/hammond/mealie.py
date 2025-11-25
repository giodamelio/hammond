import json
import os
import tempfile

import discord
import requests
from urlextract import URLExtract

from hammond.logger import logger
from hammond.systemd_creds import SystemdCreds

API_ROOT = "https://mealie.gio.ninja/api"

cache_dir = os.environ.get("CACHE_DIRECTORY", tempfile.gettempdir())
url_extractor = URLExtract(cache_dir=cache_dir)  # type: ignore

requester = requests.Session()
requester.headers = {"authorization": f"Bearer {SystemdCreds().mealie_token}"}


async def message_handler(message: discord.Message) -> None:
    logger.info("Handling Recipe Import Message")

    # Extract all URLS from the message
    urls = url_extractor.find_urls(message.clean_content)
    for url in urls:
        try:
            recipe_url = create_from_url(url)
            _ = await message.reply(content=f"Recipe created:\n{recipe_url}")
        except RecipeException as e:
            _ = await message.reply(content=f"{e}")


# Creates a recipe, tags it and returns the URL for it
def create_from_url(url: str) -> str:
    logger.debug(f"Adding recipe to Mealie: {url}")

    # Create the recipe
    data = json.dumps({"includeTags": True, "url": url})
    r = requester.post(API_ROOT + "/recipes/create/url", data=data)
    recipe_slug: dict = r.json()

    if r.status_code != 201:
        error_detail = r.json()["detail"]
        raise RecipeException(f"Could not create recipe: {error_detail}")

    # Fetch existing tags
    r = requester.get(API_ROOT + f"/recipes/{recipe_slug}")
    existing_tags: list[dict] = r.json()["tags"]

    # Tag the recipe
    data = json.dumps(
        {
            "tags": existing_tags
            + [
                {
                    "id": "21b57ac3-0840-44a7-9fc3-1bf4fa60f126",
                    "groupId": "9e266c5c-fc3f-4d02-98b1-e6c9340b703d",
                    "name": "From Discord",
                    "slug": "from-discord",
                },
                {
                    "id": "ec531fbd-2089-46a0-8336-0a687e873363",
                    "groupId": "9e266c5c-fc3f-4d02-98b1-e6c9340b703d",
                    "name": "Needs Cleanup",
                    "slug": "needs-cleanup",
                },
            ]
        }
    )
    r = requester.patch(API_ROOT + f"/recipes/{recipe_slug}", data=data)

    return f"https://mealie.gio.ninja/g/home/r/{recipe_slug}"


class RecipeException(Exception):
    pass
