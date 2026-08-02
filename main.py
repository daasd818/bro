import discord
from discord.ext import commands
from discord.ui import Button, View
import random
import asyncio
from datetime import datetime
import os

# --------------------------------------------
# ТОКЕН (БЕРЁТСЯ ИЗ ПЕРЕМЕННЫХ RAILWAY)
# --------------------------------------------
TOKEN = os.getenv('TOKEN')
PREFIX = '!'

# ===== НАСТРОЙКИ (МЕНЯЙ ТУТ!) =====
# Канал для заявок !принять_пилот
ID_КАНАЛА = 1533052413248802816

# Роль, которая принимает решение (нажимает кнопки)
ID_РОЛИ_АДМИНА = 1531926196281933844

# Роль, которая может писать !принять_пилот
ID_РОЛИ_ДЛЯ_КОМАНДЫ = 1531927352957993080

# Список ролей, которые выдаются при принятии
СПИСОК_РОЛЕЙ_ДЛЯ_ВЫДАЧИ = [
    1531915879049203813,
    1531928160864567376,
]

# ===== НАСТРОЙКИ ДЛЯ !отпуск_пилот =====
# Роли, которые могут давать отпуск (ID)
ID_РОЛЕЙ_ДЛЯ_ОТПУСКА = [
    1531927352957993080,  # та же, что и для команды
    1531926196281933844,  # админ
]

# Роль, которая выдаётся во время отпуска
ID_РОЛЬ_ОТПУСКА = 1531928033462587402

# Канал, куда летят логи по отпускам
ID_КАНАЛА_ЛОГОВ_ОТПУСКА = 1533401160013316166

# --------------------------------------------
# ИНИЦИАЛИЗАЦИЯ БОТА
# --------------------------------------------
intents = discord.Intents.all()
bot = commands.Bot(command_prefix=PREFIX, intents=intents, help_command=None)


# --------------------------------------------
# СОБЫТИЕ: БОТ ЗАПУСТИЛСЯ
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
# КОМАНДА: !принять_пилот
# --------------------------------------------
@bot.command()
async def принять_пилот(ctx, принимающий: discord.Member, принявший: discord.Member):
    """
    !принять_пилот @пользователь1 @пользователь2
    """
    if ID_РОЛИ_ДЛЯ_КОМАНДЫ not in [роль.id for роль in ctx.author.roles]:
        await ctx.send("❌ У тебя нет прав использовать эту команду!")
        return

    if принимающий == принявший:
        await ctx.send("❌ Нельзя принять самого себя!")
        return

    if принявший not in ctx.guild.members:
        await ctx.send("❌ Пользователь не найден на сервере!")
        return

    канал = bot.get_channel(ID_КАНАЛА)
    if not канал:
        await ctx.send("❌ Канал не найден! Проверь ID_КАНАЛА")
        return

    роль_админа = ctx.guild.get_role(ID_РОЛИ_АДМИНА)
    if not роль_админа:
        await ctx.send("❌ Роль админа не найдена! Проверь ID_РОЛИ_АДМИНА")
        return

    роли_для_выдачи = получить_роли(ctx.guild)
    if not роли_для_выдачи:
        await ctx.send("❌ Ни одна роль из списка не найдена!")
        return

    class ЗаявкаView(View):
        def __init__(self):
            super().__init__(timeout=300)

        @discord.ui.button(label="✅ Разрешить", style=discord.ButtonStyle.green)
        async def разрешить(self, interaction: discord.Interaction, button: Button):
            if роль_админа not in interaction.user.roles:
                await interaction.response.send_message("❌ У тебя нет прав!", ephemeral=True)
                return

            await принявший.edit(roles=[])
            выдано = []
            for роль in роли_для_выдачи:
                try:
                    await принявший.add_roles(роль)
                    выдано.append(роль.name)
                except Exception as e:
                    print(f"Ошибка при выдаче {роль.name}: {e}")

            список_ролей = "\n- «" + "»\n- «".join(выдано) + "»" if выдано else "роли не выданы"

            embed = discord.Embed(
                title="✅ ЗАЯВКА ОДОБРЕНА",
                description=f"{принимающий.name} ПРИНЯЛ {принявший.name}",
                color=discord.Color.green()
            )
            embed.add_field(name="Статус", value="☑ Разрешено", inline=False)
            embed.add_field(name="Выданные роли", value=список_ролей, inline=False)
            embed.add_field(name="Кто принял", value=interaction.user.name, inline=True)
            embed.add_field(name="Время", value=discord.utils.utcnow().strftime("%H:%M:%S"), inline=True)

            await interaction.response.edit_message(embed=embed, view=None)
            await interaction.followup.send(f"✅ {принявший.mention} получил роли:\n{список_ролей}", ephemeral=False)

        @discord.ui.button(label="❌ Отказать", style=discord.ButtonStyle.red)
        async def отказать(self, interaction: discord.Interaction, button: Button):
            if роль_админа not in interaction.user.roles:
                await interaction.response.send_message("❌ У тебя нет прав!", ephemeral=True)
                return

            embed = discord.Embed(
                title="❌ ЗАЯВКА ОТКЛОНЕНА",
                description=f"{принимающий.name} ХОТЕЛ ПРИНЯТЬ {принявший.name}",
                color=discord.Color.red()
            )
            embed.add_field(name="Статус", value="☑ Отказано", inline=False)
            embed.add_field(name="Кто отказал", value=interaction.user.name, inline=True)
            embed.add_field(name="Время", value=discord.utils.utcnow().strftime("%H:%M:%S"), inline=True)

            await interaction.response.edit_message(embed=embed, view=None)
            await interaction.followup.send(f"❌ Заявка отклонена!", ephemeral=False)

    список_ролей = "\n- «" + "»\n- «".join([роль.name for роль in роли_для_выдачи]) + "»"

    embed = discord.Embed(
        title="📋 НОВАЯ ЗАЯВКА",
        description=f"{принимающий.name} ХОЧЕТ ПРИНЯТЬ {принявший.name}",
        color=discord.Color.dark_grey()
    )
    embed.add_field(name="Кто принимает", value=принимающий.name, inline=True)
    embed.add_field(name="Кого принимают", value=принявший.name, inline=True)
    embed.add_field(name="Роли для выдачи", value=список_ролей, inline=False)
    embed.add_field(name="Статус", value="⏳ Ожидание решения...", inline=False)
    embed.set_footer(text=f"Заявка от {ctx.author.name} | {discord.utils.utcnow().strftime('%d.%m.%Y %H:%M')}")

    # ПИНГ РОЛИ ОТДЕЛЬНО (ПЕРЕД ЭМБЕДОМ)
    await канал.send(f"**ВНИМАНИЕ {роль_админа.mention}**")
    view = ЗаявкаView()
    await канал.send(embed=embed, view=view)

    try:
        await ctx.message.delete()
    except:
        pass

    msg = await ctx.send(f"✅ Заявка отправлена в {канал.mention}!")
    await msg.delete(delay=5)


# --------------------------------------------
# ФУНКЦИЯ ДЛЯ ПАРСИНГА ВРЕМЕНИ (!отпуск_пилот)
# --------------------------------------------
def convert_time(время: str) -> int:
    """Конвертирует строку типа '1с', '5мин', '2ч', '1д' в секунды"""
    время = время.lower().strip()

    if время.endswith('с') or время.endswith('сек'):
        return int(время.replace('сек', '').replace('с', ''))
    elif время.endswith('мин'):
        return int(время[:-3]) * 60
    elif время.endswith('ч'):
        return int(время[:-1]) * 3600
    elif время.endswith('д'):
        return int(время[:-1]) * 86400
    else:
        raise ValueError("Неверный формат времени")


# --------------------------------------------
# КОМАНДА: !отпуск_пилот
# --------------------------------------------
@bot.command()
async def отпуск_пилот(ctx, member: discord.Member, время: str):
    """
    !отпуск_пилот @пользователь 1д
    Доступно только ролям из списка ID_РОЛЕЙ_ДЛЯ_ОТПУСКА
    """
    # Проверка прав
    has_permission = False
    for роль in ctx.author.roles:
        if роль.id in ID_РОЛЕЙ_ДЛЯ_ОТПУСКА:
            has_permission = True
            break

    if not has_permission:
        await ctx.send("❌ У тебя нет прав использовать эту команду!")
        return

    # Проверка времени
    try:
        seconds = convert_time(время)
    except ValueError:
        await ctx.send("❌ Неверный формат времени! Примеры: `1с`, `5мин`, `2ч`, `1д`")
        return

    if member not in ctx.guild.members:
        await ctx.send("❌ Пользователь не найден на сервере!")
        return

    роль_отпуска = ctx.guild.get_role(ID_РОЛЬ_ОТПУСКА)
    if not роль_отпуска:
        await ctx.send("❌ Роль отпуска не найдена! Проверь ID_РОЛЬ_ОТПУСКА")
        return

    # Сохраняем старые роли
    старые_роли = [role for role in member.roles if role.name != "@everyone"]
    имена_старых_ролей = [role.name for role in старые_роли]

    # Меняем роли
    try:
        await member.edit(roles=[])
        await member.add_roles(роль_отпуска)
    except Exception as e:
        await ctx.send(f"❌ Ошибка при выдаче ролей: {e}")
        return

    # Лог в канал
    канал_логов = bot.get_channel(ID_КАНАЛА_ЛОГОВ_ОТПУСКА)
    if канал_логов:
        embed = discord.Embed(
            title="📋 ОТПУСК",
            description=f"Сотрудник {ctx.author.name} выдал отпуск {member.name}",
            color=discord.Color.light_grey()
        )
        embed.add_field(name="⏰ Время", value=время, inline=True)
        embed.add_field(name="📌 Снятые роли", value=", ".join(имена_старых_ролей) if имена_старых_ролей else "Нет", inline=False)
        embed.add_field(name="📌 Выданные роли", value=роль_отпуска.name, inline=False)
        embed.set_footer(text=f"ID: {member.id} | {datetime.now().strftime('%d.%m.%Y %H:%M')}")
        await канал_логов.send(embed=embed)

    await ctx.send(f"✅ {member.mention} получил роль отпуска на **{время}**!")

    # Функция возврата ролей
    async def вернуть_роли():
        await asyncio.sleep(seconds)

        try:
            await member.remove_roles(роль_отпуска)
            for role in старые_роли:
                try:
                    await member.add_roles(role)
                except:
                    pass

            if канал_логов:
                embed = discord.Embed(
                    title="📋 ОТПУСК ЗАКОНЧЕН",
                    description=f"Отпуск {member.name} был закончен",
                    color=discord.Color.light_grey()
                )
                embed.add_field(name="📌 Возвращены роли", value=", ".join(имена_старых_ролей) if имена_старых_ролей else "Нет", inline=False)
                embed.set_footer(text=f"Время: {datetime.now().strftime('%d.%m.%Y %H:%M')}")
                await канал_логов.send(embed=embed)

            try:
                await ctx.send(f"✅ Отпуск {member.mention} закончен! Роли возвращены.")
            except:
                pass
        except Exception as e:
            print(f"Ошибка при возврате ролей для {member.name}: {e}")

    asyncio.create_task(вернуть_роли())


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
        ("отпуск_пилот @пользователь 1д", "Выдать роль отпуска на время"),
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
# ОБРАБОТЧИК ОШИБОК
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
