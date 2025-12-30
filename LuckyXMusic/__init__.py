from LuckyXMusic.core.bot import Lucky
from LuckyXMusic.core.dir import dirr
from LuckyXMusic.core.git import git
from LuckyXMusic.core.userbot import Userbot
from LuckyXMusic.misc import dbb, heroku

from .logging import LOGGER

dirr()
git()
dbb()
heroku()

Lucky = Lucky()
userbot = Userbot()


from .platforms import *

Apple = AppleAPI()
Carbon = CarbonAPI()
SoundCloud = SoundAPI()
Spotify = SpotifyAPI()
Resso = RessoAPI()
Telegram = TeleAPI()
YouTube = YouTubeAPI()
