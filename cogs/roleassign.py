import discord
from discord.ext import commands
from discord import app_commands

class RoleButton(discord.ui.View):
    """Interactive Role Button System (Persistent)"""
    def __init__(self, roles_mapping):
        super().__init__(timeout=None)  # Keeps buttons active indefinitely
        self.roles_mapping = roles_mapping

        # ✅ Create buttons dynamically based on roles_mapping
        for role_name, (role_id, emoji, style) in roles_mapping.items():
            self.add_item(RoleButtonComponent(label=role_name, role_id=role_id, emoji=emoji, style=style))

class RoleButtonComponent(discord.ui.Button):
    """Handles Role Assignments on Button Click"""
    def __init__(self, label, role_id, emoji, style):
        super().__init__(label=label, emoji=emoji, style=style)
        self.role_id = role_id

    async def callback(self, interaction: discord.Interaction):
        """Toggles role assignment on button click"""
        role = interaction.guild.get_role(self.role_id)
        if not role:
            await interaction.response.send_message("❌ Role not found!", ephemeral=True)
            return

        if role in interaction.user.roles:
            await interaction.user.remove_roles(role)
            await interaction.response.send_message(f"❌ Removed **{role.name}**", ephemeral=True)
        else:
            await interaction.user.add_roles(role)
            await interaction.response.send_message(f"✅ Added **{role.name}**", ephemeral=True)

class RoleAssign(commands.Cog):
    """Cog to Send and Maintain the Static Role Panel"""
    def __init__(self, bot):
        self.bot = bot
        self.channel_id = 1051881515778330784  # ✅ Set this to your **static channel ID**
        self.message_id = None  # Stores the panel message ID

        # ✅ Define Slash Command Group for role management
        self.role_group = app_commands.Group(name="roles", description="Role-related commands")

    async def send_role_panel(self, interaction: discord.Interaction):
        """Sends or Updates the Role Selection Panel"""
        await interaction.response.defer()  # ✅ Prevents timeout error

        roles_mapping = {
            "she/her": (1180926555342520391, "🙋‍♀️", discord.ButtonStyle.grey),
            "he/him": (1180926504801144842, "🙋‍♂️", discord.ButtonStyle.grey),
            "they/them": (1180926463785054309, "🍓", discord.ButtonStyle.grey),
            "gamer": (1180926412757151865, "🎮", discord.ButtonStyle.green),
            "reader": (1180927124710895747, "📖", discord.ButtonStyle.green),
            "crafter": (1180927290486558731, "🖌️", discord.ButtonStyle.green),
            "memer": (1180927983314272306, "🐱", discord.ButtonStyle.green),
            "gym rat": (1284942903864590471, "💪", discord.ButtonStyle.green),
            "youtube ping": (1192109544688595046, "📺", discord.ButtonStyle.blurple),
            "twitch ping": (1192110341241454634, "🎥", discord.ButtonStyle.blurple),
            "7days ping": (1192698554255409173, "🧟", discord.ButtonStyle.blurple),
            "giveaway": (1192115461463220248, "🎁", discord.ButtonStyle.red),
            "developer": (1350509521352659024, "💡", discord.ButtonStyle.green),
        }

        view = RoleButton(roles_mapping)
        embed = discord.Embed(
            title="🌟 **Choose Your Roles**",
            description="Click a button below to add/remove a role!\nRoles update instantly.",
            color=discord.Color.blue(),
        )

        channel = self.bot.get_channel(self.channel_id)
        if not channel:
            await interaction.followup.send("❌ Role channel not found!", ephemeral=True)
            return
        
        # ✅ Send new role panel
        message = await channel.send(embed=embed, view=view)
        self.message_id = message.id
        await interaction.followup.send("✅ Role panel updated!", ephemeral=True)

    @app_commands.command(name="setup", description="Sets up the role selection panel.")
    @app_commands.default_permissions(administrator=True)  # ✅ Restrict to admins
    @app_commands.guild_only()  # ✅ Ensure it's only usable in a server
    async def setup_role_panel(self, interaction: discord.Interaction):
        """Slash command to manually update the Role Panel"""
        await self.send_role_panel(interaction)


    async def cog_load(self):
        """Registers the slash command group dynamically"""
        if not self.bot.tree.get_command("roles"):
            self.bot.tree.add_command(self.role_group)

    async def cog_unload(self):
        """Cleanup when cog is unloaded"""
        self.bot.tree.remove_command("roles")

async def setup(bot):
    await bot.add_cog(RoleAssign(bot))