from telebot.async_telebot import AsyncTeleBot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ChatPermissions
from json import load, dump
from asyncio import sleep, create_task, run

#? LOAD CONFIG
with open('config.json', 'r') as data_config: config = load(data_config)


#? FIRST RUN CONFIG
if config == {}:
    config['bot_api_key'] = input('Paste here the BOTFATHER API KEY of your bot: \n')
    config['restrict_msg'] = input('This bot handle new members and send a simple captcha '
        'asking to user to press button\nWrite a message for the restriction message '
        'when user enter to your group\nNote: The first word of message will be '
        'automatically the user username (or name if user dont have a username)\n'
        'You can use html tags for text format, like <i></i> for italic format, or <b></b> for bold: \n')
    config['welcome_msg'] = input('Now write a welcome message. '
        'This message appears after user press the captcha button: \n')  
    buttons = input('Now write a text for button in welcome msg and a URL\n'
        'For example, type: INSTAGRAM https://www.instagram.com/INSTAGRAM\n'
        'If you need add more buttons edit config.json: \n')
    config['welcome_btns'] = {'btn1': [buttons.split()[0], buttons.split()[1]]}
    ban_words = input('Write prohibited words, bot will erase all message than contain these words')
    config['ban_words'] = ban_words.lower().split()
    with open('config.json', 'w', encoding='utf-8') as data_config:
        dump(config, data_config, indent=4)
    input('Config finished.\nRemember: If you need change any data, open config.json file,\n'
        'and remember put on folder a welcome_picture with name welcome.jpg\n\nPress any key\n')
    print('Bot started for first time')


tg = AsyncTeleBot(config['bot_api_key'], 'HTML')


#? HANDLE NEW MEMBERS
@tg.message_handler(content_types=['new_chat_members'])
async def new_member_handler(msg):
    for member in msg.new_chat_members:
        markup = InlineKeyboardMarkup()
        button = markup.add(InlineKeyboardButton('👉🏼    ✅    👈🏼', # BUTTON OF RESTRICTION MSG, EDIT IF NECCESARY
            callback_data=f'allow_{member.id}'))
        username = msg.from_user.username
        user = msg.from_user.full_name if not username else '@' + username
        try:
            await tg.restrict_chat_member(msg.chat.id, member.id, permissions=ChatPermissions())
            text = f'{user}, {config['restrict_msg']}'
            await tg.send_message(msg.chat.id, text, reply_markup=button)
            await tg.delete_message(msg.chat.id, msg.message_id) 
            print(f'Restriction message sent to {msg.from_user.full_name}')
        except Exception as e:
            print(e)
        @tg.callback_query_handler(func=lambda call:
            call.data == f'allow_{call.from_user.id}')
        async def handle_allow_button(call):
            try:
                await tg.restrict_chat_member(call.message.chat.id,
                    call.from_user.id, permissions=ChatPermissions(  
                        can_send_messages=True,
                        can_send_media_messages=True,
                        can_send_audios=True,
                        can_send_documents=True,
                        can_send_photos=True,
                        can_send_videos=True,
                        can_send_video_notes=True,
                        can_send_voice_notes=True,
                        can_send_polls=True,
                        can_send_other_messages=True,
                        can_add_web_page_previews=True,
                        can_invite_users=True
                    ))
                username = call.from_user.username
                user = f'{call.from_user.full_name}{f' / @{username}' if username else ''}'
                buttons = InlineKeyboardMarkup()
                for btn in config['welcome_btns'].values():
                    buttons.add(InlineKeyboardButton(btn[0], btn[1]))
                remsg = await tg.send_photo(
                    call.message.chat.id, open('welcome.jpg', 'rb'),
                    f'{user}, {config['welcome_msg']}',
                    reply_markup=buttons)
                await tg.delete_message(call.message.chat.id, call.message.message_id) 
                print(f'Welcome sent to {call.message.from_user.full_name}')
                create_task(del_msg(remsg, error=False))
            except Exception as e:
                print(e)


#? MUTE USERS
@tg.message_handler(['mute', 'ban'])
async def mute_user(req):
    if await is_admin(req.chat.id, req.from_user.id):
        try:
            muted_user = req.reply_to_message.from_user.id
            name = req.reply_to_message.from_user.full_name
            username = req.reply_to_message.from_user.username
            await tg.restrict_chat_member(req.chat.id, muted_user, ChatPermissions)
            remsg = await tg.reply_to(req, f'🗣 *{name}* | *@{username}* 🚷')
            print(f'{req.from_user.full_name} muted to '
                f'{name} / {username} on {req.chat.username}')
            create_task(del_msg(remsg, req))
        except Exception as e:
            remsg = await tg.reply_to(req, '⚠️ *ERROR*')
            print(f'MUTE ACTION ERROR FROM {req.chat.username}: {e}')
            create_task(del_msg(remsg, req))
    else:
        remsg = await tg.reply_to(req, '🚫 🫵🏼 🚫')
        create_task(del_msg(remsg, req))


#? DELETE MESSAGES
@tg.message_handler(func=lambda msg: True)
async def dlt_msgs(msg):
    msg_words = msg.text.lower().split()
    if [any(msg_words) in config['ban_words']]:
        await tg.delete_message(msg.chat.id, msg.message_id)
        print('Message deleted: {msg.text}')


#? FUNCTION TO DELETE MESSAGES BY TIME
async def del_msg(bot_msg=None, user_msg=None, error=True):
    if bot_msg.chat.type != 'private':
        await sleep(60) if error else await sleep(2600) # MESSAGES WILL BE DELETED IN 1HOUR. ERROR MSGS WILL BE DELETED ON 1MINUTE 
        if user_msg:
            try: await tg.delete_message(user_msg.chat.id, user_msg.message_id)
            except: pass
        if bot_msg:
            try: await tg.delete_message(bot_msg.chat.id, bot_msg.message_id)
            except: pass


#? CHECK IF USER IS ADMIN
async def is_admin(chat, user):
    is_admin = await tg.get_chat_member(chat, user)
    return is_admin.status in ['creator', 'administrator']



run(tg.infinity_polling())