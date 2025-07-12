import os
import subprocess
from label_cog.src.config import Config
from label_cog.src.utils import get_local_directory

from label_cog.src.logging_dotenv import setup_logger
logger = setup_logger(__name__)


def is_admin(ctx):
    if Config().get("bocal_role_name") in ctx.author.roles.names_lower:
        return True
    unlimited_users = Config().get("unlimited_users")
    if unlimited_users is not None:
        logger.debug(f"unlimited_users: {unlimited_users}")
        for user in unlimited_users:
            logger.debug(f"user: {user}")
            if user.get("id") == ctx.author.id:
                return True
    return False


def launch_script(script):
    script_path = os.path.join(os.getcwd(), "scripts", script)
    os.chmod(script_path, 0o755) # make the script executable
    process = subprocess.Popen(['sudo', script_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()
    output = stdout.decode() + stderr.decode()
    return output


async def run_admin_script(ctx, script):
    if os.getenv("ENV") == "dev":
        await ctx.respond("This command is disabled in dev mode", ephemeral=True)
        return
    if not is_admin(ctx.author):
        await ctx.respond("You need to be from the bocal to use this command", ephemeral=True)
        return
    script_name = script.split(".")[0]
    await ctx.respond(f"Running the {script} script...")
    try:
        output = launch_script(script)
        await ctx.followup.send(f"{script_name} script ran successfully. Output:\n{output}")
    except Exception as e:
        await ctx.followup.send(f"Failed to run {script} script: {e}")
