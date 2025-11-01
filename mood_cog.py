import discord
from discord.ext import commands, tasks
import aiosqlite
from datetime import datetime, timedelta, time
import pytz
from discord.ui import View, Select
from discord import app_commands

MOOD_MAP = {
    '😭': 'Crying', '😢': 'Sad', '😐': 'Flat', '🙂': 'Smile', '😁': 'Happy',
    '😠': 'Angry / Mad', '📞': 'Need Call'
}
DB_PATH = "couple_bot.db"


class MoodSelectView(View):
    def __init__(self, bot, partner_id, partner_role):
        super().__init__(timeout=None)
        self.bot = bot
        self.partner_id = partner_id
        self.partner_role = partner_role

        options = [discord.SelectOption(label=f"{emoji} {name}", value=emoji)
                   for emoji, name in MOOD_MAP.items()]
        select = Select(placeholder="Pilih mood kamu hari ini...",
                        options=options, custom_id="mood_select")
        select.callback = self.mood_select_callback
        self.add_item(select)

    async def mood_select_callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        mood_emoji = interaction.data['values'][0]
        mood_name = MOOD_MAP.get(mood_emoji, 'Unknown')
        user_id = interaction.user.id
        today = datetime.now(pytz.timezone('Asia/Jakarta')).strftime('%Y-%m-%d')

        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                "INSERT OR REPLACE INTO moods (user_id, date, mood_level) VALUES (?, ?, ?)",
                (user_id, today, mood_emoji)
            )
            await db.commit()

        user_role, partner_role, partner_id, partner_channel_id = await self.bot.get_partner_info(user_id)

        notification_message = None
        if mood_emoji in ['😭', '😢', '😠']:
            notification_message = f"{self.bot.get_user(partner_id).mention}, {interaction.user.mention} feels **{mood_emoji} {mood_name}** today. Please check on them."
        elif mood_emoji == '📞':
            notification_message = f"{self.bot.get_user(partner_id).mention}, hop on a call — {interaction.user.mention} needs you! **{mood_emoji}**"

        if notification_message and partner_channel_id:
            partner_channel = self.bot.get_channel(partner_channel_id)
            if partner_channel:
                await partner_channel.send(notification_message)

        await interaction.followup.send(
            f"✅ Mood hari ini ({today}) kamu adalah **{mood_emoji} {mood_name}**.",
            ephemeral=True
        )


class MoodCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.get_partner_info = self.get_partner_info
        self.bot.get_channel_id_by_role = self.get_channel_id_by_role
        self.daily_mood_check.start()

    def cog_unload(self):
        self.daily_mood_check.cancel()

    async def get_partner_info(self, user_id):
        async with aiosqlite.connect(DB_PATH) as db:
            cursor = await db.execute("SELECT role_name FROM users WHERE user_id = ?", (user_id,))
            user_role_row = await cursor.fetchone()
            if not user_role_row:
                return None, None, None, None
            user_role = user_role_row[0]
            partner_role = 'Ariel' if user_role == 'Hira' else 'Hira'
            cursor = await db.execute("SELECT user_id, personal_channel_id FROM users WHERE role_name = ?", (partner_role,))
            partner_data = await cursor.fetchone()
            if partner_data:
                return user_role, partner_role, partner_data[0], partner_data[1]
            return user_role, partner_role, None, None

    async def get_channel_id_by_role(self, role_name):
        async with aiosqlite.connect(DB_PATH) as db:
            cursor = await db.execute("SELECT personal_channel_id FROM users WHERE role_name = ?", (role_name,))
            result = await cursor.fetchone()
            return result[0] if result else None

    @tasks.loop(time=time(21, 0, 0, tzinfo=pytz.timezone('Asia/Jakarta')))
    async def daily_mood_check(self):
        async with aiosqlite.connect(DB_PATH) as db:
            cursor = await db.execute("SELECT user_id, personal_channel_id FROM users")
            users = await cursor.fetchall()

        for user_id, channel_id in users:
            user = self.bot.get_user(user_id) or await self.bot.fetch_user(user_id)
            channel = self.bot.get_channel(channel_id)
            if not user or not channel:
                continue

            user_role, partner_role, partner_id, _ = await self.get_partner_info(user_id)
            if not partner_id:
                await channel.send("ℹ️ Mood Check dilewati: Partner kamu belum terdaftar.")
                continue

            view = MoodSelectView(self.bot, partner_id, partner_role)
            await channel.send(f"**{user.mention}, waktunya cek mood hari ini!** 📝", view=view)

    @app_commands.command(name="mood", description="Cek dan masukkan mood harian kamu.")
    async def mood_command(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        user_role, partner_role, partner_id, _ = await self.get_partner_info(interaction.user.id)

        if not user_role or not partner_id:
            return await interaction.followup.send("⚠️ Kamu atau partner kamu belum menetapkan role.", ephemeral=True)

        view = MoodSelectView(self.bot, partner_id, partner_role)
        await interaction.followup.send("Pilih mood kamu hari ini:", view=view, ephemeral=True)

    @app_commands.command(name="mood_summary", description="Lihat ringkasan mood mingguan kamu.")
    async def mood_summary(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        user_id = interaction.user.id
        today = datetime.now(pytz.timezone('Asia/Jakarta'))
        start_of_week = (today - timedelta(days=today.weekday())).strftime('%Y-%m-%d')

        async with aiosqlite.connect(DB_PATH) as db:
            cursor = await db.execute(
                "SELECT date, mood_level FROM moods WHERE user_id = ? AND date >= ? ORDER BY date ASC",
                (user_id, start_of_week))
            history = await cursor.fetchall()

        if not history:
            return await interaction.followup.send("Belum ada data mood minggu ini.", ephemeral=True)

        summary = "\n".join([f"{date}: {MOOD_MAP.get(mood, mood)}" for date, mood in history])
        await interaction.followup.send(f"🗓️ **Mood Summary Minggu Ini:**\n{summary}", ephemeral=True)

    @app_commands.command(name="testmood", description="Memaksa menjalankan pengecekan mood harian.")
    async def testmood_command(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        await self.daily_mood_check()
        await interaction.followup.send("✅ Pengecekan mood harian telah dijalankan!", ephemeral=True)

    @app_commands.command(name="checkdata", description="Mengecek data role kamu di database.")
    async def check_data_command(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        async with aiosqlite.connect(DB_PATH) as db:
            cursor = await db.execute("SELECT role_name FROM users WHERE user_id = ?", (interaction.user.id,))
            result = await cursor.fetchone()

        if result:
            await interaction.followup.send(f"✅ Data kamu tersimpan! Role kamu: **{result[0]}**", ephemeral=True)
        else:
            await interaction.followup.send("❌ Data kamu belum tersimpan. Gunakan /setrole.", ephemeral=True)


async def setup(bot):
    await bot.add_cog(MoodCog(bot))
