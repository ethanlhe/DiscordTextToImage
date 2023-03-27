import discord 
from discord import app_commands
from discord.ext import commands
import tensorflow as tf
import numpy
from stable_diffusion_tf.stable_diffusion import Text2Image
from PIL import Image
import time
import asyncio

cluster_resolver = tf.distribute.cluster_resolver.TPUClusterResolver(tpu='local')
tf.tpu.experimental.initialize_tpu_system(cluster_resolver)
strategy = tf.distribute.TPUStrategy(cluster_resolver)

print("TPU's loaded, loading generator")

with strategy.scope(): 
    generator = Text2Image( 
        img_height=512,
        img_width=512,
)
print("Generator loaded")

def make_embed(images, image_num, prompt):
    image = Image.fromarray(images[image_num])
    image.save("image.png")
    embed=discord.Embed(title=f"{prompt} ({image_num+1}/{len(images)})")
    file = discord.File("image.png", filename=f"image-{image_num}.png")
    embed.set_image(url=f"attachment://image-{image_num}.png")
    return file, embed

class Prompt(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_ready(self):
        print("Prompt cog loaded")
    
    @commands.command()
    async def sync(self, ctx):
        fmt = await ctx.bot.tree.sync(guild=ctx.guild)
        await ctx.send(f'Synced {len(fmt)} commands')
    
    @commands.command()
    async def hi(self, ctx):
        await ctx.channel.send("hey")

    class Menu(discord.ui.View):
        def __init__(self, images, prompt):
            super().__init__()
            self.images = images
            self.number = 0
            self.prompt = prompt
            self.change_button_state("disable", "left")
        
        @discord.ui.button(label="⬅️", style=discord.ButtonStyle.grey, custom_id="left")
        async def left(self, interaction, button):
            self.number -= 1
            if self.number == 0:
                self.change_button_state("disable", "left")
            self.change_button_state("enable", "right")
            file, embed = make_embed(self.images, self.number, self.prompt)
            await interaction.response.edit_message(embed=embed, attachments=[file], view=self)
        
        @discord.ui.button(label="➡️", style=discord.ButtonStyle.grey, custom_id="right")
        async def right(self, interaction, button):
            self.number += 1
            if self.number == len(self.images)-1:
                self.change_button_state("disable", "right")
            self.change_button_state("enable", "left")
            file, embed = make_embed(self.images, self.number, self.prompt)
            await interaction.response.edit_message(embed=embed, attachments=[file], view=self)
        
        def change_button_state(self, operation, button_id): #operation is "enable" or "disable"
            for button in self.children:
                if button.custom_id == button_id: 
                    if operation == "enable":
                        button.disabled = False
                    elif operation == "disable":
                        button.disabled = True    

    async def gen_images(self, prompt):   
        images = generator.generate(
            prompt,
            num_steps=50,
            batch_size=8
        )
        good_images = []
        for img in images:
            if numpy.average(img) != 124:
                good_images.append(img)
        return good_images
    
    @app_commands.command(name="prompt", description="enter image prompt")
    async def prompt(self, interaction, prompt: str):
        #SHIKHAR_ID = 711351178146873344
        #if not ctx.message.guild and ctx.message.author.id != SHIKHAR_ID:
        #    await ctx.message.reply("Don't use this bot in DM's, use it in the server please!")
        #    return
        await interaction.response.defer(thinking=True)
        images = await self.gen_images(prompt)
        view = self.Menu(images, prompt)
        file, embed = make_embed(images, 0, prompt)
        await interaction.followup.send(embed=embed, file=file, view=view)

async def setup(bot):
    await bot.add_cog(Prompt(bot), guilds=[discord.Object(id=975524755098714153), discord.Object(id=999419811010453556)])

