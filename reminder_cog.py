# --- FILE: reminder_cog.py ---
import discord
from discord.ext import commands
from discord import app_commands
import asyncio
from datetime import datetime, timedelta
import pytz

class ReminderCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Format {user_id: [ (datetime_target, message, channel_id, task) ]}
        self.one_time_reminders = {} 

    @app_commands.command(name="remindme", description="Set reminder pribadi (one-time). Contoh: /remindme 30m beli makanan")
    @app_commands.describe(duration="Contoh: 30m, 2h, 1d", message="Pesan reminder kamu")
    async def remindme(self, interaction: discord.Interaction, duration: str, message: str):
        user_role, partner_role, partner_id, partner_channel_id = await self.bot.get_partner_info(interaction.user.id)
        
        if not user_role:
            return await interaction.response.send_message("⚠️ Kamu belum menetapkan role. Gunakan tombol di pesan perkenalan bot.", ephemeral=True)

        user_id = interaction.user.id
        
        try:
            unit = duration[-1].lower()
            value = int(duration[:-1])
            
            if unit == 'm':
                delta = timedelta(minutes=value)
            elif unit == 'h':
                delta = timedelta(hours=value)
            elif unit == 'd':
                delta = timedelta(days=value)
            else:
                return await interaction.response.send_message("⚠️ Format durasi salah. Gunakan m (menit), h (jam), atau d (hari).", ephemeral=True)

            target_time = datetime.now(pytz.timezone('Asia/Jakarta')) + delta
            
            await interaction.response.send_message(f"✅ Reminder diset untuk **{target_time.strftime('%H:%M WIB')}** - Pesan: '{message}'", ephemeral=True)

            async def send_reminder():
                await asyncio.sleep(delta.total_seconds())
                channel = self.bot.get_channel(interaction.channel_id)
                if channel:
                    await channel.send(f"⏰ {interaction.user.mention} Reminder: **{message}**")
                
                if user_id in self.one_time_reminders:
                    self.one_time_reminders[user_id] = [r for r in self.one_time_reminders[user_id] if r[3] != current_task]

            current_task = self.bot.loop.create_task(send_reminder())
            
            if user_id not in self.one_time_reminders:
                self.one_time_reminders[user_id] = []
            self.one_time_reminders[user_id].append((target_time, message, interaction.channel_id, current_task))


        except ValueError:
            await interaction.response.send_message("⚠️ Format durasi salah. Contoh: 30m, 2h.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"⚠️ Terjadi error: {e}", ephemeral=True)


async def setup(bot):
    await bot.add_cog(ReminderCog(bot))