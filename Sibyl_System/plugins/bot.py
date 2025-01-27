from Sibyl_System import System, session, INSPECTORS, ENFORCERS, Sibyl_logs
from Sibyl_System.strings import proof_string, scan_request_string, reject_string
from Sibyl_System.plugins.Mongo_DB.gbans import get_gban, get_gban_by_proofid
import Sibyl_System.plugins.Mongo_DB.bot_settings as db

from telethon import events, custom

from typing import Union

import re
import asyncio

data = []
DATA_LOCK = asyncio.Lock()

async def can_ban(event):
    return event.chat.admin_rights.ban_users if event.chat.admin_rights else False

async def make_proof(user: Union[str, int]):
    if isinstance(user, str) and user.startswith('#'):
        data = await get_gban_by_proofid(int(user.strip('#')))
    else:
        data = await get_gban(int(user))
    if not data:
        return False
    message = data.get("message") or ""
    async with session.post(
        "https://nekobin.com/api/documents", json={"content": message}
    ) as r:
        paste = f"https://nekobin.com/{(await r.json())['result']['key']}"
    url = "https://del.dog/documents"
    async with session.post(url, data=message.encode("UTF-8")) as f:
        r = await f.json()
        url = f"https://del.dog/{r['key']}"
    return proof_string.format(
        proof_id=data["proof_id"], reason=data["reason"], paste=paste, url=url
    )


@System.bot.on(events.NewMessage(pattern="[/?]start"))
async def sup(event):
    await event.reply("sup?")


@System.bot.on(events.NewMessage(pattern="[/?]help"))
async def help(event):
    await event.reply(
        """
This bot is a inline bot, You can use it by typing `@GbanWatchRobot`
If a user is gbanned -
    Getting reason for gban, message the user was gbanned for - `@GbanWatchRobot proof <user_id|proof_id>`
    """
    )


@System.bot.on(events.CallbackQuery(pattern=r"(approve|reject)_(\d*)"))
async def callback_handler(event):
    split = event.data.decode().split("_", 1)
    index = int(split[1])
    message = await event.get_message()
    async with DATA_LOCK:
        try:
            dict_ = data[index]
        except IndexError:
            dict_ = None
    if not dict_:
        await event.answer(
            "Message is too old (Bot was restarted after message was sent), Use /approve on it instead",
            alert=True,
        )
        return
    await event.answer(
        "I have sent you a message, Reply to it to overwrite reason/specify reject reason, Otherwise ignore",
        alert=True,
    )
    sender = await event.get_sender()
    async with event.client.conversation(sender.id, timeout=15) as conv:
        if split[0] == "approve":
            await conv.send_message(
                "You approved a scan it seems, Would you like to overwrite reason?"
            )
        else:
            await conv.send_message(
                "You rejected a scan it seems, Would you like to give rejection reason?"
            )
        try:
            r = await conv.get_response()
        except asyncio.exceptions.TimeoutError:
            r = None
    if r:
        if split[0] == "approve":
            async with DATA_LOCK:
                dict_["reason"] = r.message
                data[index] = dict_
            msg = f"New Reason:\nU_ID: {dict_['u_id']}\n"
            msg += f"Enforcer: {dict_['enforcer']}\n"
            msg += f"Source: {dict_['source']}\n"
            msg += f"Reason: {dict_['reason']}\n"
            msg += f"Message: {dict_['message']}\n"
            await event.respond(msg)
            await message.edit(
                re.sub(
                    "(\*\*)?(Scan)? ?Reason:(\*\*)? (`([^`]*)`|.*)",
                    f"**Scan Reason:** {r.message}",
                    message.message,
                )
            )
        else:
            await message.edit(reject_string)
            async with DATA_LOCK:
                del data[index]
    else:
        await event.respond("no respond, bye bye")


@System.bot.on(events.InlineQuery)
async def inline_handler(event):
    builder = event.builder
    query = event.text
    split = query.split(" ", 1)
    if event.query.user_id not in INSPECTORS:
        result = builder.article(
            "GbanWatch System", text="You don't have access to this cmd."
        )
        await event.answer([result])
        return
    if query.startswith("proof"):
        if len(split) == 1:
            result = builder.article("Type Case-ID", text="No Case-ID was provided")
        else:
            proof = await make_proof(split[1])
            if proof is False:
                result = builder.article(
                    "User is not gbanned.",
                    text="User is not gbanned.",
                )
            else:
                result = builder.article("Proof", text=proof, link_preview=False)
    elif query.startswith("builder"):
        split = query.replace("builder", "").split(":::", 4)
        print(split)
        if len(split) != 5:
            result = builder.article("Not enough info provided...")
        else:
            u_id, enforcer, source, reason, message = split
            dict_ = {
                "u_id": u_id,
                "enforcer": enforcer,
                "source": source,
                "reason": reason,
                "message": message,
            }
            print(dict_)
            async with DATA_LOCK:
                data.append(dict_)
                index = data.index(dict_)
            buttons = [
                custom.Button.inline("Approve", data=f"approve_{index}"),
                custom.Button.inline("Reject", data=f"reject_{index}"),
            ]
            result = builder.article(
                "Output",
                text=scan_request_string.format(
                    enforcer=enforcer,
                    spammer=u_id,
                    reason=reason,
                    chat=source,
                    message=message,
                ),
                buttons=buttons,
            )

    else:
        result = builder.article(
            "No type provided",
            text="Use\nproof <user_id> to get proof\nbuilder id:::enforcer:::source:::reason:::message",
        )
    await event.answer([result])

@System.bot.on(events.ChatAction(func=lambda e: e.user_joined))
async def check_user(event):
    print(event.stringify())
    if event.created:
        return
    user = await event.get_user()
    if not user:
        if System.bot.id not in event.action_message.action.users:
            return
        if not (await db.add_chat(event.chat_id)):
            return
        msg = "Thanks for adding me here!\n"\
              "Here are your current settings:\n"\
              "Alert: True\n"\
              "Alert Mode: Warn"
        await event.respond(msg)
    elif user.id in INSPECTORS or user.id in ENFORCERS:
        return
    else:
        u = await get_gban(user.id)
        chat = await db.get_chat(event.chat_id)
        if not u:
            return
        if chat['alertmode'] == 'silent-ban':
            await event.client.edit_permissions(event.chat_id, user.id, view_messages=False)
            return
        msg = f"{user.first_name}'s Crime-Coeffecient is over 300!\n"\
              f"*Reason:* `{u['reason']}`\n"
        if chat['alertmode'] == 'ban':
            if can_ban(event):
                await event.client.edit_permissions(event.chat_id, user.id, view_messages=False)
                msg += "Banning them from here."
            else:
                msg += "I can't ban users here, So just warning."

        await event.respond(msg)
        
