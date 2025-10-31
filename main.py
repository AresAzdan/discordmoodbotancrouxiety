# --- FILE: main.py (Final Fix) ---
import os
# ... setelah semua import ...
from flask import Flask  # Tambah Flask
import threading  # Tambah Threading (untuk menjalankan web server)
# ...
import discord
from discord.ext import commands, tasks
import aiosqlite
import pytz
from discord.ui import View, Button
from datetime import time
from discord import app_commands

# --- KONFIGURASI UMUM ---
TOKEN = os.environ.get('mood_token_bot')  # GANTI TOKEN KAMU DI SINI
DB_PATH = "couple_bot.db"
TIMEZONE = pytz.timezone('Asia/Jakarta')
START_TIME_WIB = time(21, 0, 0, tzinfo=TIMEZONE)

# --- INTENTS & BOT SETUP ---
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="/", intents=intents, help_command=None)


# --- DATABASE SETUP ---
async def setup_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                role_name TEXT, 
                personal_channel_id INTEGER,
                language TEXT DEFAULT 'en'
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS moods (
                user_id INTEGER,
                date TEXT,
                mood_level TEXT,
                PRIMARY KEY (user_id, date)
            )
        """)
        await db.commit()


# --- ROLE SELECTION VIEW ---


class RoleSelectView(View):

    def __init__(self, bot, role_a_name, role_b_name):
        super().__init__(timeout=None)
        self.bot = bot
        self.role_a_name = role_a_name
        self.role_b_name = role_b_name
        self.add_item(
            self.create_role_button(role_a_name, discord.ButtonStyle.green))
        self.add_item(
            self.create_role_button(role_b_name, discord.ButtonStyle.blurple))

    def create_role_button(self, label, style):
        button = Button(label=label,
                        style=style,
                        custom_id=f"role_{label.lower().replace(' ', '_')}")
        button.callback = self.role_button_callback
        return button

    async def role_button_callback(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        role_name = interaction.data['custom_id'].replace('role_', '').replace(
            '_', ' ').title()

        async with aiosqlite.connect(DB_PATH) as db:
            # Cek apakah role tersebut sudah diambil partner
            partner_role = self.role_a_name if role_name == self.role_b_name else self.role_b_name
            cursor = await db.execute(
                "SELECT user_id FROM users WHERE role_name = ? AND user_id != ?",
                (role_name, user_id))
            partner_assigned = await cursor.fetchone()

            if partner_assigned:
                await interaction.response.send_message(
                    f"⚠️ Role **{role_name}** sudah diambil oleh partner kamu! Silakan pilih role **{partner_role}**.",
                    ephemeral=True)
                return

            # --- Buat Personal Channel ---
            try:
                guild = interaction.guild
                channel_name = f"💌-{role_name}-{interaction.user.name.lower()}"

                personal_channel = await guild.create_text_channel(
                    channel_name,
                    overwrites={
                        guild.default_role:
                        discord.PermissionOverwrite(read_messages=False),
                        interaction.user:
                        discord.PermissionOverwrite(read_messages=True,
                                                    send_messages=True),
                        guild.me:
                        discord.PermissionOverwrite(read_messages=True,
                                                    send_messages=True)
                    })
                channel_id = personal_channel.id
            except Exception as e:
                await interaction.response.send_message(
                    f"❌ Gagal membuat channel pribadi. Pastikan bot memiliki permission 'Manage Channels'. Error: {e}",
                    ephemeral=True)
                return

            # --- Simpan data ke DB ---
            await db.execute(
                "INSERT OR REPLACE INTO users (user_id, role_name, personal_channel_id) VALUES (?, ?, ?)",
                (user_id, role_name, channel_id))
            await db.commit()

            await interaction.response.send_message(
                f"✅ Role **{role_name}** berhasil ditetapkan untuk {interaction.user.mention} dan channel pribadi `{personal_channel.name}` dibuat!",
                ephemeral=True)

            # Kirim pesan perkenalan ke channel pribadi
            await personal_channel.send(
                f"Halo {interaction.user.mention}! Ini adalah channel pribadimu. Semua **Mood Check** dan **Reminder** akan muncul di sini. Gunakan `/mood` untuk cek mood dan `/bantuan` untuk petunjuk lebih lanjut."
            )


# --- BOT EVENTS DAN COMMANDS BAWAAN ---


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    await setup_db()

    # Load Cogs
    try:
        await bot.load_extension('mood_cog')
        await bot.load_extension('bantuan_cog')
        await bot.load_extension('language_cog'
                                 )  # Ditambahkan untuk fitur bahasa
        await bot.load_extension('reminder_cog'
                                 )  # Ditambahkan untuk fitur reminder
    except commands.ExtensionFailed as e:
        print(f"ERROR LOADING COG: {e}")

    # Sync tree commands
    await bot.tree.sync()


@bot.event
async def on_guild_join(guild):
    role_a = "Ariel"
    role_b = "Hira"

    embed = discord.Embed(
        title="Hi! I am baymax, your personal healthcare companion",
        description=
        f"Selamat datang! Untuk memulai, silakan **pilih peran** kamu di bawah. Pilihan peran: **{role_a}** atau **{role_b}**.",
        color=discord.Color.from_rgb(255, 192, 203))

    target_channel = next((c for c in guild.text_channels
                           if c.permissions_for(guild.me).send_messages), None)

    if target_channel:
        await target_channel.send(embed=embed,
                                  view=RoleSelectView(bot, role_a, role_b))


# --- COMMAND SETROLE (Diperbaiki) ---
@bot.tree.command(name="setrole",
                  description="Mengubah atau menetapkan peran pasangan kamu.")
@app_commands.describe(role_name="Pilih 'Ariel' atau 'Hira'")
async def setrole_command(interaction: discord.Interaction, role_name: str):
    """Mengubah atau menetapkan peran pasangan kamu. (Untuk ganti peran)"""
    role_name = role_name.title()
    if role_name not in ["Ariel", "Hira"]:
        return await interaction.response.send_message(
            "⚠️ Peran harus 'Ariel' atau 'Hira'.", ephemeral=True)

    view = RoleSelectView(bot, "Ariel", "Hira")

    # Simulasikan callback
    interaction.data = {'custom_id': f"role_{role_name.lower()}"}

    await view.role_button_callback(interaction)


# ... (Akhir dari semua command bot kamu) ...

# --- LOGIC UNTUK KEEP-ALIVE 24/7 ---
web = Flask(__name__)


@web.route('/')
def index():
    return 'Bot is alive!'


def run_web_server():
    # Web server berjalan di background
    web.run(host='0.0.0.0', port=5000)


# Jalankan web server di thread terpisah (agar tidak memblokir bot)
t = threading.Thread(target=run_web_server)
t.start()

# --- JALANKAN BOT (INI HARUS BARIS PALING AKHIR) ---
bot.run(TOKEN)
