import os
import discord
from discord.ext import commands

TOKEN = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.default()
intents.messages = True
bot = commands.Bot(command_prefix='!', intents=intents)

checklists = {}

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')

@bot.command(name='create_checklist')
async def create_checklist(ctx, *, title):
    checklists[ctx.channel.id] = {'title': title, 'items': []}
    await ctx.send(f'Checklist **{title}** created! Use `!add_item Your Item` to add items.')

@bot.command(name='add_item')
async def add_item(ctx, *, item):
    if ctx.channel.id not in checklists:
        await ctx.send("No checklist found. Create one with `!create_checklist`.")
        return

    checklists[ctx.channel.id]['items'].append({'item': item, 'checked': False})
    await ctx.send(f'Added item: {item}')
    await show_checklist(ctx)

@bot.command(name='show_checklist')
async def show_checklist(ctx):
    if ctx.channel.id not in checklists:
        await ctx.send("No checklist found. Create one with `!create_checklist`.")
        return

    checklist = checklists[ctx.channel.id]
    response = f"**{checklist['title']}**\n"
    for idx, entry in enumerate(checklist['items']):
        checkbox = '✅' if entry['checked'] else '⬜'
        item = entry['item']
        if entry['checked']:
            item = f'~~{item}~~'
        response += f"{idx + 1}. {checkbox} {item}\n"

    message = await ctx.send(response)
    for idx in range(len(checklist['items'])):
        await message.add_reaction('⬜')
        await message.add_reaction('✅')

@bot.event
async def on_reaction_add(reaction, user):
    if user.bot:
        return

    message = reaction.message
    if message.author != bot.user:
        return

    if reaction.emoji not in ['⬜', '✅']:
        return

    ctx = await bot.get_context(message)
    if ctx.channel.id not in checklists:
        return

    checklist = checklists[ctx.channel.id]
    lines = message.content.split('\n')
    for idx, line in enumerate(lines[1:], 1):
        if reaction.emoji == '⬜' and '⬜' in line:
            checklist['items'][idx - 1]['checked'] = True
        elif reaction.emoji == '✅' and '✅' in line:
            checklist['items'][idx - 1]['checked'] = False

    await message.delete()
    await show_checklist(ctx)

bot.run(TOKEN)
