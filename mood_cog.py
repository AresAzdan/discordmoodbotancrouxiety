# --- FILE: mood_cog.py (Final Fix) ---
import discord
from discord.ext import commands, tasks
import aiosqlite
from datetime import datetime, timedelta, time # <-- Ditambahkan 'time'
import pytz
from discord.ui import View, Select
from discord import app_commands

# --- MOOD CONFIG ---
MOOD_MAP = {
    '😭': 'Crying',
    '😢': 'Sad',
    '😐': 'Flat',
    '🙂': 'Smile',
    '😁': 'Happy',
    '😠': 'Angry / Mad',
    '📞': 'Need Call'
}
DB_PATH = "couple_bot.db"


class MoodSelectView(View):
    def __init__(self, bot, partner_id, partner_role):
        super().__init__(timeout=None)
        self.bot = bot
        self.partner_id = partner_id
        self.partner_role = partner_role
        
        options = [
            discord.SelectOption(label=f"{emoji} {name}", value=emoji) 
            for emoji, name in MOOD_MAP.items()
        ]
        
        self.add_item(self.create_mood_select(options))

    def create_mood_select(self, options):
        select = Select(placeholder="Pilih mood kamu hari ini...", options=options, custom_id="mood_select")
        select.callback = self.mood_select_callback
        return select

    async def mood_select_callback(self, interaction: discord.Interaction):
        mood_emoji = interaction.data['values'][0]
        mood_name = MOOD_MAP.get(mood_emoji, 'Unknown')
        user_id = interaction.user.id
        today = datetime.now(pytz.timezone('Asia/Jakarta')).strftime('%Y-%m-%d')
        
        await interaction.response.send_message(f"✅ Mood hari ini ({today}) kamu adalah **{mood_emoji} {mood_name}**.", ephemeral=False)

        # --- Simpan Mood ---
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                "INSERT OR REPLACE INTO moods (user_id, date, mood_level) VALUES (?, ?, ?)",
                (user_id, today, mood_emoji)
            )
            await db.commit()

        # --- Partner Notification Logic ---
        notification_message = None
        
        if mood_emoji in ['😭', '😢', '😠']:
            notification_message = f"{self.bot.get_user(self.partner_id).mention}, {interaction.user.mention} feels **{mood_emoji} {mood_name}** today. Please check on them."
        
        elif mood_emoji == '📞':
            notification_message = f"{self.bot.get_user(self.partner_id).mention}, hop on the voice channel — {interaction.user.mention} needs a call! **{mood_emoji}**"

        if notification_message:
            partner_channel_id = await self.bot.get_channel_id_by_role(self.partner_role)
            if partner_channel_id:
                partner_channel = self.bot.get_channel(partner_channel_id)
                if partner_channel:
                    await partner_channel.send(notification_message)


class MoodCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.get_partner_info = self.get_partner_info
        self.bot.get_channel_id_by_role = self.get_channel_id_by_role

        self.daily_mood_check.start()

    def cog_unload(self):
        self.daily_mood_check.cancel()

    # --- FILE: mood_cog.py ---

# ... (Baris 84: self.daily_mood_check.cancel())
# Baris 85: 
    # --- MULAI TAMBAHKAN KODE INI DI BARIS INI ---
    @app_commands.command(name="testmood", description="Memaksa menjalankan pengecekan mood harian (khusus admin).")
    async def testmood_command(self, interaction: discord.Interaction):
        # Cek apakah user adalah pemilik server (admin) sebelum memicu     
        # Panggil fungsi task loop secara langsung
        # Perhatikan: Tidak perlu await di sini karena daily_mood_check adalah task loop.
        # Tapi kita bisa memanggil fungsi di dalamnya untuk tes.
        
        # Opsi yang lebih aman adalah memanggil logic di dalam task:
        await self.daily_mood_check.callback() # <-- Panggil fungsi di dalam task loop
        
        await interaction.response.send_message("✅ Pengecekan mood harian (21:00 WIB) telah dipicu secara manual!", ephemeral=True)
    @app_commands.command(name="checkdata", description="Mengecek data role kamu di database.")
    async def check_data_command(self, interaction: discord.Interaction):
        # Gunakan DB_PATH yang sudah didefinisikan di atas
        async with aiosqlite.connect(DB_PATH) as db: 
            # Menggunakan nama tabel 'users' dan kolom 'role_name' yang sudah benar
            cursor = await db.execute("SELECT role_name FROM users WHERE user_id = ?", (interaction.user.id,)) 
            result = await cursor.fetchone()
            
        if result:
            await interaction.response.send_message(f"✅ Data kamu tersimpan! Role kamu: **{result[0]}**", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Data kamu BELUM tersimpan di database. Silakan gunakan /setrole lagi.", ephemeral=True)
    # --- LANJUT KE FUNGSI HELPER (async def get_partner_info...) ---
    # --- HELPER FUNCTIONS ---

    async def get_partner_info(self, user_id):
        async with aiosqlite.connect(DB_PATH) as db:
            cursor = await db.execute("SELECT role_name FROM users WHERE user_id = ?", (user_id,))
            user_role_row = await cursor.fetchone()
            
            if not user_role_row:
                return None, None, None, None
            
            user_role = user_role_row[0]
            # Harus disesuaikan dengan role di main.py
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

    # --- TASK HARIAN (Pukul 21:00 WIB) ---

    @tasks.loop(time=time(21, 0, 0, tzinfo=pytz.timezone('Asia/Jakarta')))
    async def daily_mood_check(self):
        async with aiosqlite.connect(DB_PATH) as db:
            cursor = await db.execute("SELECT user_id, personal_channel_id FROM users")
            users = await cursor.fetchall()
            
            for user_id, channel_id in users:
                user = self.bot.get_user(user_id) or await self.bot.fetch_user(user_id)
                channel = self.bot.get_channel(channel_id)

                if user and channel:
                    user_role, partner_role, partner_id, _ = await self.get_partner_info(user_id)
                    
                    if partner_id:
                        view = MoodSelectView(self.bot, partner_id, partner_role)
                        await channel.send(f"**{user.mention}, waktunya cek mood hari ini!** 📝", view=view)


    # --- SLASH COMMAND /mood ---

    @app_commands.command(name="mood", description="Cek dan masukkan mood harian kamu.")
    async def mood_command(self, interaction: discord.Interaction): # <-- FIX Context
        user_role, partner_role, partner_id, _ = await self.get_partner_info(interaction.user.id)
        
        if not user_role or not partner_id:
            return await interaction.response.send_message("⚠️ Kamu atau partner kamu belum menetapkan role. Silakan gunakan tombol di pesan perkenalan bot.", ephemeral=True)

        view = MoodSelectView(self.bot, partner_id, partner_role)
        await interaction.response.send_message("Pilih mood kamu hari ini:", view=view, ephemeral=True)


    # --- SLASH COMMAND /mood_summary ---

    @app_commands.command(name="mood_summary", description="Lihat ringkasan mood mingguan kamu.")
    async def mood_summary(self, interaction: discord.Interaction): # <-- FIX Context
        user_id = interaction.user.id
        today = datetime.now(pytz.timezone('Asia/Jakarta'))
        start_of_week = (today - timedelta(days=today.weekday())).strftime('%Y-%m-%d')

        async with aiosqlite.connect(DB_PATH) as db:
            cursor = await db.execute("""
                SELECT date, mood_level FROM moods 
                WHERE user_id = ? AND date >= ? ORDER BY date DESC
            """, (user_id, start_of_week))
            history = await cursor.fetchall()

        if not history:
            return await interaction.response.send_message("Belum ada data mood minggu ini.", ephemeral=True)

        summary_text = "**Ringkasan Mood Mingguan:**\n"
        mood_counts = {emoji: 0 for emoji in MOOD_MAP.keys()}

        for date_str, mood in history:
            mood_counts[mood] += 1
            summary_text += f"- {date_str}: {mood} {MOOD_MAP[mood]}\n"

        summary_text += "\n**Total Mood:**\n"
        for emoji, count in mood_counts.items():
            if count > 0:
                summary_text += f" {emoji} {count} kali | "

        await interaction.response.send_message(summary_text, ephemeral=True)


async def setup(bot):

    await bot.add_cog(MoodCog(bot)) # WAJIB PAKE 'await' dan 'async'


