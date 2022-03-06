from Sibyl_System import (
    System,
    system_cmd,
    make_collections,
    INSPECTORS,
    ENFORCERS,
    Sibyl_logs,
)
from Sibyl_System.strings import on_string
import logging
import importlib
import asyncio
import time
from telethon import TelegramClient, events, Button, types, functions, errors

logging.basicConfig(
    format="[%(levelname) 5s/%(asctime)s] %(name)s: %(message)s", level=logging.WARNING
)

from Sibyl_System.plugins import to_load

HELP = {}
IMPORTED = {}
FAILED_TO_LOAD = {}

for load in to_load:
    try:
        imported = importlib.import_module("Sibyl_System.plugins." + load)
        if not hasattr(imported, "__plugin_name__"):
            imported.__plugin_name__ = imported.__name__

        if imported.__plugin_name__.lower() not in IMPORTED:
            IMPORTED[imported.__plugin_name__.lower()] = imported

        if hasattr(imported, "help_plus") and imported.help_plus:
            HELP[imported.__plugin_name__.lower()] = imported
    except Exception as e:
        print(f"Error while loading plugin: {load}")
        print("------------------------------------")
        print(e)
        FAILED_TO_LOAD[load] = e
        print("------------------------------------")


@System.on(system_cmd(pattern=r"status", allow_enforcer=True))
async def status(event):
    msg = await event.reply("Portable Psychological Diagnosis and Suppression System.")
    time.sleep(1)
    await msg.edit("Initialising ▫️◾️▫️")
    time.sleep(1)
    await msg.edit("Initialising ◾️▫️◾️")
    time.sleep(1)
    await msg.edit("Initialising ▫️◾️▫️")
    time.sleep(1)
    await msg.edit("Initialising ◾️▫️◾️")
    time.sleep(1)
    await msg.edit("Initialising ▫️◾️▫️")
    time.sleep(1)
    await msg.edit("Initialising ◾️▫️◾️")
    time.sleep(1)
    await msg.edit("Initialising ▫️◾️▫️")
    time.sleep(1)
    await msg.edit("Connection successful!")
    time.sleep(2)
    sender = await event.get_sender()
    user_status = "Inspector" if sender.id in INSPECTORS else "Enforcer"
    time.sleep(1)
    await msg.edit(on_string.format(Enforcer=user_status, name=sender.first_name))


@System.on(system_cmd(pattern="sibyl stats"))
async def stats(event):
    msg = f"Processed {System.processed} messages since last restart."
    msg += f"\n{len(ENFORCERS)} Enforcers & {len(INSPECTORS)} Inspectors"
    g = 0
    async for d in event.client.iter_dialogs(limit=None):
        if d.is_channel and not d.entity.broadcast or d.is_group:
            g += 1
    msg += f"\nModerating {g} Groups"
    await event.reply(msg)


start_msg = """Hi {user}!
**Myself GbanWatch System , mainly focused on working to reduce spam and scam [admin approval invite links](https://t.me/telegram/153).**
**__I can__**:
- __Auto detect illigal activity of telegram requests.__
- __Auto Push and release Watch From Gban System Requests.__
`Click the below button to know how to use me!`"""
start_buttons = [
    [Button.url("Support", "https://t.me/GbanWatch")],
    [Button.url("Updates", "https://t.me/GbanWatch")],
]


@System.on(system_cmd(pattern=r"help", allow_slash=False, allow_inspectors=True))
async def send_help(event):
    from_ = await System.get_entity(event.sender_id)
    await event.reply(
        start_msg.format(user=from_.first_name),
        buttons=start_buttons,
        link_preview=False,
    )


async def main():
    try:
        await make_collections()
        me = await System.bot.get_me()
        System.bot.id = me.id
    except Exception as e:
        FAILED_TO_LOAD["main"] = e
    await System.start()
    await System.catch_up()
    if FAILED_TO_LOAD:
        msg = "Few plugins failed to load:"
        for plugin in FAILED_TO_LOAD:
            msg += f"\n**{plugin}**\n\n`{FAILED_TO_LOAD[plugin]}`"
        await System.send_message(Sibyl_logs, msg)
    else:
        await System.send_message(Sibyl_logs, "I'm up!")
    await System.run_until_disconnected()


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())
