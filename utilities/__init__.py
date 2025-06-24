"""
Utilities package for NEBot.
This package contains various utility functions used throughout the bot.
"""

from .text_formatting import (
    convert_country_name, 
    convert_country_name_channel,
    parse_mentions
)
from .currency import (
    convert, 
    unconvert, 
    amount_converter
)
from .discord_utils import (
    is_authorized,
    send_long_message,
    discord_input,
    get_auth_embed,
    get_users_by_reaction
)
from .construction import (
    calculate_total_area,
    calculate_construction_cost,
    get_people_per_apartment
)
# For backwards compatibility
from .text_formatting import *
from .currency import *
from .discord_utils import *
from .construction import *