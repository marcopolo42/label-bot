
import discord
from label_cog.src.utils import get_translation, get_lang


class CustomLabelModal(discord.ui.Modal):
    def __init__(self, label, lang):
        super().__init__(title=get_translation("custom_label_modal_title", lang), timeout=300)  # 5 minutes timeout
        self.label = label
        fields = label.template.fields

        if len(fields) > 5:
            raise ValueError("Too many extra fields, the modal can only handle 5 fields")
        for f in fields:
            if f.get("max_length") > 20:
                style = discord.InputTextStyle.long
            else:
                style = discord.InputTextStyle.short
            # check if the field has already been filled before and add the old value back
            previous_value = label.template.data.get(f.get("key"))
            if previous_value is not None:
                self.add_item(discord.ui.InputText(
                    label=get_lang(f.get("name"), lang),
                    max_length=f.get("max_length"),
                    placeholder=get_lang(f.get("placeholder"), lang),
                    style=style,
                    value=previous_value))
            else:
                self.add_item(discord.ui.InputText(
                    label=get_lang(f.get("name"), lang),
                    max_length=f.get("max_length"),
                    placeholder=get_lang(f.get("placeholder"), lang),
                    style=style))

    async def callback(self, interaction: discord.Interaction):
        for idx, item in enumerate(self.label.template.fields):
            self.label.template.data.update({item["key"]: self.children[idx].value})
            #easter egg
            # if the value contains a 69
            if "69" in self.children[idx].value:
                await interaction.response.send_message("69... Nice 😎👌🔥!", ephemeral=True)
            elif "42" in self.children[idx].value:
                await interaction.response.send_message("42... The answer to life, the universe, and everything 🌌🔥!", ephemeral=True)
            elif "gg" in self.children[idx].value.lower():
                await interaction.response.send_message("GG 🎮🔥!", ephemeral=True)
            elif "64" in self.children[idx].value:
                await interaction.response.send_message("64... Nintendo 64 🎮🔥!", ephemeral=True)
            elif "smash" in self.children[idx].value.lower():
                await interaction.response.send_message("Smash Bros 🎮🔥!", ephemeral=True)
            elif "canard" in self.children[idx].value.lower() or "duck" in self.children[idx].value.lower():
                await interaction.response.send_message("Quack 🦆🔥!", ephemeral=True)
            elif "pika" in self.children[idx].value.lower():
                await interaction.response.send_message("Pika Pika ⚡🔥!", ephemeral=True)
            else:
                await interaction.response.defer()