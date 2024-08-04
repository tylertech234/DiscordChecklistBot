import pytest

def test_example():
    assert True

def test_create_checklist(bot, ctx):
    ctx.invoke(bot.get_command('create_checklist'), title="Test Checklist")
    assert ctx.channel.id in checklists
    assert checklists[ctx.channel.id]['title'] == "Test Checklist"

def test_add_item(bot, ctx):
    ctx.invoke(bot.get_command('create_checklist'), title="Test Checklist")
    ctx.invoke(bot.get_command('add_item'), item="Test Item")
    assert checklists[ctx.channel.id]['items'][0]['item'] == "Test Item"

def test_show_checklist(bot, ctx):
    ctx.invoke(bot.get_command('create_checklist'), title="Test Checklist")
    ctx.invoke(bot.get_command('add_item'), item="Test Item")
    result = ctx.invoke(bot.get_command('show_checklist'))
    assert "Test Checklist" in result.content
    assert "Test Item" in result.content
