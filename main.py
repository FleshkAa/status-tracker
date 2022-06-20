"""
█▀▀ █   █▀▀ █▀▀ █  █ █ █ █▀▀█ 
█▀▀ █   █▀▀ ▀▀█ █▀▀█ █▀▄ █▄▄█ 
▀   ▀▀▀ ▀▀▀ ▀▀▀ ▀  ▀ ▀ ▀ ▀  ▀
    © Copyright 2022

https://discord.com/users/906838008261664790
https://github.com/fleshkaa/
Licensed under the GNU GPLv3
"""

import disnake as discord
from disnake.ext import commands
import sqlite3
import os
import math

#variables
intents=discord.Intents().default()
intents.members=True
intents.presences=True
client=commands.InteractionBot(intents=intents)

token=open('token').read()

db=sqlite3.connect('data.db',timeout=1)
sql=db.cursor()

emb_color=discord.Colour.from_rgb(0, 162, 255)

#bot code
class UsersResetButtons(discord.ui.View):
    def init(self):
        super().init()
        self.value = None

    @discord.ui.button(label="Yes", style=discord.ButtonStyle.green)
    async def yes(self, button: discord.ui.Button,inter: discord.MessageInteraction):
        sql.execute("UPDATE guilds SET statusu=? WHERE guildid = ?",['',inter.guild.id])
        db.commit()
     
        await inter.send(embed=discord.Embed(description='**Successfully cleared the list of tracked users**',colour=emb_color))
        self.value = True
        self.stop()

    @discord.ui.button(label="No", style=discord.ButtonStyle.red)
    async def no(self, button: discord.ui.Button,inter: discord.MessageInteraction):
        await inter.response.send_message(embed=discord.Embed(description='**Canceled**',colour=emb_color),ephemeral=True)
        self.value = False
        self.stop()

class TextResetButtons(discord.ui.View):
    def init(self):
        super().init()
        self.value = None

    @discord.ui.button(label="Yes", style=discord.ButtonStyle.green)
    async def yes(self, button: discord.ui.Button,inter: discord.MessageInteraction):
    	await inter.send(embed=discord.Embed(description=f'**Successfully reset the text**',colour=emb_color))
    	self.value = True
    	self.stop()

    @discord.ui.button(label="No", style=discord.ButtonStyle.red)
    async def no(self, button: discord.ui.Button,inter: discord.MessageInteraction):
    	await inter.response.send_message(embed=discord.Embed(description='**Canceled**',colour=emb_color),ephemeral=True)
    	self.value = False
    	self.stop()


@client.event
async def on_ready():
	sql.execute("""CREATE TABLE IF NOT EXISTS guilds (
		guildid BIGINT,
		statusc BIGINT,
		statusu TEXT,
		onlinetext TEXT,
		offlinetext TEXT
		)""")               

	for guild in client.guilds:
		if sql.execute("SELECT guildid FROM guilds WHERE guildid = ?",[guild.id]).fetchone() is None:
			sql.execute("INSERT INTO guilds VALUES (?, ?, ?, ?, ?)",[guild.id,'None','',r'**{user}** is **Online**',r'**{user}** is **Offline**'])
			db.commit()
		
	print(f'{client.user} with id {client.user.id} is started!')

	await client.change_presence(activity=discord.Game(name=f"/help | v1.1"))


@client.event
async def on_slash_command_error(inter,error):
	if isinstance(error, commands.MissingPermissions):
		await inter.response.send_message(embed=discord.Embed(description="You must have **administrator** permission to use this command",colour=emb_color),ephemeral=True)

	if isinstance(error, commands.CommandOnCooldown):
		await inter.response.send_message(embed=discord.Embed(description="You have to wait **{}s** to use this command again".format(math.ceil(error.retry_after)),colour=emb_color),ephemeral=True)



@client.event
async def on_guild_join(guild):
	if sql.execute("SELECT guildid FROM guilds WHERE guildid = ?",[guild.id]).fetchone() is None:
		sql.execute("INSERT INTO guilds VALUES (?, ?, ?, ?, ?)",[guild.id,'None','',r'**{user}** is **Online**',r'**{user}** is **Offline**'])
		db.commit()

@client.event
async def on_presence_update(before, after):
	if before.status != discord.Status.offline and after.status != discord.Status.offline: return
	if str(after.id) not in sql.execute("SELECT statusu FROM guilds WHERE guildid=?",[after.guild.id]).fetchone()[0]: return 
	if sql.execute("SELECT statusc FROM guilds WHERE guildid=?",[after.guild.id]).fetchone()[0] == 'None': return

	usr=after.name + '#' + after.discriminator
	channel=client.get_channel(sql.execute("SELECT statusc FROM guilds WHERE guildid=?",[after.guild.id]).fetchone()[0])

	offtext=sql.execute("SELECT offlinetext FROM guilds WHERE guildid = ?",[after.guild.id]).fetchone()[0].replace('{user}',usr) if "{user}" in sql.execute("SELECT offlinetext FROM guilds WHERE guildid = ?",[after.guild.id]).fetchone()[0] else sql.execute("SELECT offlinetext FROM guilds WHERE guildid = ?",[after.guild.id]).fetchone()[0]
	onltext=sql.execute("SELECT onlinetext FROM guilds WHERE guildid = ?",[after.guild.id]).fetchone()[0].replace('{user}',usr) if "{user}"  in sql.execute("SELECT onlinetext FROM guilds WHERE guildid = ?",[after.guild.id]).fetchone()[0] else sql.execute("SELECT onlinetext FROM guilds WHERE guildid = ?",[after.guild.id]).fetchone()[0]
	
	if after.status==discord.Status.offline: await channel.send(embed=discord.Embed(description=offtext,colour=emb_color))
	else:  await channel.send(embed=discord.Embed(description=onltext,colour=emb_color))
		
@client.event
async def on_member_remove(member):
	users=sql.execute("SELECT statusu FROM guilds WHERE guildid = ?",[member.guild.id]).fetchone()[0]
	if str(member.id) in users:
		users=users.replace(str(member.id),'')
		sql.execute("UPDATE guilds SET statusu = ? WHERE guildid = ?",[users,member.guild.id])
		db.commit()


@client.slash_command(description='All links about the bot')
@commands.cooldown(1, 5, commands.BucketType.default)
async def links(inter):
	await inter.send(embed=discord.Embed(title='Links:',description='[Invite link](https://discord.com/oauth2/authorize?client_id=970987574019620864&permissions=117760&scope=bot%20applications.commands)\n[Support server](https://discord.com/invite/VgTwMxyJSN)',colour=emb_color))

@client.slash_command(description='Set channel to posts status updates')
@commands.has_permissions(administrator=True)
@commands.cooldown(1, 5, commands.BucketType.default)
async def setchannel(inter: discord.GuildCommandInteraction,channel:discord.TextChannel=commands.Param(description='Set channel to post status updates')):
	try:
		await channel.send('Now i will post status updates here')
		sql.execute("UPDATE guilds SET statusc = ? WHERE guildid=?",[channel.id,inter.guild.id])
		db.commit()
		await inter.send(embed=discord.Embed(description=f'**Sucessfuly set posts channel to {channel.mention}**',colour=emb_color))
	except:
		await inter.response.send_message(embed=discord.Embed(title=':x: Error',description=f'Cant set posts channel to {channel.mention}',colour=emb_color),ephemeral=True)

@client.slash_command(description='Remove posts channel')
@commands.has_permissions(administrator=True)
@commands.cooldown(1, 5, commands.BucketType.default)
async def removechannel(inter: discord.GuildCommandInteraction):
	if sql.execute("SELECT statusc FROM guilds WHERE guildid=?",[inter.guild.id]).fetchone()[0] == 'None': return await inter.response.send_message(embed=discord.Embed(description='**The server has no channel to post status updates**',colour=emb_color),ephemeral=True)
	sql.execute("UPDATE guilds SET statusc = ? WHERE guildid=?",['None',inter.guild.id])
	db.commit()
	await inter.send(embed=discord.Embed(description=f'**Sucessfuly removed posts channel**',colour=emb_color))

@client.slash_command(description='Add user to list of tracked users')
@commands.has_permissions(administrator=True)
@commands.cooldown(1, 5, commands.BucketType.default)
async def adduser(inter: discord.GuildCommandInteraction,user: discord.Member = commands.Param(description='Add user to tracking')):
	if len(sql.execute("SELECT statusu FROM guilds WHERE guildid=?",[inter.guild.id]).fetchone()[0].strip().split(' ')) >= 50: return await inter.response.send_message(embed=discord.Embed(description='**Amount of tracking users cant be more than 50',color=emb_color))
	if sql.execute("SELECT statusc FROM guilds WHERE guildid=?",[inter.guild.id]).fetchone()[0] == 'None': return await inter.response.send_message(embed=discord.Embed(description="**You should specify channel to post status updates**",colour=emb_color))
	
	usrs=sql.execute("SELECT statusu FROM guilds WHERE guildid=?",[inter.guild.id]).fetchone()[0]
	if str(user.id) not in usrs.split(' '):
		usrs+=str(f" {user.id}")
		sql.execute("UPDATE guilds SET statusu = ? WHERE guildid = ?",[usrs,inter.guild.id])
		db.commit()
		await inter.send(embed=discord.Embed(description=f'**Successfully added a {user} to the list of tracked users**',colour=emb_color)) 	
	else:
		await inter.response.send_message(embed=discord.Embed(description=f'**The user is already on the list of tracked users**',colour=emb_color),ephemeral=True)

@client.slash_command(description='Remove user from list of tracked users')
@commands.has_permissions(administrator=True)
@commands.cooldown(1, 5, commands.BucketType.default)
async def removeuser(inter: discord.GuildCommandInteraction,user: discord.Member = commands.Param(description='Remove user from tracking')):
	if sql.execute("SELECT statusc FROM guilds WHERE guildid=?",[inter.guild.id]).fetchone()[0] == 'None': return await inter.send(embed=discrod.Embed(description="**You should specify channel to post status updates**",colour=emb_color))
	
	usrs=sql.execute("SELECT statusu FROM guilds WHERE guildid=?",[inter.guild.id]).fetchone()[0]
	if str(user.id) in usrs.split(' '):
		usrs=usrs.replace(str(user.id),'')
		sql.execute("UPDATE guilds SET statusu = ? WHERE guildid = ?",[usrs,inter.guild.id])
		db.commit()
		await inter.send(embed=discord.Embed(description=f'**Sucessfuly removed __{user}__ list of tracked users**',colour=emb_color)) 	
	else:
		await inter.response.send_message(embed=discord.Embed(description=f'**The user is not on the list of tracked users**',colour=emb_color),ephemeral=True)


@client.slash_command(description='Clear list of tracked users')
@commands.has_permissions(administrator=True)
@commands.cooldown(1, 5, commands.BucketType.default)
async def resetusers(inter: discord.GuildCommandInteraction):
	if sql.execute("SELECT statusu FROM guilds WHERE guildid=?",[inter.guild.id]).fetchone()[0] in ['',' ']: return await inter.response.send_message(embed=discord.Embed(description='**The list is empty**',color=emb_color),ephemeral=True)	
	view=UsersResetButtons()
	msg=await inter.send(embed=discord.Embed(description='**Are you sure you want to clear the list of tracked users?**',colour=emb_color),view=view)
	await view.wait()
	if view.value is None:
		try: await msg.edit(embed=discord.Embed(description='**Timed out**',colour=emb_color))
		except: pass


@client.slash_command(description='Show list of tracked users')
@commands.has_permissions(administrator=True)
@commands.cooldown(1, 5, commands.BucketType.default)
async def users(inter: discord.GuildCommandInteraction):
	usrs=sql.execute("SELECT statusu FROM guilds WHERE guildid=?",[inter.guild.id]).fetchone()[0].strip()
	usrs=usrs.split(' ')
	final=[]
	for usr in usrs:
		try:
			usr=inter.guild.get_member(int(usr))
			status='Offline' if usr.status == discord.Status.offline else 'Online'
			usr=f"**{usr.name}#{usr.discriminator}**"
			final.append(str(usr) + ' - ' + status)
		except:
			final.append("The list is empty")
			break
	await inter.send(embed=discord.Embed(title='List of tracked users in this server:',description="{}".format('\n'.join(final)),colour=emb_color))


@client.slash_command(description='Set posts text. Use "{user}" to specify user')
@commands.has_permissions(administrator=True)
@commands.cooldown(1, 5, commands.BucketType.default)
async def settext(inter: discord.GuildCommandInteraction,status:str=commands.Param(description='Specify: this is text for online or offline status?',choices=['online','offline']), text: str=commands.Param(description='Set text to post')):
	if status=='online': rawstatus='onlinetext'
	elif status=='offline': rawstatus='offlinetext'
	else: return await inter.response.send_message(embed=discord.Embed(description='**Status can be only online or offline**',colour=emb_color),ephemeral=True)

	sql.execute(f"UPDATE guilds SET {rawstatus} = ? WHERE guildid = ?",[text,inter.guild.id])
	db.commit()
	await inter.send(embed=discord.Embed(description=f'**Sucessfuly set {status} status text to **`{text}`',colour=emb_color))


@client.slash_command(description='Reset posts text')
@commands.has_permissions(administrator=True)
@commands.cooldown(1, 5, commands.BucketType.default)
async def resettext(inter: discord.GuildCommandInteraction, status:str=commands.Param(description='Specify: this is text for online or offline status?',choices=['online','offline'])):
	if status=='online': rawstatus='onlinetext'
	elif status=='offline': rawstatus='offlinetext'
	else: return await inter.response.send_message(embed=discord.Embed(description='**Status can be only online or offline**',colour=emb_color))
	if sql.execute(f"SELECT {rawstatus} FROM guilds WHERE guildid = ?",[inter.guild.id]) == "**{user}** is **" + status.replace("o","O") + '**': return await inter.response.send_message(embed=discord.Embed(description='**Status text is already default**',colour=emb_color),ephemeral=True)

	view=TextResetButtons()
	msg=await inter.send(embed=discord.Embed(description=F'**Are you sure you want to reset {status} text?**',colour=emb_color),view=view)
	await view.wait()

	if view.value is None:
		try: await msg.edit(embed=discord.Embed(description='**Timed out**',colour=emb_color))
		except: pass
	elif view.value:
		sql.execute(f"UPDATE guilds SET {rawstatus} = ? WHERE guildid = ?",["**{user}** is **" + status.replace("o","O") + '**' ,inter.guild.id])
		db.commit()

@client.slash_command(description='Show all commands')
@commands.cooldown(1, 5, commands.BucketType.default)
async def help(inter: discord.GuildCommandInteraction):
	text='''
	**__Info commands__:**

	**/links** - Get all links that are related to the bot
	**/help** - Show this message

	**__Config commands__:**
	(Required permission: **Administrator**)

	**/setchannel** - Set channel to post status updates
	**/removechannel** - Remove channel to post status updates
	**/adduser** - Add user to list of tracked users
	**/removeuser** - Remove user from list of tracked users
	**/resetusers** - Reset the list of tracked users
	**/users** - Show list of tracked users
	**/settext** - Set status updates text (use "{user}" to specify user)
	**/resettext** - Reset the text

	**__This bot use slash commands!__**
	'''.strip()

	embed=discord.Embed(description=text,colour=emb_color)
	embed.set_footer(text='FleshkA © 2022. All rights are reserved')

	await inter.send(embed=embed)


client.run(token,reconnect=True)
