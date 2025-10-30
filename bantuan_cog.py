# --- FILE: bantuan_cog.py (Perbaikan Final Context) ---
import discord
from discord.ext import commands
from discord import app_commands # Wajib ada

class BantuanCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="bantuan", description="Menampilkan daftar command.")
    # Context diubah dari 'ctx: discord.ApplicationContext' menjadi 'interaction: discord.Interaction'
    async def bantuan_command(self, interaction: discord.Interaction): 
        embed = discord.Embed(
            title="🧠 Panduan Couple Bot",
            description="Bot ini berfungsi untuk mencatat mood harian dan mengirim reminder. Semua command diawali `/`.",
            color=discord.Color.from_rgb(255, 192, 203)
        )
        embed.add_field(name="/setrole", value="Mengubah atau menetapkan peran kamu ('Ariel' atau 'Hira').", inline=False)
        embed.add_field(name="/mood", value="Menampilkan menu untuk memilih mood harian kamu.", inline=False)
        embed.add_field(name="/mood_summary", value="Menampilkan ringkasan mood mingguan kamu.", inline=False)
        embed.add_field(name="/remindme", value="Mengatur reminder pribadi (Contoh: /remindme 2h beli makan).", inline=False)
        embed.add_field(name="/language", value="Mengubah bahasa bot (ID/EN).", inline=False)
        embed.add_field(name="/bantuan", value="Menampilkan panduan ini.", inline=False)
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

# Fungsi setup wajib di bagian paling bawah
async def setup(bot):
    await bot.add_cog(BantuanCog(bot))