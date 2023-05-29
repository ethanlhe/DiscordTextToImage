from code import interact
import discord 
from discord import app_commands
from discord.ext import commands
import tensorflow as tf
import numpy
from stable_diffusion_tf.stable_diffusion import Text2Image
from PIL import Image
import time
import asyncio
import functools
from titlecase import titlecase
from transformers import pipeline
from datetime import datetime

import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3' # no warnings

'''
cluster_resolver = tf.distribute.cluster_resolver.TPUClusterResolver(tpu='local')
tf.tpu.experimental.initialize_tpu_system(cluster_resolver)
strategy = tf.distribute.TPUStrategy(cluster_resolver)

print("TPU's loaded, loading image generator")

with strategy.scope(): 
    generator = Text2Image( 
        img_height=512,
        img_width=512,
)
print("Image Generator loaded")
'''

print("Loading Text Generator")
text_generator = pipeline('text-generation', model='EleutherAI/gpt-neo-125M')
print("Loaded Text Generator")

queue = []

def make_image_embed(images, image_num, prompt, user):
    embed=discord.Embed(title=f"{titlecase(prompt)} ({image_num+1}/{len(images)})")
    embed.set_footer(text=user.display_name, icon_url=user.display_avatar.url)
    new_prompt = ''
    for letter in list(prompt):
        if letter.isalnum() or letter == ' ':
            new_prompt += letter
    prompt_dashes = new_prompt.replace(' ', '-')
    image = Image.fromarray(images[image_num])
    image.save("image.png")
    filename = f"{prompt_dashes}-{image_num+1}.png"
    file = discord.File("image.png", filename=filename)
    embed.set_image(url=f"attachment://{filename}")
    return file, embed

def make_text_embed(prompt, text, user):
    embed=discord.Embed(title=prompt, description=text)
    embed.set_footer(text=user.display_name, icon_url=user.display_avatar.url)
    return embed

class Prompt(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_ready(self):
        print("Prompt cog loaded")
    
    @commands.command()
    async def sync(self, ctx):
        fmt = await ctx.bot.tree.sync(guild=ctx.guild)
        await ctx.send(f'Synced {len(fmt)} commands in this server')
    
    @commands.command()
    async def global_sync(self, ctx):
        fmt = await ctx.bot.tree.sync()
        await ctx.send(f'Synced {len(fmt)} commands globally')
    
    @commands.command()
    async def hi(self, ctx):
        await ctx.channel.send("hey")

    class Menu(discord.ui.View):
        def __init__(self, images, prompt, user):
            super().__init__(timeout=None)
            self.images = images
            self.number = 0
            self.prompt = prompt
            self.user = user
            self.change_button_state("disable", "left")
        
        @discord.ui.button(label="⬅️", style=discord.ButtonStyle.blurple, custom_id="left")
        async def left(self, interaction, button):
            self.number -= 1
            if self.number == 0:
                self.change_button_state("disable", "left")
            self.change_button_state("enable", "right")
            file, embed = make_image_embed(self.images, self.number, self.prompt, self.user)
            await interaction.response.edit_message(embed=embed, attachments=[file], view=self)
        
        @discord.ui.button(label="➡️", style=discord.ButtonStyle.blurple, custom_id="right")
        async def right(self, interaction, button):
            self.number += 1
            if self.number == len(self.images)-1:
                self.change_button_state("disable", "right")
            self.change_button_state("enable", "left")
            file, embed = make_image_embed(self.images, self.number, self.prompt, self.user)
            await interaction.response.edit_message(embed=embed, attachments=[file], view=self)
        
        def change_button_state(self, operation, button_id): #operation is "enable" or "disable"
            for button in self.children:
                if button.custom_id == button_id: 
                    if operation == "enable":
                        button.disabled = False
                    elif operation == "disable":
                        button.disabled = True   

    def wait_until_position(self, interaction):
        queue.append([interaction, datetime.now()])
        position = 10000
        while queue[0][0] != interaction:
            if (datetime.now() - queue[0][1]).total_seconds() > 60:
                queue.pop(0) 
            temp_position = 1
            for temp_interaction, _ in queue:
                if temp_interaction == interaction:
                    break
                temp_position += 1
            if temp_position != position:
                position = temp_position
                print("Queue position:", interaction.command.qualified_name, position)
        print("Queue position:", [param.locale_name for param in interaction.command.parameters], 1)

    def gen_images(self, prompt, interaction):       
        #self.wait_until_position(interaction)    
        images = generator.generate(
            prompt,
            num_steps=50,
            batch_size=8
        )
        good_images = []
        for img in images:
            if numpy.average(img) != 124:
                good_images.append(img)
        queue.pop(0)
        return good_images
        
    @app_commands.command(name="image", description="Enter image prompt")
    async def image(self, interaction, prompt: str):
        await interaction.response.defer(thinking=True)
        loop = asyncio.get_running_loop()
        images = await loop.run_in_executor(None, functools.partial(
            self.gen_images, prompt = prompt, interaction=interaction
            ))
        view = self.Menu(images, prompt, interaction.user)
        file, embed = make_image_embed(images, 0, prompt, interaction.user)
        await interaction.followup.send(embed=embed, file=file, view=view)
    
    def gen_text(self, prompt, length, interaction):
        self.wait_until_position(interaction)    
        temperature = .7
        output = text_generator(prompt, do_sample=True, min_length=length, max_length=length, temperature=temperature)
        text = output[0]['generated_text']
        queue.pop(0)
        return text

    @app_commands.command(name="text", description="Generates text based on prompt")
    async def text(self, interaction, prompt: str, length: int = 50):
        await interaction.response.defer(thinking=True)
        title = prompt
        if length < 0:
            text = f"You entered {length} words. Please give a positive word length!"
            title = "Error"
        elif length <= 1000:
            loop = asyncio.get_running_loop()
            text = await loop.run_in_executor(None, functools.partial(
                self.gen_text, prompt=prompt, length=length, interaction=interaction
            ))
        else:
            text = f"You entered {length} words. The max word length is 100 words!"
            title = "Error"
        embed = make_text_embed(title, text, interaction.user)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="ping", description="testing if bot responds")
    async def ping(self, interaction):
        await interaction.response.send_message("pong")

async def setup(bot):
    await bot.add_cog(Prompt(bot), guilds=[discord.Object(id=975524755098714153), 
                                            discord.Object(id=999419811010453556), 
                                            discord.Object(id=937936836523884566),
                                            discord.Object(id=812413283738058802),
                                            discord.Object(id=964374335349473363)])

