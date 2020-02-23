# load everything during testing
from telegram.ext import *
from telegram import *
import pickle
from bs4 import BeautifulSoup
import requests
import youtube_dl

TOKEN= 'TOKEN GOES HERE'

#The channel ID prefix URL for RSS:
rss_base="https://www.youtube.com/feeds/videos.xml?channel_id="

#The username prefix URL for RSS:
#rss_base="https://www.youtube.com/feeds/videos.xml?user="

#The playlist prefix URL for RSS:
#rss_base="https://www.youtube.com/feeds/videos.xml?playlist_id="

yt_watch = "https://www.youtube.com/watch?v="

user_playlist_dict={}

try:
    with open('objs.pkl','rb') as f:
        user_playlist_dict = pickle.load(f)
except:
    pass



def start(update, context):
    keyboard_main=[[KeyboardButton('/check_latest')]]
    reply_markup = ReplyKeyboardMarkup(keyboard_main)
    update.message.reply_text('convert videos from a youtube RSS feed to mp3.\n\nUse the /add command followed by the channel_id to save the reference to the feed with this bot.\n\nPress the /check_latest keyboard button to get a list of the five latest videos.\n\nSelect an item from the list and wait for the video to download and convert.', reply_markup=reply_markup)

    
def add(update, context):
    #context.bot.send_message(update.effective_chat.id, 'Enter the ID from a YouTube playlist:',reply_markup=ForceReply())
    USER_ID = update.effective_message.chat_id
    PLAYLIST_SHORTCODE = update.message.text.split()[-1].split('=')[-1]

    #context.bot.send_message(update.effective_chat.id, '{}: {}'.format(USER_ID,PLAYLIST_SHORTCODE))
    context.bot.send_message(update.effective_message.chat_id, 'adding {} to list'.format(PLAYLIST_SHORTCODE))
    
    user_playlist_dict[USER_ID] = PLAYLIST_SHORTCODE
    with open('objs.pkl', 'wb') as f:
        pickle.dump(user_playlist_dict, f)

    context.bot.send_message(update.effective_message.chat_id, 'saved.')


def download_audio(yt_shortcode):
    yt_link = "{}{}".format(yt_watch,yt_shortcode)
    outtmpl = yt_shortcode + '.%(ext)s'
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': outtmpl,
        'postprocessors': [
            {'key': 'FFmpegExtractAudio','preferredcodec': 'mp3',
             'preferredquality': '96',
            },
            {'key': 'FFmpegMetadata'},
        ],
    }
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(yt_link, download=True)
    
def check_latest(update, context):

    context.bot.send_chat_action(chat_id=update.effective_message.chat_id, action=ChatAction.TYPING )
    playlist_id = user_playlist_dict[update.effective_message.chat_id]
    context.bot.send_chat_action(chat_id=update.effective_message.chat_id, action=ChatAction.TYPING )

    feed=rss_base+playlist_id
    soup = BeautifulSoup(requests.get(feed).text, 'lxml')
    
    rss_dict={}
    # add media info to rss_dict 
    for i,(yt_id, yt_title, yt_published) in enumerate(zip(soup.find_all('id'),soup.find_all('title'), soup.find_all('published'))):
        yt_id = yt_id.get_text(strip=True).replace('yt:video:','').replace('yt:playlist:','')
        yt_title = yt_title.get_text(strip=True)
        yt_published = yt_published.get_text(strip=True)

        if yt_title not in rss_dict.keys():
            rss_dict[i] = {'yt_id': yt_id, 'yt_title': yt_title, 'yt_published': yt_published}

    rss_dict.pop(0,None)

    keyboard_inline = [
        [InlineKeyboardButton(rss_dict[1]['yt_title'], callback_data=rss_dict[1]['yt_id'])],
        [InlineKeyboardButton(rss_dict[2]['yt_title'], callback_data=rss_dict[2]['yt_id'])],
        [InlineKeyboardButton(rss_dict[3]['yt_title'], callback_data=rss_dict[3]['yt_id'])],
        [InlineKeyboardButton(rss_dict[4]['yt_title'], callback_data=rss_dict[4]['yt_id'])],
        [InlineKeyboardButton(rss_dict[5]['yt_title'], callback_data=rss_dict[5]['yt_id'])]
    ]

    reply_markup_inline = InlineKeyboardMarkup(keyboard_inline)

    update.message.reply_text('Select a video title to convert:', reply_markup=reply_markup_inline)

def button(update, context):
    query = update.callback_query
    context.bot.send_message(update.effective_message.chat_id, 'https://invidio.us/watch?v={}'.format(query.data))

    context.bot.send_message(update.effective_message.chat_id, 'downloading, converting, and uploading.\n\nThis may take a while.')
    
    context.bot.send_chat_action(chat_id=update.effective_message.chat_id, action=ChatAction.UPLOAD_AUDIO)
    download_audio(yt_shortcode=query.data)

    # send as document
    context.bot.send_message(update.effective_message.chat_id, 'uploading...')
    context.bot.send_audio(chat_id=update.callback_query.from_user.id, audio=open('{}.mp3'.format(query.data), 'rb'),timeout=10000)


def help(update, context):
    update.message.reply_text("Use /start to test this bot.\n")


def error(update, context):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)


def main():
    # Create the Updater and pass it your bot's token.
    # Make sure to set use_context=True to use the new context based callbacks
    # Post version 12 this will no longer be necessary
    updater = Updater(TOKEN, use_context=True)

    updater.dispatcher.add_handler(CommandHandler('start', start))
    updater.dispatcher.add_handler(CommandHandler('add', add))
    updater.dispatcher.add_handler(CommandHandler('check_latest', check_latest))

    updater.dispatcher.add_handler(CallbackQueryHandler(button))
    updater.dispatcher.add_handler(CommandHandler('help', help))
    updater.dispatcher.add_error_handler(error)

    # Start the Bot
    updater.start_polling()

    # Run the bot until the user presses Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT
    updater.idle()


if __name__ == '__main__':
    main()
