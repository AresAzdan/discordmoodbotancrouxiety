# --- FILE: language_cog.py ---
import discord
from discord.ext import commands
from discord import app_commands
import aiosqlite

DB_PATH = "couple_bot.db"

class LanguageCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.get_user_language = self.get_user_language

    async def get_user_language(self, user_id):
        """Mendapatkan bahasa dari database."""
        async with aiosqlite.connect(DB_PATH) as db:
            cursor = await db.execute("SELECT language FROM users WHERE user_id = ?", (user_id,))
            result = await cursor.fetchone()
            return result[0] if result else 'en'

    @app_commands.command(name="language", description="Mengubah bahasa bot (ID/EN).")
    @app_commands.describe(lang_code="Pilih 'id' untuk Indonesia atau 'en' untuk English")
    async def set_language(self, interaction: discord.Interaction, lang_code: str):
        lang_code = lang_code.lower()
        if lang_code not in ['id', 'en']:
            return await interaction.response.send_message("⚠️ Pilih 'id' atau 'en' saja.", ephemeral=True)
        
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("UPDATE users SET language = ? WHERE user_id = ?", (lang_code, interaction.user.id))
            await db.commit()
        
        if lang_code == 'id':
            msg = "✅ Bahasa berhasil diubah ke Bahasa Indonesia."
        else:
            msg = "✅ Language successfully set to English."
            
        await interaction.response.send_message(msg, ephemeral=True)

async def setup(bot):
    await bot.add_cog(LanguageCog(bot))