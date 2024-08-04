import os
from dotenv import load_dotenv
from opencensus.ext.azure.log_exporter import AzureLogHandler
from opencensus.ext.azure.trace_exporter import AzureExporter
from opencensus.ext.requests import requests_trace
from opencensus.trace.samplers import ProbabilitySampler
from opencensus.trace.tracer import Tracer
import logging
import discord
from discord.ext import commands

# Configure logging
logging.basicConfig(level=logging.INFO, filename='app.log', filemode='a', format='%(name)s - %(levelname)s - %(message)s')

logging.info('This is an informational message.')
logging.error('This is an error message.')

# Load the bot token and App Insights Instrumentation Key from environment variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
INSTRUMENTATION_KEY = os.getenv('APPINSIGHTS_INSTRUMENTATIONKEY')

# Configure logging
logging.basicConfig(level=logging.INFO, handlers=[AzureLogHandler(connection_string=f'InstrumentationKey={INSTRUMENTATION_KEY}')])

# Set up tracing
tracer = Tracer(exporter=AzureExporter(connection_string=f'InstrumentationKey={INSTRUMENTATION_KEY}'), sampler=ProbabilitySampler(1.0))
requests_trace.trace_integration(tracer)

# Set up bot intents and create a bot instance
intents = discord.Intents.default()
intents.messages = True
bot = commands.Bot(command_prefix='!', intents=intents)

# In-memory storage for checklists
checklists = {}

@bot.event
async def on_ready():
    """Event called when the bot has successfully connected to Discord."""
    logging.info(f'Logged in as {bot.user}')
    print(f'Logged in as {bot.user}')

@bot.command(name='create_checklist')
async def create_checklist(ctx, *, title):
    """Command to create a new checklist."""
    try:
        checklists[ctx.channel.id] = {'title': title, 'items': []}
        await ctx.send(f'Checklist **{title}** created! Use `!add_item Your Item` to add items.')
        logging.info(f'Checklist created: {title}')
    except Exception as e:
        await ctx.send("An error occurred while creating the checklist.")
        logging.error(f"Error in create_checklist: {e}")

@bot.command(name='add_item')
async def add_item(ctx, *, item):
    """Command to add an item to the current checklist."""
    try:
        if ctx.channel.id not in checklists:
            await ctx.send("No checklist found. Create one with `!create_checklist`.")
            return

        checklists[ctx.channel.id]['items'].append({'item': item, 'checked': False})
        await ctx.send(f'Added item: {item}')
        await show_checklist(ctx)
        logging.info(f'Item added: {item}')
    except Exception as e:
        await ctx.send("An error occurred while adding the item.")
        logging.error(f"Error in add_item: {e}")

@bot.command(name='show_checklist')
async def show_checklist(ctx):
    """Command to display the current checklist."""
    try:
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
        logging.info('Checklist displayed')
    except Exception as e:
        await ctx.send("An error occurred while displaying the checklist.")
        logging.error(f"Error in show_checklist: {e}")

@bot.event
async def on_reaction_add(reaction, user):
    """Event called when a reaction is added to a message."""
    try:
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
        logging.info('Reaction added and checklist updated')
    except Exception as e:
        logging.error(f"Error in on_reaction_add: {e}")

# Run the bot
try:
    bot.run(TOKEN)
except Exception as e:
    logging.error(f"Error starting the bot: {e}")
