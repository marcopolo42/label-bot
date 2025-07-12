
import discord
from label_cog.src.config import Config
from label_cog.src.view_utils import update_displayed_status, update_displayed_status_with_data
from label_cog.src.database import update_user_language
from label_cog.src.logging_dotenv import setup_logger
from label_cog.src.utils import get_translation
from label_cog.src.view_utils import display_and_stop, set_current_value_as_default
from label_cog.src.database import add_user_coins, get_user_coins
from label_cog.src.printer import print_label
from label_cog.src.coins_render import render_coins_image, render_wallet_image
from label_cog.src.coins import money_to_coins, coins_to_money
import asyncio


logger = setup_logger(__name__)


class AddCoinsView(discord.ui.View):
    def __init__(self, session):
        super().__init__(disable_on_timeout=True, timeout=300)  # 5 minutes timeout
        self.author = session.author
        self.lang = session.lang

        options = []
        for i in range(1, 25):
            options.append(discord.SelectOption(
                label=f"{i} CHF",
                value=str(i),
                emoji="💰"
            ))
        options[0].default = True
        self.coins_select = discord.ui.Select(
            options=options
        )
        self.coins_select.callback = self.coins_select_callback

        self.confirm_button = discord.ui.Button(
            row=3,
            label=get_translation("confirm_button_label", self.lang),
            custom_id="PrintBtn",
            style=discord.ButtonStyle.green,
            emoji="🖨️",
        )
        self.confirm_button.callback = self.confirm_button_callback

        self.cancel_button = discord.ui.Button(
            row=3,
            label=get_translation("cancel_button_label", self.lang),
            style=discord.ButtonStyle.secondary,
            emoji="🚫",
        )
        self.cancel_button.callback = self.cancel_button_callback

        self.add_item(self.coins_select)
        self.add_item(self.confirm_button)
        self.add_item(self.cancel_button)

    async def coins_select_callback(self, interaction):
        money = int(self.coins_select.values[0])
        set_current_value_as_default(self.coins_select, money)
        coins_count = money_to_coins(money)
        user_coins = await get_user_coins(self.author)
        coin_img = await asyncio.to_thread(render_coins_image, coins_count) #maybe combine this two in a thread
        thumbnail = await asyncio.to_thread(render_wallet_image, user_coins)
        await update_displayed_status_with_data(
            "coins_selected",
            {"coins": coins_count, "money": money, "total": user_coins + coins_count},
            self.lang,
            interaction=interaction,
            view=self,
            image=coin_img,
            thumbnail=thumbnail,
        )

    async def cancel_button_callback(self, interaction):
        await display_and_stop(self, interaction, "canceled")

    async def confirm_button_callback(self, interaction):
        money = int(self.coins_select.values[0])
        coins_count = money_to_coins(money)
        total_coins = await add_user_coins(interaction.user, coins_count)
        thumbnail = await asyncio.to_thread(render_wallet_image, await get_user_coins(self.author))
        await update_displayed_status_with_data(
            "coins_added",
            {"coins": coins_count, "total": total_coins},
            self.lang,
            interaction=interaction,
            thumbnail=thumbnail,
        )

