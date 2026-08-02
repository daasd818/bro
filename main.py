import discord
from discord.ext import commands
from discord.ui import Button, View
import random

# --------------------------------------------
# ТОКЕН
# --------------------------------------------
TOKEN = ''  # Токен будет в .env
PREFIX = '!'

# ===== НАСТРОЙКИ (МЕНЯЙ ТУТ!) =====
ID_КАНАЛА = 1533052413248802816  # ID канала для заявок

# РОЛЬ, КОТОРАЯ ПРИНИМАЕТ РЕШЕНИЕ (НАЖИМАЕТ КНОПКИ)
ID_РОЛИ_АДМИНА = 1531926196281933844

# РОЛЬ, КОТОРАЯ МОЖЕТ ПИСАТЬ КОМАНДУ
ID_РОЛИ_ДЛЯ_КОМАНДЫ = 1531927352957993000

# ===== СПИСОК ID РОЛЕЙ ДЛЯ ВЫДАЧИ =====
СПИСОК_РОЛЕЙ_ДЛЯ_ВЫДАЧИ = [
    1531915879049203813,  # ID роли
    1531928160864567376,  # ID роли
    # ДОБАВЛЯЙ СКОЛЬКО УГОДНО
]

intents = discord.Intents.all()
bot = commands.Bot(command_prefix=PREFIX, intents=intents, help_command=None)

# --------------------------------------------
# БОТ ЗАПУСТИЛСЯ
# --------------------------------------------
@bot.event
async def on_ready():
    print(f'✅ Бот {bot.user} запущен!')
    print(f'➡️  Зашёл на {len(bot.guilds)} серверов')
    await bot.change_presence(activity=discord.Game(name=f"{PREFIX}help | v1.0"))

# --------------------------------------------
# ФУНКЦИЯ ДЛЯ ПОЛУЧЕНИЯ РОЛЕЙ ПО ID
# --------------------------------------------
def получить_роли(guild):
    роли = []
    for id_роли in СПИСОК_РОЛЕЙ_ДЛЯ_ВЫДАЧИ:
        роль = guild.get_role(id_роли)
        if роль:
            роли.append(роль)
        else:
            print(f"⚠️ Роль с ID {id_роли} не найдена!")
    return роли

# --------------------------------------------
# КОМАНДА ПРИНЯТЬ_ПИЛОТ
# --------------------------------------------
@bot.command()
async def принять_пилот(ctx, принимающий: discord.Member, принявший: discord.Member):
    """
    !принять_пилот @пользователь1 @пользователь2
    """
    
    # Проверка: есть ли роль для использования команды
    if ID_РОЛИ_ДЛЯ_КОМАНДЫ not in [роль.id for роль in ctx.author.roles]:
        await ctx.send("❌ У тебя нет прав использовать эту команду!")
        return
    
    # Проверки
    if принимающий == принявший:
        await ctx.send("❌ Нельзя принять самого себя!")
        return
    
    if принявший not in ctx.guild.members:
        await ctx.send("❌ Пользователь не найден на сервере!")
        return
    
    # Ищем канал
    канал = bot.get_channel(ID_КАНАЛА)
    if not канал:
        await ctx.send("❌ Канал не найден! Проверь ID_КАНАЛА")
        return
    
    # Ищем роль админа
    роль_админа = ctx.guild.get_role(ID_РОЛИ_АДМИНА)
    if not роль_админа:
        await ctx.send("❌ Роль админа не найдена! Проверь ID_РОЛИ_АДМИНА")
        return
    
    # Получаем роли для выдачи
    роли_для_выдачи = получить_роли(ctx.guild)
    
    if not роли_для_выдачи:
        await ctx.send("❌ Ни одна роль из списка не найдена! Проверь СПИСОК_РОЛЕЙ_ДЛЯ_ВЫДАЧИ")
        return
    
    # Создаём кнопки
    class ЗаявкаView(View):
        def __init__(self):
            super().__init__(timeout=300)
            
        @discord.ui.button(label="✅ Разрешить", style=discord.ButtonStyle.green)
        async def разрешить(self, interaction: discord.Interaction, button: Button):
            if роль_админа not in interaction.user.roles:
                await interaction.response.send_message("❌ У тебя нет прав!", ephemeral=True)
                return
            
            # Убираем все роли
            await принявший.edit(roles=[])
            
            # Выдаем роли
            выдано = []
            for роль in роли_для_выдачи:
                try:
                    await принявший.add_roles(роль)
                    выдано.append(роль.name)
                except Exception as e:
                    print(f"Ошибка при выдаче {роль.name}: {e}")
            
            # Формируем список ролей
            список_ролей = "\n- «" + "»\n- «".join(выдано) + "»" if выдано else "роли не выданы"
            
            # Зеленый эмбед
            embed = discord.Embed(
                title="✅ ЗАЯВКА ОДОБРЕНА",
                description=f"**{принимающий.mention}** ПРИНЯЛ **{принявший.mention}**",
                color=discord.Color.green()
            )
            embed.add_field(name="Статус", value="☑ Разрешено", inline=False)
            embed.add_field(name="Выданные роли", value=список_ролей, inline=False)
            embed.add_field(name="Кто принял", value=interaction.user.mention, inline=True)
            embed.add_field(name="Время", value=discord.utils.utcnow().strftime("%H:%M:%S"), inline=True)
            
            # Редактируем эмбед
            await interaction.response.edit_message(embed=embed, view=None)
            
            # ОТДЕЛЬНОЕ СООБЩЕНИЕ С РЕЗУЛЬТАТОМ (без пинга роли)
            await interaction.followup.send(f"✅ {принявший.mention} получил роли:\n{список_ролей}", ephemeral=False)
        
        @discord.ui.button(label="❌ Отказать", style=discord.ButtonStyle.red)
        async def отказать(self, interaction: discord.Interaction, button: Button):
            if роль_админа not in interaction.user.roles:
                await interaction.response.send_message("❌ У тебя нет прав!", ephemeral=True)
                return
            
            # Красный эмбед
            embed = discord.Embed(
                title="❌ ЗАЯВКА ОТКЛОНЕНА",
                description=f"**{принимающий.mention}** ХОТЕЛ ПРИНЯТЬ **{принявший.mention}**",
                color=discord.Color.red()
            )
            embed.add_field(name="Статус", value="☑ Отказано", inline=False)
            embed.add_field(name="Кто отказал", value=interaction.user.mention, inline=True)
            embed.add_field(name="Время", value=discord.utils.utcnow().strftime("%H:%M:%S"), inline=True)
            
            await interaction.response.edit_message(embed=embed, view=None)
            
            # ОТДЕЛЬНОЕ СООБЩЕНИЕ ОБ ОТКАЗЕ (без пинга)
            await interaction.followup.send(f"❌ Заявка отклонена!", ephemeral=False)
    
    # Получаем список ролей для эмбеда
    список_ролей = "\n- «" + "»\n- «".join([роль.name for роль in роли_для_выдачи]) + "»"
    
    # Создаем эмбед (без пинга роли внутри!)
    embed = discord.Embed(
        title="📋 НОВАЯ ЗАЯВКА",
        description=f"**{принимающий.mention}** ХОЧЕТ ПРИНЯТЬ **{принявший.mention}**",
        color=discord.Color.dark_grey()
    )
    embed.add_field(name="Кто принимает", value=принимающий.mention, inline=True)
    embed.add_field(name="Кого принимают", value=принявший.mention, inline=True)
    embed.add_field(name="Роли для выдачи", value=список_ролей, inline=False)
    embed.add_field(name="Статус", value="⏳ Ожидание решения...", inline=False)
    embed.set_footer(text=f"Заявка от {ctx.author.name} | {discord.utils.utcnow().strftime('%d.%m.%Y %H:%M')}")
    
    # ОТДЕЛЬНЫЙ ПИНГ РОЛИ (перед эмбедом)
    await канал.send(f"**ВНИМАНИЕ {роль_админа.mention}**")
    
    # Отправляем эмбед с кнопками
    view = ЗаявкаView()
    await канал.send(embed=embed, view=view)
    
    # Удаляем команду
    try:
        await ctx.message.delete()
    except:
        pass
    
    # Отправляем подтверждение автору (удалится через 5 сек)
    msg = await ctx.send(f"✅ Заявка отправлена в {канал.mention}!")
    await msg.delete(delay=5)

# --------------------------------------------
# ОСТАЛЬНЫЕ КОМАНДЫ
# --------------------------------------------
@bot.command()
async def help(ctx):
    embed = discord.Embed(
        title="📖 Список команд",
        description=f"Используй префикс `{PREFIX}` перед командой",
        color=discord.Color.green()
    )
    
    команды = [
        ("принять_пилот @пользователь1 @пользователь2", "Создать заявку на принятие"),
        ("привет", "Поздороваться с ботом"),
        ("рандом 1 10", "Случайное число"),
        ("инфо", "Информация о сервере"),
        ("кик @User", "Кикнуть пользователя"),
        ("очистка 10", "Удалить сообщения"),
        ("help", "Показать эту справку")
    ]
    
    for комманда, описание in команды:
        embed.add_field(
            name=f"{PREFIX}{комманда}",
            value=описание,
            inline=False
        )
    
    await ctx.send(embed=embed)

@bot.command()
async def привет(ctx):
    await ctx.send(f'Привет, {ctx.author.mention}! 👋')

@bot.command()
async def рандом(ctx, min_num: int = 1, max_num: int = 100):
    result = random.randint(min_num, max_num)
    await ctx.send(f'🎲 Твоё число: {result}')

@bot.command()
async def инфо(ctx):
    embed = discord.Embed(
        title=f"📊 Информация о сервере {ctx.guild.name}",
        color=discord.Color.blue()
    )
    embed.add_field(name="👑 Владелец", value=ctx.guild.owner.mention, inline=True)
    embed.add_field(name="👥 Участников", value=ctx.guild.member_count, inline=True)
    embed.add_field(name="📅 Создан", value=ctx.guild.created_at.strftime("%d.%m.%Y"), inline=True)
    embed.set_thumbnail(url=ctx.guild.icon.url if ctx.guild.icon else None)
    await ctx.send(embed=embed)

@bot.command()
@commands.has_permissions(kick_members=True)
async def кик(ctx, member: discord.Member, *, reason="Не указана"):
    await member.kick(reason=reason)
    await ctx.send(f'🚪 {member.mention} был кикнут. Причина: {reason}')

@bot.command()
@commands.has_permissions(manage_messages=True)
async def очистка(ctx, amount: int):
    if amount < 1:
        await ctx.send("❌ Число должно быть больше 0")
        return
    deleted = await ctx.channel.purge(limit=amount + 1)
    msg = await ctx.send(f"🗑 Удалено {len(deleted)-1} сообщений")
    await msg.delete(delay=3)

# --------------------------------------------
# ОШИБКИ
# --------------------------------------------
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ У тебя нет прав для этой команды!")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"❌ Не хватает аргументов. Напиши `{PREFIX}help`")
    elif isinstance(error, commands.BadArgument):
        await ctx.send("❌ Неверный формат аргумента (нужно пинговать пользователей)")
    else:
        await ctx.send(f"⚠️ Ошибка: {error}")

# --------------------------------------------
# ЗАПУСК
# --------------------------------------------
if __name__ == "__main__":
    bot.run(TOKEN)