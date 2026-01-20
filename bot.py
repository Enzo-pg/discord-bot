import discord
from discord.ext import commands, tasks
import random
import requests
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import asyncio
from discord import FFmpegPCMAudio
import yt_dlp
from ytmusicapi import YTMusic
import asyncio

# ----------------- CONFIGURAÇÕES -----------------
ytmusic = YTMusic()
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.members = True  # necessário para pegar informações do membro

bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

SEU_CANAL_ID = 1462983722222489704
SEU_SERVIDOR_ID = 1462965824410353828
SEU_USUARIO_ID = 1205980632434348093

# ----------------- BOT ONLINE -----------------
@bot.event
async def on_ready():
    print(f"{bot.user.name} está online! 🛡️")
    await bot.change_presence(activity=discord.Game(name="RPG e jogos grátis/desconto | !ajuda"))
    
    if not enviar_perfil_semanal.is_running():
        enviar_perfil_semanal.start()

# ----------------- AJUDA / COMANDOS -----------------
@bot.command()
async def ajuda(ctx):
    await comandos(ctx)

@bot.command(name="comandos")
async def comandos(ctx):
    embed = discord.Embed(
        title="📜 Comandos do BOT Rafa",
        description="Aqui estão todos os comandos que você pode usar:",
        color=discord.Color.blue()
    )

    embed.add_field(
        name="🗡️ RPG",
        value="`!rpg <situação> <dado> <sucesso>` → Ex: `!rpg Pular o abismo d20 12`",
        inline=False
    )
    embed.add_field(
        name="💻 Steam",
        value="`!steamgratis` → Mostra jogos grátis\n`!steamdesconto` → Mostra jogos com desconto",
        inline=False
    )
    embed.add_field(
        name="🎮 Epic Games",
        value="`!epicgratis` → Mostra jogos grátis\n`!epicdesconto` → Mostra jogos com desconto",
        inline=False
    )
    embed.add_field(
        name="👤 Perfil do Usuário",
        value="`!perfil <usuário>` → Mostra informações\n`!perfilimg <usuário>` → Gera cartão de perfil em imagem",
        inline=False
    )
    embed.add_field(
        name="🎵 Música",
        value="`!tocar <nome ou link>` → Toca música\n`!tocarplaylist <link>` → Adiciona à fila\n`!proxima` → Pula\n`!parar` → Para e limpa fila\n`!sair` → Sai do canal",
        inline=False
    )

    embed.set_footer(text="Use os comandos acima para se divertir e acompanhar promoções de jogos!")
    await ctx.send(embed=embed)

# ----------------- RPG -----------------
@bot.command()
async def rpg(ctx, *, args):
    try:
        partes = args.rsplit(' ', 2)
        situacao = partes[0]
        dado = partes[1]
        sucesso = int(partes[2])

        if not dado.lower().startswith('d'):
            await ctx.send("Formato do dado inválido! Use d6, d20...")
            return
        
        lados = int(dado[1:])
        resultado = random.randint(1, lados)

        await ctx.send(f"🗡️ **Situação:** {situacao}\n🎲 Tipo de dado: {dado}")
        texto = f"✅ Sucesso! Você rolou **{resultado}**!" if resultado >= sucesso else f"❌ Falha! Você rolou **{resultado}**!"
        await ctx.send(texto)
    except:
        await ctx.send("Erro! Use: !rpg <situação> <dado> <sucesso>")

# ----------------- STEAM / EPIC -----------------
async def enviar_jogos_steam(ctx, free=True):
    try:
        if free:
            url = "https://www.cheapshark.com/api/1.0/deals?storeID=1&upperPrice=0&sortBy=Price"
            title = "🎮 Jogos grátis na Steam"
            cor = discord.Color.green()
        else:
            url = "https://www.cheapshark.com/api/1.0/deals?storeID=1&sortBy=Discount"
            title = "🔥 Jogos em desconto na Steam"
            cor = discord.Color.red()
        dados = requests.get(url, timeout=10).json()
        embed = discord.Embed(title=title, color=cor)
        count = 0
        for jogo in dados:
            steam_app_id = jogo.get('steamAppID')
            deal_id = jogo.get('dealID')
            link = f"https://store.steampowered.com/app/{steam_app_id}" if steam_app_id else f"https://www.cheapshark.com/redirect?dealID={deal_id}"
            name = jogo.get('title')
            if name:
                if free:
                    embed.add_field(name=name, value=f"[Link]({link})", inline=False)
                else:
                    sale_price = jogo.get('salePrice')
                    discount = jogo.get('discountAmount')
                    embed.add_field(name=name, value=f"Preço: ${sale_price} (Desconto: {discount}%) → [Link]({link})", inline=False)
                count += 1
            if count >= 10: break
        await ctx.send(embed=embed if count>0 else "Nenhum jogo encontrado 😢")
    except:
        await ctx.send("Erro ao buscar jogos na Steam 😢")

@bot.command()
async def steamgratis(ctx): await enviar_jogos_steam(ctx, free=True)
@bot.command()
async def steamdesconto(ctx): await enviar_jogos_steam(ctx, free=False)

async def enviar_jogos_epic(ctx, free=True):
    try:
        url = "https://store-site-backend-static-ipv4.ak.epicgames.com/freeGamesPromotions?locale=pt-BR&country=BR&allowCountries=BR"
        dados = requests.get(url, timeout=10).json()['data']['Catalog']['searchStore']['elements']
        embed = discord.Embed(title=("🎮 Jogos grátis na Epic" if free else "🔥 Jogos com desconto na Epic"), color=(discord.Color.green() if free else discord.Color.red()))
        count = 0
        for jogo in dados:
            promos = jogo.get('promotions')
            if free and promos and promos.get('promotionalOffers'):
                embed.add_field(name=jogo['title'], value=f"[Link](https://www.epicgames.com/store/pt-BR/p/{jogo['productSlug']})", inline=False)
                count += 1
            elif not free and promos and promos.get('upcomingPromotionalOffers'):
                embed.add_field(name=jogo['title'], value=f"[Link](https://www.epicgames.com/store/pt-BR/p/{jogo['productSlug']})", inline=False)
                count += 1
            if count >= 10: break
        await ctx.send(embed=embed if count>0 else "Nenhum jogo encontrado 😢")
    except:
        await ctx.send("Erro ao buscar jogos na Epic 😢")

@bot.command()
async def epicgratis(ctx): await enviar_jogos_epic(ctx, free=True)
@bot.command()
async def epicdesconto(ctx): await enviar_jogos_epic(ctx, free=False)

# ----------------- PERFIL -----------------
@bot.command()
async def perfil(ctx, member: discord.Member = None):
    member = member or ctx.author
    embed = discord.Embed(title=f"Perfil de {member.name}", color=discord.Color.blue())
    embed.set_thumbnail(url=member.avatar.url)
    embed.add_field(name="Nome", value=member.name, inline=True)
    embed.add_field(name="Nickname", value=member.display_name, inline=True)
    embed.add_field(name="ID", value=member.id, inline=True)
    embed.add_field(name="Status", value=str(member.status).title(), inline=True)
    embed.add_field(name="Cargo mais alto", value=member.top_role.name, inline=True)
    embed.add_field(name="Entrou no servidor", value=member.joined_at.strftime("%d/%m/%Y %H:%M"), inline=True)
    tempo = discord.utils.utcnow() - member.joined_at
    embed.add_field(name="Tempo no servidor", value=f"{tempo.days} dias", inline=True)
    await ctx.send(embed=embed)

@bot.command()
async def perfilimg(ctx, member: discord.Member = None):
    member = member or ctx.author
    response = requests.get(member.avatar.url)
    avatar = Image.open(BytesIO(response.content)).convert("RGBA").resize((128, 128))
    fundo = Image.new("RGBA", (400, 200), (30, 30, 30, 255))
    fundo.paste(avatar, (20, 36), avatar)
    draw = ImageDraw.Draw(fundo)
    font = ImageFont.truetype("arial.ttf", 20)
    draw.text((170, 40), f"{member.name}", fill=(255, 255, 255))
    draw.text((170, 80), f"Nickname: {member.display_name}", fill=(200, 200, 200))
    draw.text((170, 120), f"ID: {member.id}", fill=(200, 200, 200))
    draw.text((170, 160), f"Cargo: {member.top_role.name}", fill=(200, 200, 200))
    buffer = BytesIO()
    fundo.save(buffer, format="PNG")
    buffer.seek(0)
    await ctx.send(file=discord.File(fp=buffer, filename=f"{member.name}_perfil.png"))

# ----------------- ENVIO AUTOMÁTICO SEMANAL -----------------
@tasks.loop(seconds=604800)  # 1 semana
async def enviar_perfil_semanal():
    canal = bot.get_channel(SEU_CANAL_ID)
    guild = bot.get_guild(SEU_SERVIDOR_ID)
    membro = guild.get_member(SEU_USUARIO_ID)
    if canal and membro:
        embed = discord.Embed(title=f"Perfil semanal de {membro.name}", color=discord.Color.purple())
        embed.set_thumbnail(url=membro.avatar.url)
        embed.add_field(name="Entrou no servidor", value=membro.joined_at.strftime("%d/%m/%Y %H:%M"))
        tempo = discord.utils.utcnow() - membro.joined_at
        embed.add_field(name="Tempo no servidor", value=f"{tempo.days} dias")
        await canal.send(embed=embed)

# ----------------- MÚSICA / PLAYLIST (COM YTMUSIC) -----------------
import os

FFMPEG_PATH = r"C:\Users\phcce\Downloads\ffmpeg-2026-01-19-git-43dbc011fa-essentials_build\bin\ffmpeg.exe"
ytmusic = YTMusic()  # Apenas público

# Filas por servidor
filas = {}          # {guild_id: [ {"title":..., "path":...}, ... ]}
musica_atual = {}   # {guild_id: {"title":..., "path":...}} -> música que está tocando agora

# Função chamada quando a música termina
def after_play(error, ctx=None):
    if error:
        print(f"Erro ao tocar música: {error}")

    if ctx:
        guild_id = ctx.guild.id
        # Deleta música que acabou de tocar
        m = musica_atual.get(guild_id)
        if m and os.path.exists(m["path"]):
            try:
                os.remove(m["path"])
            except Exception as e:
                print(f"Erro ao deletar música: {e}")
        musica_atual.pop(guild_id, None)

        # Toca próxima música da fila
        coro = tocar_proxima(ctx)
        fut = asyncio.run_coroutine_threadsafe(coro, bot.loop)
        try:
            fut.result()
        except Exception as e:
            print(f"Erro no after_play: {e}")

# Toca a próxima música da fila
async def tocar_proxima(ctx):
    guild_id = ctx.guild.id
    voz = ctx.voice_client
    if not voz:
        return

    if guild_id not in filas or len(filas[guild_id]) == 0:
        await ctx.send("✅ A fila acabou!")
        return

    musica = filas[guild_id].pop(0)
    musica_atual[guild_id] = musica  # marca música atual

    voz.play(
        FFmpegPCMAudio(
            musica["path"],
            executable=FFMPEG_PATH,
            options='-vn -reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5'
        ),
        after=lambda e: after_play(e, ctx)
    )
    await ctx.send(f"🎵 Tocando: **{musica['title']}**")

# Comando para tocar música (YouTube ou YouTube Music)
@bot.command()
async def tocar(ctx, *, busca: str = None):
    if not ctx.author.voice or not ctx.author.voice.channel:
        await ctx.send("❌ Você precisa estar em um canal de voz!")
        return
    if not busca:
        await ctx.send("❌ Coloque um link ou nome de música!")
        return

    # Converte link do YouTube Music para YouTube
    if "music.youtube.com" in busca:
        try:
            resultados = ytmusic.search(busca, filter="songs")
            if not resultados:
                await ctx.send("❌ Música não encontrada no YouTube Music!")
                return
            video_id = resultados[0].get('videoId')
            if not video_id:
                await ctx.send("❌ Música inválida no YouTube Music!")
                return
            busca = f"https://www.youtube.com/watch?v={video_id}"
        except Exception as e:
            await ctx.send(f"❌ Erro ao buscar música no YouTube Music: {e}")
            return

    canal = ctx.author.voice.channel
    if ctx.voice_client:
        await ctx.voice_client.move_to(canal)
    else:
        await canal.connect()
    voz = ctx.voice_client

    ydl_opts = {
        'format': 'bestaudio/best',
        'quiet': True,
        'noplaylist': True,
        'outtmpl': 'temp.%(ext)s'
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(busca, download=True)
            filename = ydl.prepare_filename(info)

        filas.setdefault(ctx.guild.id, []).append({"title": info["title"], "path": filename})

        if not voz.is_playing():
            await tocar_proxima(ctx)

        await ctx.send(f"🎵 Música adicionada e pronta para tocar: **{info['title']}**")

    except Exception as e:
        await ctx.send(f"❌ Erro ao tocar música: {e}")

# Comando para pular música
@bot.command()
async def proxima(ctx):
    voz = ctx.voice_client
    if voz and voz.is_playing():
        voz.stop()
        await ctx.send("⏭ Música pulada!")
    else:
        await ctx.send("❌ Não estou tocando música no momento.")

# Comando para parar e limpar fila
@bot.command()
async def parar(ctx):
    voz = ctx.voice_client
    guild_id = ctx.guild.id

    # Deleta música atual
    m = musica_atual.get(guild_id)
    if m and os.path.exists(m["path"]):
        try:
            os.remove(m["path"])
        except Exception as e:
            print(f"Erro ao deletar música: {e}")
    musica_atual.pop(guild_id, None)

    # Deleta músicas da fila
    if guild_id in filas:
        for m in filas[guild_id]:
            if os.path.exists(m["path"]):
                try:
                    os.remove(m["path"])
                except Exception as e:
                    print(f"Erro ao deletar música da fila: {e}")
        filas[guild_id].clear()

    # Para o áudio
    if voz and voz.is_playing():
        voz.stop()
        await ctx.send("⏹ Música parada e fila limpa!")
    else:
        await ctx.send("❌ Não estou tocando música no momento.")

# Comando para sair do canal de voz
@bot.command()
async def sair(ctx):
    voz = ctx.voice_client
    guild_id = ctx.guild.id

    # Deleta música atual
    m = musica_atual.get(guild_id)
    if m and os.path.exists(m["path"]):
        try:
            os.remove(m["path"])
        except Exception as e:
            print(f"Erro ao deletar música: {e}")
    musica_atual.pop(guild_id, None)

    # Deleta músicas da fila
    if guild_id in filas:
        for m in filas[guild_id]:
            if os.path.exists(m["path"]):
                try:
                    os.remove(m["path"])
                except Exception as e:
                    print(f"Erro ao deletar música da fila: {e}")
        filas[guild_id].clear()

    # Sai do canal
    if voz:
        await voz.disconnect()
        await ctx.send("👋 Sai do canal de voz e fila limpa!")
    else:
        await ctx.send("❌ Não estou em nenhum canal de voz.")


# ----------------- NOVO COMANDO: tocar YTMusic -----------------
@bot.command()
async def ytm(ctx, *, busca: str = None):
    if not ctx.author.voice or not ctx.author.voice.channel:
        await ctx.send("❌ Você precisa estar em um canal de voz!")
        return
    if not busca:
        await ctx.send("❌ Coloque um link ou nome de música!")
        return

    canal = ctx.author.voice.channel
    if ctx.voice_client:
        await ctx.voice_client.move_to(canal)
    else:
        await canal.connect()
    voz = ctx.voice_client

    try:
        # Buscar música pelo nome
        resultados = ytmusic.search(busca, filter="songs")
        if not resultados:
            await ctx.send("❌ Nenhuma música encontrada no YouTube Music!")
            return
        
        # Pega a primeira música encontrada
        musica_info = resultados[0]
        titulo = musica_info["title"]
        videoId = musica_info["videoId"]
        url = f"https://www.youtube.com/watch?v={videoId}"  # ainda vamos usar yt-dlp pra pegar áudio

        # Baixa/pega o áudio usando yt-dlp como antes
        ydl_opts = {
            'format': 'bestaudio/best',
            'quiet': True,
            'noplaylist': True,
            'outtmpl': 'temp.%(ext)s'
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

        filas.setdefault(ctx.guild.id, []).append({"title": titulo, "path": filename})

        if not voz.is_playing():
            await tocar_proxima(ctx)

        await ctx.send(f"🎵 Música adicionada da **YT Music** e pronta para tocar: **{titulo}**")

    except Exception as e:
        await ctx.send(f"❌ Erro ao tocar música do YouTube Music: {e}")

# ----------------- RODAR BOT -----------------
TOKEN = "discord_token"
bot.run(TOKEN)
