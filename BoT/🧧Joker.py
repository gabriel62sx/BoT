import discord
from discord.ext import commands, tasks
from discord import app_commands
import os
import json
from dotenv import load_dotenv
import asyncio
from datetime import datetime, timedelta
import typing
import random
# Imports para manipulação de imagem
from PIL import Image, ImageDraw, ImageFont, ImageOps
from io import BytesIO
import io
import requests
import re
import qrcode
import aiohttp
import sys
# Força o terminal do Windows a aceitar emojis nos prints (evita UnicodeEncodeError)
if sys.stdout and sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# IA Removida

# Carregar variáveis de ambiente
load_dotenv()

# Configurações do bot
intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.guilds = True
print(f'🔧 Intents configurados: Members={intents.members}, Content={intents.message_content}')

bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)

# --- Restrição Global: Apenas ADM e Dono ---
@bot.check
async def global_restrict(ctx):
    """Restringe comandos de prefixo (!) para ADM e Dono, exceto específicos"""
    if ctx.guild is None: return False
    if ctx.command and ctx.command.name in ["script", "minigames", "meuvip", "minhasskins"]:
        return True
    return ctx.author.id == ctx.guild.owner_id or ctx.author.guild_permissions.administrator

@bot.tree.interaction_check
async def global_interaction_restrict(interaction: discord.Interaction):
    """Restringe comandos slash (/) para ADM e Dono, exceto específicos"""
    if interaction.guild is None: return False
    # Lista de comandos liberados para todos (ou controle interno)
    if interaction.command and interaction.command.name in ["script", "minigames", "meuvip", "minhasskins", "money", "mis", "sync"]:
        return True
    
    is_admin = interaction.user.id == interaction.guild.owner_id or interaction.user.guild_permissions.administrator
    if not is_admin:
        await interaction.response.send_message("❌ **Acesso Negado:** Apenas Administradores e o Dono do servidor podem usar os comandos do 🧧Joker.", ephemeral=True)
    return is_admin

# IDs e configurações (serão configurados via comandos)
welcome_channel_id = None
leave_channel_id = None
booster_channel_id = None
member_role_id = None
ticket_category_loja_id = None
ticket_category_suporte_id = None
ticket_category_suporte_id = None
# Configurações de Parceria (YouTube)
# Serão carregadas do config no on_ready

# Armazenar configurações
config = {}

# --- Sistema de Pastas e Salvamento ---
# Garante que os arquivos sejam salvos na pasta correta (STAFF)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(BASE_DIR, 'bot_config.json')
VENDAS_PENDENTES_FILE = os.path.join(BASE_DIR, "vendas_pendentes.json")
USER_DATA_FILE = os.path.join(BASE_DIR, 'usuarios.json')
VIPS_FILE = os.path.join(BASE_DIR, 'vips.json')
SKINS_FILE = os.path.join(BASE_DIR, 'skins.json')
CLANS_FILE = os.path.join(BASE_DIR, 'clans.json')

# Preços Automáticos (Lookup)
TABELA_PRECOS = {
    "vip bronze": 10.00,
    "vip prata": 20.00,
    "vip ouro": 30.00,
    "vip scripts": 50.00
}

# Cache para controle de spam/concorrência
xp_cooldowns = {}
canais_em_fechamento = set()
tickets_em_criacao = set()
canais_em_fechamento = set() # Trava de segurança para evitar duplicidade no fechamento
tickets_em_criacao = set() # NOVO: Evitar duplo clique na criação de tickets
invites_cache = {} # Cache de convites: {guild_id: {code: uses}}
canais_temporarios = set() # Guarda os IDs das salas de voz temporárias
tempo_afk = {} # Rastrear tempo AFK dos usuários em voz

# --- Sistema de IAS (Inteligência Artificial) ---
# IA Removida

async def update_invite_cache(guild):
    """Atualiza o cache de convites de um servidor"""
    if not guild.me.guild_permissions.manage_guild:
        return
    try:
        invites = await guild.invites()
        invites_cache[guild.id] = {invite.code: invite.uses for invite in invites}
    except Exception as e:
        print(f"⚠️ Erro ao atualizar cache de convites em {guild.name}: {e}")

def carregar_usuarios():
    if not os.path.exists(USER_DATA_FILE):
        return {}
    with open(USER_DATA_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except:
            return {}

def salvar_usuarios(usuarios):
    with open(USER_DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(usuarios, f, indent=4)

def carregar_vips():
    if not os.path.exists(VIPS_FILE):
        return {}
    with open(VIPS_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except:
            return {}

def salvar_vips(vips):
    with open(VIPS_FILE, "w", encoding="utf-8") as f:
        json.dump(vips, f, indent=4)

def carregar_skins():
    if not os.path.exists(SKINS_FILE):
        return {}
    with open(SKINS_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except:
            return {}

def salvar_skins(skins):
    with open(SKINS_FILE, "w", encoding="utf-8") as f:
        json.dump(skins, f, indent=4)

def carregar_clans():
    if not os.path.exists(CLANS_FILE):
        return {}
    with open(CLANS_FILE, "r", encoding="utf-8") as f:
        try: return json.load(f)
        except: return {}

def salvar_clans(clans):
    with open(CLANS_FILE, "w", encoding="utf-8") as f:
        json.dump(clans, f, indent=4)

def salvar_config(config_data):
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config_data, f, indent=4)

def normalizar_nome(texto: str) -> str:
    """Normaliza texto removendo acentos e caracteres especiais para busca"""
    if not texto: return ""
    import unicodedata
    # Normalizar para remover acentos
    texto = unicodedata.normalize('NFD', texto)
    texto = "".join([c for c in texto if not unicodedata.combining(c)])
    # Remover emojis e caracteres especiais simples, mantendo letras e números
    texto = re.sub(r'[^a-zA-Z0-9\s]', '', texto)
    return texto.lower().strip()

@tasks.loop(minutes=5)
async def check_youtube_videos():
    """Verifica automaticamente novos vídeos nos canais do YouTube dos parceiros"""
    await bot.wait_until_ready()
    global config
    
    youtube_data = config.get("partner_youtube_channels", {})
    target_channel_id = config.get("partner_forward_target_id")
    
    if not youtube_data or not target_channel_id:
        return
        
    target_channel = bot.get_channel(int(target_channel_id))
    if not target_channel:
        return

    alterado = False
    for channel_id, data in youtube_data.items():
        try:
            # RSS Feed do YouTube
            url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                # Extrair o vídeo ID do vídeo mais recente usando regex
                # O primeiro <yt:videoId> no XML costuma ser o mais recente
                video_ids = re.findall(r'<yt:videoId>(.*?)</yt:videoId>', response.text)
                
                if video_ids:
                    latest_video_id = video_ids[0]
                    last_seen_id = data.get("last_video_id")
                    
                    if latest_video_id != last_seen_id:
                        # Novo vídeo detectado!
                        video_url = f"https://www.youtube.com/watch?v={latest_video_id}"
                        
                        # Postar no estilo Loritta
                        await target_channel.send(f"Novo vídeo no canal! {video_url}")
                        
                        # Atualizar último vídeo visto
                        config["partner_youtube_channels"][channel_id]["last_video_id"] = latest_video_id
                        alterado = True
                        print(f"🎬 [YouTube] Novo vídeo detectado no canal {channel_id}: {latest_video_id}")
        except Exception as e:
            print(f"⚠️ Erro ao checar YouTube ({channel_id}): {e}")

    if alterado:
        salvar_config(config)

# --- Sistema de Integração Efipay ---
# Armazenamento de pagamentos pendentes
pagamentos_pendentes = {}  # {channel_id: {"txid": "...", "valor": 0.0, "atendente_id": "..."}}

async def obter_token_efipay():
    """Obtém token de acesso OAuth2 da API Efipay com suporte a certificado mTLS"""
    global config
    
    client_id = config.get("efipay_client_id")
    client_secret = config.get("efipay_client_secret")
    cert_path = config.get("efipay_cert_path")
    ambiente = config.get("efipay_ambiente", "homologacao")
    
    if not client_id or not client_secret:
        print("❌ Efipay: Credenciais não configuradas!")
        return None
        
    if not cert_path:
        print("❌ Efipay: Caminho do certificado não configurado!")
        return None
        
    cert_full_path = os.path.join(BASE_DIR, cert_path)
    if not os.path.exists(cert_full_path):
        print(f"❌ Efipay: Arquivo de certificado não encontrado: {cert_full_path}")
        return None

    # Validação básica: verificar se é um arquivo PEM (texto)
    try:
        with open(cert_full_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read(100)
            if "-----BEGIN" not in content:
                print(f"❌ Efipay: O arquivo `{cert_path}` NÃO parece ser um certificado PEM válido.")
                print("💡 DICA: Se você baixou um arquivo .p12, você precisa convertê-lo para .pem antes de usar.")
                return None
    except Exception as e:
        print(f"❌ Efipay: Erro ao ler o arquivo de certificado: {e}")
        return None
    
    try:
        # Endpoint de autenticação
        base_url = "https://api-pix.gerencianet.com.br" if ambiente == "producao" else "https://api-pix-h.gerencianet.com.br"
        url = f"{base_url}/oauth/token"
        
        import base64
        credentials = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
        
        headers = {
            "Authorization": f"Basic {credentials}",
            "Content-Type": "application/json"
        }
        
        payload = {"grant_type": "client_credentials"}
        
        print(f"🔄 Efipay: Tentando autenticar em {ambiente} usando {cert_path}...")
        
        # O certificado é OBRIGATÓRIO para a API PIX
        response = requests.post(url, headers=headers, json=payload, cert=cert_full_path, timeout=15)
        
        if response.status_code == 200:
            return response.json().get("access_token")
        else:
            print(f"⚠️ Erro de API Efipay ({response.status_code}): {response.text}")
            return None
    except requests.exceptions.SSLError as ssl_err:
        print(f"❌ Efipay: Erro de SSL/Certificado: {ssl_err}")
        print("💡 DICA: Verifique se o certificado PEM contém tanto a CHAVE PRIVADA quanto o CERTIFICADO.")
        return None
    except Exception as e:
        print(f"❌ Efipay: Erro de conexão: {e}")
        return None

async def criar_pagamento_efipay(valor: float, descricao: str = "Compra STAFF"):
    """Cria um pagamento PIX dinâmico via API Efipay"""
    global config
    
    ambiente = config.get("efipay_ambiente", "homologacao")
    cert_path = config.get("efipay_cert_path")
    cert_full_path = os.path.join(BASE_DIR, cert_path) if cert_path else None
    
    # Obter token de acesso
    token = await obter_token_efipay()
    if not token:
        print("❌ Efipay: Falha ao obter token de acesso!")
        return None
    
    try:
        # Endpoint de criação de cobrança
        base_url = "https://api-pix.gerencianet.com.br" if ambiente == "producao" else "https://api-pix-h.gerencianet.com.br"
        
        # Gerar txid único
        import uuid
        txid = str(uuid.uuid4()).replace("-", "")[:35]
        
        url = f"{base_url}/v2/cob/{txid}"
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        # Payload da cobrança
        payload = {
            "calendario": {
                "expiracao": 3600  # 1 hora
            },
            "valor": {
                "original": f"{valor:.2f}"
            },
            "chave": config.get("efipay_chave_pix", ""),  # Chave PIX cadastrada na Efipay
            "solicitacaoPagador": descricao
        }
        
        print(f"🔄 Efipay: Criando pagamento de R$ {valor:.2f}...")
        
        response = requests.put(url, headers=headers, json=payload, cert=cert_full_path, timeout=15)
        
        print(f"📡 Efipay Response: {response.status_code}")
        
        if response.status_code in [200, 201]:
            data = response.json()
            
            # Obter QR Code
            loc_id = data.get("loc", {}).get("id")
            if loc_id:
                qrcode_url = f"{base_url}/v2/loc/{loc_id}/qrcode"
                qrcode_response = requests.get(qrcode_url, headers=headers, cert=cert_full_path, timeout=10)
                
                if qrcode_response.status_code == 200:
                    qrcode_data = qrcode_response.json()
                    qr_code = qrcode_data.get("qrcode")
                    qr_code_base64 = qrcode_data.get("imagemQrcode")
                else:
                    qr_code = None
                    qr_code_base64 = None
            else:
                qr_code = None
                qr_code_base64 = None
            
            print(f"✅ Efipay: Pagamento criado com sucesso!")
            return {
                "qr_code": qr_code,
                "txid": data.get("txid"),
                "location": data.get("location"),
                "qr_code_base64": qr_code_base64
            }
        else:
            print(f"⚠️ Erro ao criar pagamento Efipay: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ Erro na API Efipay: {e}")
        return None

async def verificar_pagamento_efipay(txid: str):
    """Verifica o status de um pagamento na Efipay"""
    global config
    
    ambiente = config.get("efipay_ambiente", "homologacao")
    cert_path = config.get("efipay_cert_path")
    cert_full_path = os.path.join(BASE_DIR, cert_path) if cert_path else None
    
    # Obter token de acesso
    token = await obter_token_efipay()
    if not token:
        return None
    
    try:
        base_url = "https://api-pix.gerencianet.com.br" if ambiente == "producao" else "https://api-pix-h.gerencianet.com.br"
        url = f"{base_url}/v2/cob/{txid}"
        
        headers = {
            "Authorization": f"Bearer {token}"
        }
        
        response = requests.get(url, headers=headers, cert=cert_full_path, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            return data.get("status")  # "ATIVA", "CONCLUIDA", "REMOVIDA_PELO_USUARIO_RECEBEDOR", etc.
        else:
            return None
    except Exception as e:
        print(f"❌ Erro ao verificar pagamento: {e}")
        return None

@tasks.loop(seconds=30)
async def check_efipay_payments():
    """Verifica automaticamente o status dos pagamentos pendentes"""
    await bot.wait_until_ready()
    global pagamentos_pendentes, config
    
    if not config.get("efipay_enabled", False):
        return
    
    canais_pagos = []
    
    for channel_id, data in pagamentos_pendentes.items():
        txid = data.get("txid")
        
        if not txid:
            continue
        
        status = await verificar_pagamento_efipay(txid)
        
        if status == "CONCLUIDA":
            # Pagamento confirmado!
            channel = bot.get_channel(int(channel_id))
            
            if channel:
                embed = discord.Embed(
                    title="✅ Pagamento Confirmado!",
                    description="O pagamento foi confirmado automaticamente pela Efipay!",
                    color=discord.Color.green()
                )
                embed.add_field(name="💰 Valor", value=f"R$ {data.get('valor', 0):.2f}", inline=True)
                
                # Tentar extrair ID do Game do tópico do canal
                game_id_ref = "Não identificado"
                if channel.topic and "ID:" in channel.topic:
                    try: game_id_ref = channel.topic.split("ID:")[1].strip()
                    except: pass
                
                embed.add_field(name="🆔 ID do Game", value=f"**{game_id_ref}**", inline=True)
                embed.add_field(name="🆔 ID da Transação", value=txid, inline=False)
                embed.set_footer(text=f"Confirmado em {datetime.now().strftime('%d/%m/%Y às %H:%M')}")
                
                await channel.send(embed=embed)
                
                # Adicionar comissão ao atendente automaticamente
                atendente_id = data.get("atendente_id")
                valor = data.get("valor", 0)
                
                if atendente_id and valor > 0:
                    usuarios = carregar_usuarios()
                    if atendente_id not in usuarios:
                        usuarios[atendente_id] = {"xp": 0, "level": 0, "comissao": 0}
                    
                    comissao = valor * 0.10  # 10% de comissão
                    usuarios[atendente_id]["comissao"] = usuarios[atendente_id].get("comissao", 0) + comissao
                    salvar_usuarios(usuarios)
                    
                    # Notificar atendente
                    try:
                        atendente = await bot.fetch_user(int(atendente_id))
                        embed_comissao = discord.Embed(
                            title="💰 Nova Comissão!",
                            description=f"Você recebeu uma comissão de **R$ {comissao:.2f}** pela venda!",
                            color=discord.Color.gold()
                        )
                        await atendente.send(embed=embed_comissao)
                    except:
                        pass
            
            canais_pagos.append(channel_id)
        
        elif status in ["REMOVIDA_PELO_USUARIO_RECEBEDOR", "REMOVIDA_PELO_PSP"]:
            # Pagamento expirado/removido
            channel = bot.get_channel(int(channel_id))
            if channel:
                embed = discord.Embed(
                    title="⏰ Pagamento Expirado",
                    description="O tempo para pagamento expirou. Solicite um novo link de pagamento ao atendente.",
                    color=discord.Color.orange()
                )
                await channel.send(embed=embed)
            
            canais_pagos.append(channel_id)
    
    # Remover pagamentos processados
    for channel_id in canais_pagos:
        pagamentos_pendentes.pop(channel_id, None)


@bot.event
async def on_ready():
    global config
    
    # Carregar configurações do arquivo JSON
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                saved_config = json.load(f)
                for key, value in saved_config.items():
                    try:
                        if isinstance(value, str):
                            if '.' in value:
                                config[key] = float(value)
                            elif value.isdigit():
                                config[key] = int(value)
                            else:
                                config[key] = value
                        else:
                            config[key] = value
                    except:
                        config[key] = value
                print(f'✅ Configurações carregadas de {CONFIG_FILE}')
        else:
            print(f'⚠️ {CONFIG_FILE} não encontrado, usando configurações padrão')
    except FileNotFoundError:
        print(f'⚠️ bot_config.json não encontrado, usando configurações padrão')
    except Exception as e:
        print(f'❌ Erro ao carregar configurações: {e}')
    
    # Registrar o botão para ele funcionar pra sempre
    bot.add_view(VerificacaoView())
    bot.add_view(PerfilView())
    bot.add_view(SugestaoView())
    bot.add_view(TicketFecharView())
    bot.add_view(TicketPanelView())

    # Iniciar loop de XP de voz
    if not check_voice_xp.is_running():
        check_voice_xp.start()
        
    # Iniciar loop de VIPs
    if not check_vips.is_running():
        check_vips.start()

    # Iniciar loop de expiração de moedas
    if not check_coin_expiration.is_running():
        check_coin_expiration.start()

    # Iniciar loop de cupons de evento
    if not check_event_coupons.is_running():
        check_event_coupons.start()

    # Iniciar loop de YouTube
    if not check_youtube_videos.is_running():
        check_youtube_videos.start()

    # Iniciar loop de Efipay
    if not check_efipay_payments.is_running():
        check_efipay_payments.start()

    # IA Removida

    # Nickname fixo (Removido o efeito de piscar)
    for guild in bot.guilds:
        try:
            if guild.me and guild.me.nick != "🔴 JOKER 🔴":
                await guild.me.edit(nick="🔴 JOKER 🔴")
        except: pass


    print(f'✅ Bot conectado como {bot.user.name}')
    print(f'📋 ID do Bot: {bot.user.id}')
    
    try:
        synced = await bot.tree.sync()
        print(f'✅ {len(synced)} comandos slash sincronizados')
    except Exception as e:
        print(f'❌ Erro ao sincronizar comandos: {e}')

    # Sincronizar cache de convites
    for guild in bot.guilds:
        await update_invite_cache(guild)
    print(f'✅ Cache de convites sincronizado para {len(bot.guilds)} servidores')

    # Definir status do bot
    try:
        await bot.change_presence(activity=discord.CustomActivity(name=" /ajuda 🧧Joker"))
        print('✅ Status definido para: informações /ajuda 🧧Joker')
    except Exception as e:
        print(f'❌ Erro ao definir status: {e}')

# Função para gerar imagem personalizada (AGORA ANIMADA)
async def gerar_imagem_perfil(member, title, color_hex):
    # Dimensões da imagem
    W, H = 1024, 500
    
    frames = []
    
    # Preparar base (background + overlay) apenas uma vez para performance
    try:
        bg_path = os.path.join(BASE_DIR, "Fundo Staff.png")
        if os.path.exists(bg_path):
            base_bg = Image.open(bg_path).convert("RGBA")
            base_bg = base_bg.resize((W, H))
            # Sem desfoque
        else:
            base_bg = Image.new("RGBA", (W, H), "#1a1a1a")
    except:
        base_bg = Image.new("RGBA", (W, H), "#1a1a1a")

    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 60))
    base_bg = Image.alpha_composite(base_bg, overlay)
    
    # Pre-carregar fontes
    try:
        font_ttf = os.path.join(BASE_DIR, "fonte.ttf")
        font_otf = os.path.join(BASE_DIR, "fonte.otf")
        if os.path.exists(font_ttf):
            font_title = ImageFont.truetype(font_ttf, 90)
            font_name = ImageFont.truetype(font_ttf, 60)
        elif os.path.exists(font_otf):
            font_title = ImageFont.truetype(font_otf, 90)
            font_name = ImageFont.truetype(font_otf, 60)
        else:
            font_title = ImageFont.truetype("arialbd.ttf", 90) 
            font_name = ImageFont.truetype("arialbd.ttf", 60)
    except:
        try:
            font_title = ImageFont.truetype("arial.ttf", 90)
            font_name = ImageFont.truetype("arial.ttf", 60)
        except:
            font_title = ImageFont.load_default()
            font_name = ImageFont.load_default()

    # Pre-carregar Avatar
    try:
        avatar_url = member.avatar.url if member.avatar else member.default_avatar.url
        response = requests.get(avatar_url)
        avatar_img_raw = Image.open(BytesIO(response.content)).convert("RGBA")
        avatar_size = 230
        avatar_img_raw = avatar_img_raw.resize((avatar_size, avatar_size))
        
        mask = Image.new("L", (avatar_size, avatar_size), 0)
        draw_mask = ImageDraw.Draw(mask)
        draw_mask.ellipse((0, 0, avatar_size, avatar_size), fill=255)
        
        avatar_final = ImageOps.fit(avatar_img_raw, mask.size, centering=(0.5, 0.5))
        avatar_final.putalpha(mask)
    except Exception as e:
        print(f"Erro avatar: {e}")
        avatar_final = None

    # Gerar quadros (Frames)
    # Vamos criar um efeito de "respiração" na borda (variando width de 4 a 10)
    # 10 frames é suficiente para um gif rápido e leve
    widths = [5, 6, 7, 8, 9, 10, 9, 8, 7, 6] 
    
    for w in widths:
        # Copiar background base
        frame = base_bg.copy()
        draw = ImageDraw.Draw(frame)
        
        # Avatar
        if avatar_final:
            avatar_x = (W - avatar_size) // 2
            avatar_y = 40 
            frame.paste(avatar_final, (avatar_x, avatar_y), avatar_final)
            
            # Borda ANIMADA
            draw.ellipse(
                (avatar_x-5, avatar_y-5, avatar_x+avatar_size+5, avatar_y+avatar_size+5), 
                outline="#FF4500", 
                width=w
            )

        # Título
        try:
            w_title = draw.textlength(title, font=font_title)
            x_title = (W - w_title) / 2
            y_title = 40 + 230 + 15 
            
            draw.text((x_title + 4, y_title + 4), title, font=font_title, fill="#8B0000")
            draw.text((x_title, y_title), title, font=font_title, fill="white", stroke_width=3, stroke_fill="black")
        except:
            pass

        # Nome
        try:
            name_text = str(member.name).upper()
            w_name = draw.textlength(name_text, font=font_name)
            x_name = (W - w_name) / 2
            y_name = (40 + 230 + 15) + 90
            
            draw.text((x_name + 3, y_name + 3), name_text, font=font_name, fill="#8B0000")
            draw.text((x_name, y_name), name_text, font=font_name, fill="white", stroke_width=2, stroke_fill="black")
        except:
            pass
            
        frames.append(frame)

    buffer = BytesIO()
    # Salvar como GIF
    frames[0].save(
        buffer, 
        format="GIF", 
        save_all=True, 
        append_images=frames[1:], 
        optimize=True, 
        duration=100, # 100ms por frame
        loop=0
    )
    buffer.seek(0)
    return buffer

async def gerar_imagem_rank(pagina_atual, pagina_num, total_paginas, user_pos, user_xp, guild):
    # Dimensões
    W, H = 1000, 1100
    
    try:
        bg_path = os.path.join(BASE_DIR, "Fundo Staff.png")
        if os.path.exists(bg_path):
            img = Image.open(bg_path).convert("RGBA")
            img = img.resize((W, H))
        else:
            img = Image.new("RGBA", (W, H), "#1a1a1a")
    except Exception as e:
        print(f"Erro ao carregar fundo: {e}")
        img = Image.new("RGBA", (W, H), "#1a1a1a")

    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 160))
    img = Image.alpha_composite(img, overlay)
    draw = ImageDraw.Draw(img)

    # Fontes
    try:
        font_path = os.path.join(BASE_DIR, "fonte.otf")
        if not os.path.exists(font_path):
            font_path = os.path.join(BASE_DIR, "fonte.ttf")
            
        if os.path.exists(font_path):
            font_big = ImageFont.truetype(font_path, 60)
            font_mid = ImageFont.truetype(font_path, 40)
            font_small = ImageFont.truetype(font_path, 25)
        else:
            # Fallback para arial se existir, senão default
            try:
                font_big = ImageFont.truetype("arial.ttf", 60)
                font_mid = ImageFont.truetype("arial.ttf", 40)
                font_small = ImageFont.truetype("arial.ttf", 25)
            except:
                font_big = font_mid = font_small = ImageFont.load_default()
    except:
        font_big = font_mid = font_small = ImageFont.load_default()

    # Cabeçalho
    g_name = guild.name
    try:
        w_g = draw.textlength(g_name, font=font_big)
        draw.text(((W - w_g) / 2, 40), g_name, font=font_big, fill="white")
    except:
        draw.text((W/2 - 100, 40), g_name, font=font_big, fill="white")

    p_info = f"Página {pagina_num} de {total_paginas}"
    try:
        w_p = draw.textlength(p_info, font=font_small)
        draw.text(((W - w_p) / 2, 110), p_info, font=font_small, fill="#aaaaaa")
    except:
        draw.text((W/2 - 50, 110), p_info, font=font_small, fill="#aaaaaa")
    
    y_offset = 160
    
    # Sua Posição (se houver)
    if user_pos > 0:
        draw.rectangle([50, y_offset, W-50, y_offset+70], fill=(255, 69, 0, 100))
        draw.text((70, y_offset+15), f"SUA POSIÇÃO: #{user_pos} | XP: {user_xp:,}", font=font_mid, fill="white")
        y_offset += 90

    # Listar Membros
    for i, (u_id, data) in enumerate(pagina_atual, 1):
        actual_pos = ((pagina_num-1) * 10) + i
        xp = data.get("xp", 0)
        lv = data.get("level", 0)
        
        # Tentar pegar o nome do membro
        try:
            member = guild.get_member(int(u_id))
            nome_membro = member.name if member else f"Usuário {u_id}"
        except:
            nome_membro = f"Usuário {u_id}"

        # Box para cada membro
        draw.rectangle([50, y_offset, W-50, y_offset+85], fill=(0, 0, 0, 120))
        
        # Posição
        draw.text((70, y_offset+10), f"#{actual_pos}", font=font_mid, fill="#FFD700")
        
        # Nome e ID
        draw.text((160, y_offset+10), f"{nome_membro}", font=font_mid, fill="white")
        draw.text((160, y_offset+50), f"ID: {u_id} | XP: {xp:,} // NÍVEL: {lv}", font=font_small, fill="#00BFFF")
        
        y_offset += 95

    buffer = BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer

# --- Sistema de XP de Voz ---
@tasks.loop(minutes=1)
async def check_voice_xp():
    try:
        # Carregar config localmente para pegar o canal AFK
        afk_channel_id = config.get("afk_channel_id", 0)
        usuarios = carregar_usuarios()
        alterado = False

        for guild in bot.guilds:
            for voice_channel in guild.voice_channels:
                if voice_channel.id == afk_channel_id:
                    continue
                for member in voice_channel.members:
                    if member.bot: continue
                    
                    try:
                        user_id = str(member.id)
                        
                        # Verificar se o usuário está mutado/deaf (AFK no discord)
                        if not member.voice: continue # Segurança extra
                        
                        is_silent = member.voice.self_mute or member.voice.mute or member.voice.self_deaf or member.voice.deaf
                        if is_silent:
                            tempo_afk[user_id] = tempo_afk.get(user_id, 0) + 1
                            if tempo_afk[user_id] >= 5 and afk_channel_id != 0:
                                afk_channel = bot.get_channel(afk_channel_id)
                                if afk_channel:
                                    try:
                                        await member.move_to(afk_channel)
                                        tempo_afk[user_id] = 0
                                    except: pass
                        else:
                            tempo_afk[user_id] = 0
                            if user_id not in usuarios:
                                usuarios[user_id] = {"xp": 0, "level": 0}
                            
                            nivel_atual = usuarios[user_id].get("level", 0)
                            
                            xp_atual = usuarios[user_id].get("xp", 0) + 10 # 10 XP por minuto em call
                            
                            usuarios[user_id]["xp"] = xp_atual
                            
                            novo_nivel = xp_atual // 500
                            usuarios[user_id]["level"] = novo_nivel
                            
                            if novo_nivel > nivel_atual:
                                # Usar create_task para não bloquear
                                asyncio.create_task(gerenciar_cargos_nivel(member, novo_nivel))
                                
                            alterado = True
                    except Exception as e_member:
                        print(f"⚠️ Erro ao processar membro {member.name} no check_voice_xp: {e_member}")
                    else:
                        tempo_afk[user_id] = 0
                        if user_id not in usuarios:
                            usuarios[user_id] = {"xp": 0, "level": 0}
                        
                        nivel_atual = usuarios[user_id].get("level", 0)
                        
                        xp_atual = usuarios[user_id].get("xp", 0) + 10 # 10 XP por minuto em call
                        
                        usuarios[user_id]["xp"] = xp_atual
                        
                        novo_nivel = xp_atual // 500
                        usuarios[user_id]["level"] = novo_nivel
                        
                        if novo_nivel > nivel_atual:
                             asyncio.create_task(gerenciar_cargos_nivel(member, novo_nivel))
                            
                        alterado = True
        
        if alterado:
            salvar_usuarios(usuarios)
    except Exception as e:
        print(f"❌ Erro no check_voice_xp: {e}")

@bot.event
async def on_voice_state_update(member, before, after):
    """Gerencia a criação e exclusão de salas de voz temporárias"""
    global config
    
    # 1. CRIAR SALA (Quando entra no canal master)
    master_channel_id = config.get('create_call_channel_id')
    
    if after.channel and after.channel.id == master_channel_id:
        try:
            guild = member.guild
            categoria = after.channel.category
            
            # Criar o canal de voz temporário
            channel_name = f"Sala de {member.name}"
            new_channel = await guild.create_voice_channel(
                name=channel_name,
                category=categoria,
                reason=f"Canal temporário para {member.name}"
            )
            
            # Adicionar ao set de canais temporários
            canais_temporarios.add(new_channel.id)
            
            # Mover o membro para a nova sala
            await member.move_to(new_channel)
            print(f"🔊 Sala temporária criada: {channel_name}")
            
        except Exception as e:
            print(f"❌ Erro ao criar sala temporária: {e}")

    # 2. DELETAR SALA (Quando a sala fica vazia)
    if before.channel and before.channel.id in canais_temporarios:
        if len(before.channel.members) == 0:
            try:
                channel_id = before.channel.id
                await before.channel.delete(reason="Sala temporária vazia")
                canais_temporarios.discard(channel_id)
                print(f"🗑️ Sala temporária {before.channel.name} removida por estar vazia.")
            except Exception as e:
                print(f"❌ Erro ao deletar sala temporária: {e}")

@bot.event
async def on_voice_state_update(member, before, after):
    """Gerencia a criação e exclusão de salas de voz temporárias"""
    global config
    
    # 1. CRIAR SALA (Quando entra no canal master)
    master_channel_id = config.get('create_call_channel_id')
    
    if after.channel and after.channel.id == master_channel_id:
        try:
            guild = member.guild
            categoria = after.channel.category
            
            # Criar o canal de voz temporário
            channel_name = f"Sala de {member.name}"
            new_channel = await guild.create_voice_channel(
                name=channel_name,
                category=categoria,
                reason=f"Canal temporário para {member.name}"
            )
            
            # Adicionar ao set de canais temporários
            canais_temporarios.add(new_channel.id)
            
            # Mover o membro para a nova sala
            await member.move_to(new_channel)
            print(f"🔊 Sala temporária criada: {channel_name}")
            
        except Exception as e:
            print(f"❌ Erro ao criar sala temporária: {e}")

    # 2. DELETAR SALA (Quando a sala fica vazia)
    if before.channel and before.channel.id in canais_temporarios:
        if len(before.channel.members) == 0:
            try:
                channel_id = before.channel.id
                await before.channel.delete(reason="Sala temporária vazia")
                canais_temporarios.discard(channel_id)
                print(f"🗑️ Sala temporária {before.channel.name} removida por estar vazia.")
            except Exception as e:
                print(f"❌ Erro ao deletar sala temporária: {e}")

    # 3. VERIFICAR VIP CLÃ (Voz)
    clans = carregar_clans()
    for c_owner_id, c_data in clans.items():
        if after.channel and after.channel.id == c_data.get("vc_channel_id"):
            exp_str = c_data.get("expiracao")
            if exp_str:
                exp_dt = datetime.fromisoformat(exp_str)
                if datetime.now() > exp_dt:
                    # VIP Vencido: Apenas o dono pode ficar no voice
                    if str(member.id) != c_owner_id:
                        try:
                            await member.move_to(None, reason="VIP do Clã Vencido")
                            await member.send(f"❌ O canal de voz do clã **{c_data['nome']}** está bloqueado porque o VIP do clã venceu!")
                        except: pass

@bot.event
async def on_message(message):
    # Ignorar mensagens de bots
    if message.author.bot:
        return
    
    # Resposta automática para DMs
    if message.guild is None:
        embed = discord.Embed(
            title="🔥 Olá! Eu sou o STAFF!",
            description="Obrigado por entrar em contato!\n\nEu sou o bot oficial do servidor **STAFF**.\nPara ver meus comandos, use `/ajuda` no servidor!",
            color=discord.Color.orange(),
            timestamp=datetime.now()
        )
        
        embed.add_field(
            name="🎮 Entre no nosso servidor!",
            value="[Clique aqui para entrar](https://discord.gg/5YWbbBZc8y)",
            inline=False
        )
        
        embed.add_field(
            name="🔗 Nossas Redes Sociais",
            value=(
                "📺 [YouTube](https://www.youtube.com/@STAFFmtaoficial)\n"
                "🎵 [TikTok](https://www.tiktok.com/@STAFFmtaoficial)\n"
                "📸 [Instagram](https://www.instagram.com/STAFFmtaoficial/)"
            ),
            inline=False
        )
        
        embed.set_thumbnail(url=bot.user.avatar.url if bot.user.avatar else None)
        embed.set_footer(text="STAFF • Feito com ❤️", icon_url=bot.user.avatar.url if bot.user.avatar else None)
        
        try:
            await message.channel.send(embed=embed)
        except:
            pass
        return

    # Processar XP por mensagem
    user_id = str(message.author.id)
    agora = datetime.now()
    content = message.content.lower()

    # --- NOVO: Detecção de Comissão em Tickets ---
    cat_loja = config.get('ticket_category_loja_id')
    cat_suporte = config.get('ticket_category_suporte_id')
    
    if message.channel.category_id in [cat_loja, cat_suporte]:
        # Verificar se é um valor sendo falado (Ex: R$ 50,00, 50.00, 20 reais)
        # Regex para pegar valores monetários
        padrao_valor = r'(?:r\$\s*)?(\d+(?:[.,]\d{2})?)'
        match = re.search(padrao_valor, content)
        
        if match:
            valor_str = match.group(1).replace(',', '.')
            try:
                valor = float(valor_str)
                
                # Identificar o Atendente (Pode ser o autor se for staff, ou o último staff que falou)
                role_parceiro = discord.utils.get(message.guild.roles, name="🎥Parceiros")
                is_staff = (role_parceiro in message.author.roles) or message.author.guild_permissions.administrator
                
                # Se quem falou foi o staff (@🎥Parceiros), a comissão vai pra ele
                # Se foi o cliente, a comissão vai para o atendente que está no tópico ou o último staff que falou
                target_atendente_id = None
                
                if is_staff:
                    target_atendente_id = user_id
                    # Atualizar tópico para marcar este atendente como responsável
                    if message.channel.topic and "| Atendente:" not in message.channel.topic:
                        try:
                            new_topic = f"{message.channel.topic} | Atendente: {message.author.id}"
                            await message.channel.edit(topic=new_topic)
                        except: pass
                else:
                    # Se foi o cliente, tenta pegar do tópico
                    if message.channel.topic and "| Atendente:" in message.channel.topic:
                        target_atendente_id = message.channel.topic.split("| Atendente: ")[-1].strip()
                
                if target_atendente_id:
                    # A comissão agora é processada APENAS no fechamento do ticket.
                    pass

                # --- AUTOMAÇÃO TICKET LOJA: Pix após o membro falar ---
                if message.channel.category_id == config.get('ticket_category_loja_id'):
                    # Verificar se quem mandou a mensagem é o dono do ticket (não é staff)
                    role_parceiro = discord.utils.get(message.guild.roles, name="🎥Parceiros")
                    is_staff = (role_parceiro in message.author.roles) or message.author.guild_permissions.administrator
                    
                    if not is_staff:
                        # Verificar se o bot já enviou o Pix neste canal (usando o histórico recente ou uma tag de controle no tópico)
                        # Para ser simples e direto, verificamos se o bot já postou o embed de pagamento
                        ja_mandou_pix = False
                        async for msg in message.channel.history(limit=50):
                            if msg.author == bot.user and msg.embeds:
                                if msg.embeds[0].title == "💸 Pagamento via PIX":
                                    ja_mandou_pix = True
                                    break
                        
                        # SISTEMA DE PIX ESTÁTICO DESATIVADO - Agora usando PushinPay
                        # if not ja_mandou_pix:
                        #     valor_pix = config.get('pix_default_code')
                        #     if valor_pix:
                        #         # Gerar o QR Code
                        #         qr = qrcode.QRCode(version=1, box_size=10, border=4)
                        #         qr.add_data(valor_pix)
                        #         qr.make(fit=True)
                        #         img = qr.make_image(fill_color="black", back_color="white")
                        #         
                        #         buffer = BytesIO()
                        #         img.save(buffer, format="PNG")
                        #         buffer.seek(0)
                        #         buffer.seek(0)
                        #         
                        #         file = discord.File(buffer, filename="pix_qr.png")
                        #         embed_pix = discord.Embed(
                        #             title="💸 Pagamento via PIX",
                        #             description="Para agilizar o seu atendimento, você pode realizar o pagamento agora mesmo!\n\n**Código Copia e Cola:**",
                        #             color=discord.Color.green()
                        #         )
                        #         embed_pix.add_field(name="\u200b", value=f"```\n{valor_pix}\n```", inline=False)
                        #         embed_pix.set_image(url="attachment://pix_qr.png")
                        #         embed_pix.set_footer(text="Após pagar, clique no botão abaixo para confirmar.")
                        #         
                        #         await message.channel.send(embed=embed_pix, file=file)
                        #         await message.channel.send("📥 **Já realizou o pagamento?** Clique no botão abaixo para avisar a equipe!", view=TicketLojaPagamentoView())
            except:
                pass

    # Validação simples de mensagem (como no botmain.py)
    if 5 <= len(content) <= 10 and len(set(content)) >= 3:
        # Cooldown de 10 segundos para XP
        can_get_xp = True
        if user_id in xp_cooldowns:
            if (agora - xp_cooldowns[user_id]).total_seconds() < 10:
                can_get_xp = False

        if can_get_xp:
            usuarios = carregar_usuarios()
            if user_id not in usuarios:
                usuarios[user_id] = {"xp": 0, "level": 0}
            
            nivel_antigo = usuarios[user_id].get("level", 0)
            
            # Verificar se já está no nível máximo (100)
            novo_xp = usuarios[user_id].get("xp", 0) + 5
                
            usuarios[user_id]["xp"] = novo_xp
            novo_nivel = novo_xp // 500
            usuarios[user_id]["level"] = novo_nivel
            
            # Se subiu de nível
            if novo_nivel > nivel_antigo:
                try:
                    await message.channel.send(f"🎉 Parabéns {message.author.mention}! Você subiu para o **Nível {novo_nivel}**!")
                except: pass
                
                await gerenciar_cargos_nivel(message.author, novo_nivel)

            salvar_usuarios(usuarios)
            
            xp_cooldowns[user_id] = agora

    # --- NOVO: Verificação de VIP de Clã ---
    clans = carregar_clans()
    for c_owner_id, c_data in clans.items():
        if message.channel.id == c_data.get("txt_channel_id"):
            exp_str = c_data.get("expiracao")
            if exp_str:
                exp_dt = datetime.fromisoformat(exp_str)
                if datetime.now() > exp_dt:
                    # VIP do Clã Vencido
                    if str(message.author.id) != c_owner_id:
                        # Membro falando em clã vencido: Deletar
                        await message.delete()
                        try:
                            await message.author.send(f"❌ Você não pode falar no chat do clã **{c_data['nome']}** porque o VIP do clã está **VENCIDO**!")
                        except: pass
                        return
                    else:
                        # Dono falando em clã vencido: Aviso de renovação
                        embed_aviso = discord.Embed(
                            title="⏳ VIP Clã Vencido!",
                            description=f"Seu clã **{c_data['nome']}** está com o VIP vencido.\n\nOs membros não podem falar no chat nem entrar no voice até que você renove!",
                            color=discord.Color.red()
                        )
                        await message.channel.send(embed=embed_aviso, delete_after=10)

    # CRITICAL: Processar comandos
    await bot.process_commands(message)

@bot.event
async def on_invite_create(invite):
    """Atualiza o cache quando um convite é criado"""
    if invite.guild.id not in invites_cache:
        invites_cache[invite.guild.id] = {}
    invites_cache[invite.guild.id][invite.code] = invite.uses

@bot.event
async def on_invite_delete(invite):
    """Remove do cache quando um convite é deletado"""
    if invite.guild.id in invites_cache:
        invites_cache[invite.guild.id].pop(invite.code, None)

@bot.event
async def on_member_join(member):
    """Evento quando um novo membro entra no servidor"""
    global config
    
    # --- Rastreamento de Convite ---
    inviter = "Desconhecido"
    invite_code = "Desconhecido"
    
    if member.guild.id in invites_cache and member.guild.me.guild_permissions.manage_guild:
        try:
            old_invites = invites_cache[member.guild.id]
            new_invites = await member.guild.invites()
            
            for invite in new_invites:
                if old_invites.get(invite.code) is not None:
                    if invite.uses > old_invites[invite.code]:
                        inviter = invite.inviter
                        invite_code = invite.code
                        break
            
            # Atualizar cache após detecção
            invites_cache[member.guild.id] = {invite.code: invite.uses for invite in new_invites}
        except Exception as e:
            print(f"⚠️ Erro ao rastrear convite em {member.guild.name}: {e}")

    # Enviar log de convite
    channel_invite_log_id = config.get('invite_logs_channel_id')
    if channel_invite_log_id:
        invite_log_channel = bot.get_channel(int(channel_invite_log_id))
        if invite_log_channel:
            try:
                inviter_mention = inviter.mention if hasattr(inviter, 'mention') else f"**{inviter}**"
                msg_convite = f"🚪 {member.mention} entrou no servidor!\n👤 **Convidado por:** {inviter_mention}\n🎫 **Código:** `{invite_code}`"
                await invite_log_channel.send(msg_convite)
            except Exception as e:
                print(f"❌ Erro ao enviar log de convite: {e}")

    # Enviar mensagem de boas-vindas
    if 'welcome_channel_id' in config and config['welcome_channel_id']:
        channel = bot.get_channel(config['welcome_channel_id'])
        if channel:
            try:
                # Gerar imagem (GIF)
                buffer = await gerar_imagem_perfil(member, "BEM-VINDO", "#ffff00")
                file = discord.File(buffer, filename="welcome.gif")
                
                # Criar embed personalizado
                embed = discord.Embed(
                    description=f"Olá {member.mention}, seja muito bem-vindo(a) ao **{member.guild.name}**!\n\nEsperamos que você se divirta muito por aqui! Não esqueça de ler as regras.",
                    color=discord.Color.green(),
                    timestamp=datetime.now()
                )
                
                embed.set_footer(text=f"ID: {member.id}")
                embed.set_image(url="attachment://welcome.gif")
                
                await channel.send(embed=embed, file=file)
                print(f'✅ Boas-vindas enviada para {member.name}')
            except Exception as e:
                print(f'❌ Erro ao enviar boas-vindas: {e}')

@bot.event
async def on_member_remove(member):
    """Evento quando um membro sai do servidor"""
    global config
    
    # Remover reação da verificação quando sair
    if 'verification_message_id' in config and 'verification_channel_id' in config:
        try:
            channel = bot.get_channel(config['verification_channel_id'])
            if channel:
                message = await channel.fetch_message(config['verification_message_id'])
                await message.remove_reaction("✅", member)
                print(f'✅ Reação de verificação removida para {member.name}')
        except Exception as e:
            print(f'⚠️ Não foi possível remover reação: {e}')

    if 'leave_channel_id' in config and config['leave_channel_id']:
        channel = bot.get_channel(config['leave_channel_id'])
        if channel:
            try:
                # Gerar imagem (GIF)
                buffer = await gerar_imagem_perfil(member, "ATÉ LOGO", "#ff0000")
                file = discord.File(buffer, filename="leave.gif")
                
                embed = discord.Embed(
                    description=f"**{member.name}** saiu do servidor. Sentiremos sua falta!",
                    color=discord.Color.red(),
                    timestamp=datetime.now()
                )
                
                embed.set_footer(text=f"Membro #{member.guild.member_count}")
                embed.set_image(url="attachment://leave.gif")
                
                await channel.send(embed=embed, file=file)
                print(f'✅ Saída enviada para {member.name}')
            except Exception as e:
                print(f'❌ Erro ao enviar mensagem de saída: {e}')
    
@bot.event
async def on_member_update(before, after):
    """Evento quando um membro impulsiona o servidor"""
    global config
    
    # Verificar se o status de boost mudou (não era booster -> virou booster)
    if not before.premium_since and after.premium_since:
        if 'booster_channel_id' in config and config['booster_channel_id']:
            channel = bot.get_channel(config['booster_channel_id'])
            if channel:
                try:
                    # Gerar imagem (GIF)
                    buffer = await gerar_imagem_perfil(after, "BOOSTER", "#ff00ff")
                    file = discord.File(buffer, filename="booster.gif")
                    
                    embed = discord.Embed(
                        title="🚀 Novo Booster!",
                        description=f"Obrigado {after.mention} por impulsionar o servidor! 🎉",
                        color=discord.Color.purple(),
                        timestamp=datetime.now()
                    )
                    
                    embed.set_thumbnail(url=after.avatar.url if after.avatar else after.default_avatar.url)
                    embed.set_image(url="attachment://booster.gif")
                    
                    await channel.send(embed=embed, file=file)
                    print(f'✅ Mensagem de booster enviada para {after.name}')
                except Exception as e:
                    print(f'❌ Erro ao enviar mensagem de booster: {e}')

# Sistema de Verificação (Botão)
class VerificacaoView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None) # Timeout=None para o botão não parar de funcionar
    
    @discord.ui.button(label="Verificar", style=discord.ButtonStyle.green, emoji="✅", custom_id="verificar_button")
    async def verificar_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        global config
        
        # Verificar se a config de cargo existe
        if 'member_role_id' in config and config['member_role_id']:
            role_id = config['member_role_id']
            role = interaction.guild.get_role(role_id)
            
            if role:
                if role in interaction.user.roles:
                    await interaction.response.send_message("❌ Você já está verificado!", ephemeral=True)
                else:
                    try:
                        await interaction.user.add_roles(role)
                        await interaction.response.send_message("✅ Verificado com sucesso! Acesso liberado.", ephemeral=True)
                        print(f'✅ Cargo membro adicionado para {interaction.user.name} via botão')
                    except discord.Forbidden:
                        await interaction.response.send_message("❌ **ERRO:** O Bot não tem permissão! Peça para um Admin mover o cargo do Bot para cima do cargo de Membro.", ephemeral=True)
                        print(f'❌ Erro Permissão: Bot abaixo do cargo {role.name}')
                    except Exception as e:
                        await interaction.response.send_message("❌ Erro ao dar cargo. Contate um admin.", ephemeral=True)
                        print(f'❌ Erro ao dar cargo via botão: {e}')
            else:
                await interaction.response.send_message("❌ Cargo de membro não configurado corretamente.", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Sistema de verificação não configurado.", ephemeral=True)

@bot.tree.command(name="verificacao", description="Criar painel de verificação (Botão)")
@app_commands.describe(canal="Canal onde enviar o painel de verificação")
async def criar_verificacao(interaction: discord.Interaction, canal: discord.TextChannel = None):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ Você precisa ser administrador para usar este comando!", ephemeral=True)
        return
    
    target_channel = canal or interaction.channel
    
    embed = discord.Embed(
        title="✅ Verificação",
        description="Clique no botão abaixo para se verificar e liberar os canais!",
        color=discord.Color.green()
    )
    
    # Enviar a view com o botão
    await target_channel.send(embed=embed, view=VerificacaoView())
    await interaction.response.send_message(f"✅ Painel criado em {target_channel.mention}!", ephemeral=True)

# Comando de Regras
@bot.tree.command(name="regras", description="Envia as regras do servidor em um embed")
@app_commands.describe(canal="Canal para enviar as regras (opcional)")
async def enviar_regras(interaction: discord.Interaction, canal: discord.TextChannel = None):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ Você precisa ser administrador para usar este comando!", ephemeral=True)
        return
    
    # Determinar o canal onde enviar as regras
    target_channel = canal or interaction.channel
    
    try:
        # Criar embed das regras baseado na imagem fornecida
        embed = discord.Embed(
            title="📜 REGRAS DO SERVIDOR",
            color=discord.Color.blue()
        )
        
        # Cabeçalho (simulando o "Sapphire APP" e data da imagem)
        current_time = datetime.now().strftime("%d/%m/%Y %H:%M")
        embed.set_author(name="STAFF", icon_url=bot.user.avatar.url if bot.user.avatar else None)
        embed.description = ""
        
        regras_path = os.path.join(BASE_DIR, "Regras.png")
        if os.path.exists(regras_path):
            arquivo_regras = discord.File(regras_path, filename="Regras.png")
            embed.set_image(url="attachment://Regras.png")
        else:
            arquivo_regras = None
            embed.description = "⚠️ *A imagem Regras.png não foi encontrada.*"
        
        # Rodapé
        embed.set_footer(text="Reaja com ✅ para confirmar que leu e aceita as regras")
        
        # Enviar embed
        if arquivo_regras:
            message = await target_channel.send(embed=embed, file=arquivo_regras)
        else:
            message = await target_channel.send(embed=embed)
        
        # Adicionar reação
        await message.add_reaction("✅")
        
        # Responder ao usuário
        await interaction.response.send_message(
            f"✅ Regras enviadas com sucesso em {target_channel.mention}!",
            ephemeral=True
        )
        
        print(f'✅ Regras enviadas por {interaction.user.name} em #{target_channel.name}')
        
    except Exception as e:
        await interaction.response.send_message(
            f"❌ Erro ao enviar regras: {e}",
            ephemeral=True
        )
        print(f'❌ Erro ao enviar regras: {e}')

# Comandos de Configuração
@bot.tree.command(name="configurar_boas_vindas", description="Configurar canal de boas-vindas")
@app_commands.describe(canal="Canal para mensagens de boas-vindas", imagem_url="URL da imagem (opcional)")
async def configurar_boas_vindas(interaction: discord.Interaction, canal: discord.TextChannel, imagem_url: str = None):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ Você precisa ser administrador para usar este comando!", ephemeral=True)
        return
    
    global config
    config['welcome_channel_id'] = canal.id
    if imagem_url:
        config['welcome_image'] = imagem_url
    
    embed = discord.Embed(
        title="✅ Configuração Salva",
        description=f"Canal de boas-vindas definido para {canal.mention}",
        color=discord.Color.green()
    )
    if imagem_url:
        embed.add_field(name="🖼️ Imagem", value=imagem_url)
    
    await interaction.response.send_message(embed=embed)
    print(f'✅ Canal de boas-vindas configurado por {interaction.user.name}')

@bot.tree.command(name="configurar_saida", description="Configurar canal de saída")
@app_commands.describe(canal="Canal para mensagens de saída", imagem_url="URL da imagem (opcional)")
async def configurar_saida(interaction: discord.Interaction, canal: discord.TextChannel, imagem_url: str = None):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ Você precisa ser administrador para usar este comando!", ephemeral=True)
        return
    
    global config
    config['leave_channel_id'] = canal.id
    if imagem_url:
        config['leave_image'] = imagem_url
    
    embed = discord.Embed(
        title="✅ Configuração Salva",
        description=f"Canal de saída definido para {canal.mention}",
        color=discord.Color.green()
    )
    if imagem_url:
        embed.add_field(name="🖼️ Imagem", value=imagem_url)
    
    await interaction.response.send_message(embed=embed)
    print(f'✅ Canal de saída configurado por {interaction.user.name}')

@bot.tree.command(name="configurar_booster", description="Configurar canal de booster")
@app_commands.describe(canal="Canal para mensagens de booster", imagem_url="URL da imagem (opcional)")
async def configurar_booster(interaction: discord.Interaction, canal: discord.TextChannel, imagem_url: str = None):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ Você precisa ser administrador para usar este comando!", ephemeral=True)
        return
    
    global config
    config['booster_channel_id'] = canal.id
    if imagem_url:
        config['booster_image'] = imagem_url
    
    embed = discord.Embed(
        title="✅ Configuração Salva",
        description=f"Canal de booster definido para {canal.mention}",
        color=discord.Color.green()
    )
    if imagem_url:
        embed.add_field(name="🖼️ Imagem", value=imagem_url)
    
    await interaction.response.send_message(embed=embed)
    print(f'✅ Canal de booster configurado por {interaction.user.name}')

@bot.tree.command(name="configurar_cargo_membro", description="Configurar cargo para novos membros")
async def configurar_cargo_membro(interaction: discord.Interaction, cargo: discord.Role):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ Você precisa ser administrador para usar este comando!", ephemeral=True)
        return
    
    global config
    config['member_role_id'] = cargo.id
    
    embed = discord.Embed(
        title="✅ Configuração Salva",
        description=f"Cargo de membro definido para {cargo.mention}",
        color=discord.Color.green()
    )
    await interaction.response.send_message(embed=embed)
    print(f'✅ Cargo de membro configurado por {interaction.user.name}')

# Comandos de Ticket
@bot.tree.command(name="configurar_tickets_loja", description="Configurar categoria para tickets de loja")
async def configurar_tickets_loja(interaction: discord.Interaction, categoria: discord.CategoryChannel):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ Você precisa ser administrador para usar este comando!", ephemeral=True)
        return
    
    global config
    config['ticket_category_loja_id'] = categoria.id
    
    embed = discord.Embed(
        title="✅ Configuração Salva",
        description=f"Categoria para tickets de loja definida para **{categoria.name}**",
        color=discord.Color.green()
    )
    await interaction.response.send_message(embed=embed)
    print(f'✅ Categoria de tickets loja configurada por {interaction.user.name}')

@bot.tree.command(name="configurar_tickets_suporte", description="Configurar categoria para tickets de suporte")
async def configurar_tickets_suporte(interaction: discord.Interaction, categoria: discord.CategoryChannel):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ Você precisa ser administrador para usar este comando!", ephemeral=True)
        return
    
    global config
    config['ticket_category_suporte_id'] = categoria.id
    
    embed = discord.Embed(
        title="✅ Configuração Salva",
        description=f"Categoria para tickets de suporte definida para **{categoria.name}**",
        color=discord.Color.green()
    )
    await interaction.response.send_message(embed=embed)
    print(f'✅ Categoria de tickets suporte configurada por {interaction.user.name}')

@bot.tree.command(name="configurar_logs_ticket", description="Configurar canal para logs/transcripts de tickets")
async def configurar_logs_ticket(interaction: discord.Interaction, canal: discord.TextChannel):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ Você precisa ser administrador para usar este comando!", ephemeral=True)
        return
    
    global config
    config['ticket_logs_channel_id'] = canal.id
    
    # Salvar no JSON
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                saved_config = json.load(f)
        else:
            saved_config = {}
        
        saved_config['ticket_logs_channel_id'] = str(canal.id)
        
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(saved_config, f, indent=4)
    except Exception as e:
        print(f"❌ Erro ao salvar config de logs: {e}")

    embed = discord.Embed(
        title="✅ Configuração Salva",
        description=f"Canal de logs de tickets definido para {canal.mention}",
        color=discord.Color.green()
    )
    await interaction.response.send_message(embed=embed)





# --- SISTEMA DE DESCONTO COM MOEDAS ---

async def trigger_pix_flow(interaction: discord.Interaction, valor_texto, produto_nome, game_id: str = None):
    """Gera o fluxo de pagamento PIX (Efipay ou Estático)"""
    pix_code = None
    tx_id = None
    qr_code_base64 = None
    valor_final = 0.0
    
    # Tenta gerar via Efipay se houver valor identificado
    if 'R$' in valor_texto:
        try:
            # Limpeza robusta de valor monetário
            valor_limpo = valor_texto.replace('R$', '').strip()
            if ',' in valor_limpo and '.' in valor_limpo:
                # Provável formato 1.234,56
                valor_limpo = valor_limpo.replace('.', '').replace(',', '.')
            elif ',' in valor_limpo:
                # Provável formato 30,00
                valor_limpo = valor_limpo.replace(',', '.')
            
            match = re.search(r'[\d\.]+', valor_limpo)
            if match:
                valor_final = float(match.group(0))
                
                # Se Efipay estiver ativa, usa ela
                if config.get("efipay_enabled", False):
                    # Incluir o ID do Game na descrição da cobrança
                    descricao = f"Compra {produto_nome} - ID Game {game_id}" if game_id else f"Compra {produto_nome} - {interaction.user.name}"
                    payment_data = await criar_pagamento_efipay(valor_final, descricao)
                    if payment_data:
                        pix_code = payment_data.get("qr_code")
                        tx_id = payment_data.get("txid")
                        qr_code_base64 = payment_data.get("qr_code_base64")
        except Exception as e:
            print(f"❌ Erro ao processar valor para Efipay: {e}")
    
    # Se falhou ou Efipay desativada, usa o padrão estático (apenas para exibição, sem verificação automática extra)
    if not pix_code:
        pix_code = config.get('pix_default_code')
        
    if pix_code:
        # Preparar arquivo de imagem (QR Code)
        if qr_code_base64:
            import base64
            image_data = base64.b64decode(qr_code_base64.split(",")[-1])
            buffer = BytesIO(image_data)
        else:
            # Gerar o QR Code localmente se não veio da API
            qr = qrcode.QRCode(version=1, box_size=10, border=4)
            qr.add_data(pix_code)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")
            
            buffer = BytesIO()
            img.save(buffer, format="PNG")
        
        buffer.seek(0)
        file = discord.File(buffer, filename="pix_qr.png")
        
        embed_pix = discord.Embed(
            title="💳 Pagamento via PIX - Efipay",
            description=f"**Produto:** {produto_nome}\n**Valor:** {valor_texto}\n**ID Game:** {game_id if game_id else 'Não informado'}\n\nPara agilizar o seu atendimento, você pode realizar o pagamento agora mesmo!\n\n**Código Copia e Cola:**",
            color=discord.Color.green()
        )
        embed_pix.add_field(name="\u200b", value=f"```\n{pix_code}\n```", inline=False)
        
        if tx_id:
            embed_pix.set_footer(text=f"ID Transação: {tx_id} • O pagamento será confirmado automaticamente.")
            # Salvar nos pagamentos pendentes para controle automático
            global pagamentos_pendentes
            pagamentos_pendentes[str(interaction.channel.id)] = {
                "txid": tx_id,
                "valor": valor_final,
                "atendente_id": str(interaction.user.id)
            }
        else:
            embed_pix.set_footer(text="Após pagar, envie o comprovante para a equipe.")
            
        embed_pix.set_image(url="attachment://pix_qr.png")
        
        await interaction.channel.send(embed=embed_pix, file=file)
    else:
        await interaction.channel.send("❌ Não foi possível gerar o código PIX. Chame um atendente.")

class OrderDiscountModal(discord.ui.Modal, title="💰 Aplicar Desconto"):
    moedas_input = discord.ui.TextInput(
        label="Quantidade de Moedas",
        placeholder="Quanto de moedas usar? (1 Moeda = R$ 0.10 de desconto)",
        min_length=0,
        max_length=5,
        required=False
    )
    codigo_input = discord.ui.TextInput(
        label="Código de Parceiro(a)",
        placeholder="Ex: lor5%, Lobo5%...",
        min_length=0,
        max_length=20,
        required=False
    )

    def __init__(self, original_view):
        super().__init__()
        self.original_view = original_view

    async def on_submit(self, interaction: discord.Interaction):
        try:
            qtd_moedas = 0
            if self.moedas_input.value:
                try:
                    qtd_moedas = int(self.moedas_input.value)
                except ValueError:
                    await interaction.response.send_message("❌ Digite um número válido de moedas!", ephemeral=True)
                    return

            if qtd_moedas < 0:
                await interaction.response.send_message("❌ A quantidade deve ser maior ou igual a zero!", ephemeral=True)
                return

            usuarios = carregar_usuarios()
            u_id = str(interaction.user.id)
            saldo_moedas = usuarios.get(u_id, {}).get("moedas", 0)

            if qtd_moedas > 0 and saldo_moedas < qtd_moedas:
                await interaction.response.send_message(f"❌ Você não tem moedas suficientes! Saldo atual: **{saldo_moedas} Moedas**", ephemeral=True)
                return

            # Calcular novo valor
            valor_texto = self.original_view.valor_atual
            valor_limpo = valor_texto.replace('R$', '').strip()
            
            if ',' in valor_limpo and '.' in valor_limpo:
                valor_limpo = valor_limpo.replace('.', '').replace(',', '.')
            elif ',' in valor_limpo:
                valor_limpo = valor_limpo.replace(',', '.')

            if "consultar" in valor_texto.lower():
                await interaction.response.send_message("❌ Não é possível aplicar desconto automático em produtos sob consulta.", ephemeral=True)
                return

            match = re.search(r'[\d\.]+', valor_limpo)
            if not match:
                 await interaction.response.send_message("❌ Erro ao identificar o valor do produto.", ephemeral=True)
                 return
                 
            valor_num = float(match.group(0))
            
            desconto_total = 0.0
            logs_txt = []
            partner_code_used = self.codigo_input.value.strip() if self.codigo_input.value else None

            # REGRA: Ou um, ou outro
            if self.moedas_input.value and partner_code_used:
                await interaction.response.send_message("❌ Você só pode usar Moedas OU Código de Parceiro por vez!", ephemeral=True)
                return

            # 1. Moedas: LIMITE 10%
            if qtd_moedas > 0:
                desconto_moedas = float(qtd_moedas) * 0.10
                limite_moedas = valor_num * 0.10 # Limite de 10%
                
                if desconto_moedas > limite_moedas:
                    desconto_moedas = limite_moedas
                    qtd_moedas = int(desconto_moedas / 0.10)
                
                desconto_total += desconto_moedas
                logs_txt.append(f"✨ Moedas: - R$ {desconto_moedas:.2f} ({qtd_moedas} moedas)")
                usuarios[u_id]["moedas"] -= qtd_moedas
                self.original_view.moedas_usadas += qtd_moedas

            # 2. Código Parceiro ou Cupom Evento
            if partner_code_used:
                eventos = config.get('eventos', {})
                PARTNERS = config.get('parceiros', {
                    "lor5%": "669960132863721492",
                    "Lobo5%": "775105629396008990"
                })
                
                desconto_aplicado_parcial = 0
                tipo_log = ""

                # 2.1 Verificar Cupom de Evento
                if partner_code_used in eventos:
                    cupom_data = eventos[partner_code_used]
                    exp_str = cupom_data.get('expiracao')
                    if exp_str:
                        exp_dt = datetime.fromisoformat(exp_str)
                        if datetime.now() > exp_dt:
                            await interaction.response.send_message("❌ Este cupom de evento já expirou!", ephemeral=True)
                            return
                    
                    porcentagem = cupom_data.get('desconto', 5.0) / 100.0
                    desconto_aplicado_parcial = valor_num * porcentagem
                    logs_txt.append(f"🎉 Cupom `{partner_code_used}`: - R$ {desconto_aplicado_parcial:.2f}")
                    tipo_log = "Cupom de Evento"

                # 2.2 Verificar Parceiro Fixo
                elif partner_code_used in PARTNERS:
                    desconto_aplicado_parcial = valor_num * 0.05
                    logs_txt.append(f"🤝 Parceiro `{partner_code_used}`: - R$ {desconto_aplicado_parcial:.2f}")
                    tipo_log = "Código de Parceiro"
                    
                    # Salvar para comissão
                    partner_id = PARTNERS[partner_code_used]
                    comissao_valor = valor_num * 0.05
                    try:
                        current_topic = interaction.channel.topic or ""
                        partes_limpas = [p.strip() for p in current_topic.split("|") if "Parceiro:" not in p and "ComissaoP:" not in p and "VendaP:" not in p]
                        new_topic = " | ".join(partes_limpas + [f"Parceiro: {partner_id}", f"ComissaoP: {comissao_valor:.2f}", f"VendaP: {valor_num:.2f}"])
                        await interaction.channel.edit(topic=new_topic)
                    except Exception as e:
                        print(f"⚠️ Erro ao salvar parceiro no tópico: {e}")
                
                # 2.3 Verificar Códigos Especiais (Baseados em Cargo)
                else:
                    # Código Especial: Booster (7% desconto para Server Boosters)
                    if partner_code_used.lower() == "booster":
                        # Verificar se o usuário tem o cargo Server Booster
                        booster_role = discord.utils.get(interaction.guild.roles, name="Server Booster")
                        if not booster_role or booster_role not in interaction.user.roles:
                            await interaction.response.send_message("❌ Você precisa do cargo **@Server Booster** para usar este código!", ephemeral=True)
                            return
                        
                        # Aplicar 7% de desconto
                        desconto_aplicado_parcial = valor_num * 0.07
                        logs_txt.append(f"🚀 Booster `{partner_code_used}`: - R$ {desconto_aplicado_parcial:.2f}")
                        tipo_log = "Código Booster"
                    else:
                        await interaction.response.send_message("❌ Código de parceiro ou cupom inválido!", ephemeral=True)
                        return

                # Aplicar desconto ao total
                desconto_total += desconto_aplicado_parcial
                
                # Log para Admins
                log_channel_id = config.get('ticket_logs_loja_channel_id') or config.get('ticket_logs_channel_id')
                if log_channel_id:
                    log_channel = interaction.guild.get_channel(int(log_channel_id))
                    if log_channel:
                        embed_log = discord.Embed(
                            title=f"🎟️ {tipo_log} Usado",
                            description=f"O membro {interaction.user.mention} usou **{partner_code_used}**!",
                            color=discord.Color.blue(),
                            timestamp=datetime.now()
                        )
                        embed_log.add_field(name="💳 Produto", value=self.original_view.produto)
                        embed_log.add_field(name="💰 Valor Original", value=valor_texto)
                        embed_log.add_field(name="📉 Desconto", value=f"R$ {desconto_aplicado_parcial:.2f}")
                        embed_log.set_footer(text=f"ID Usuário: {interaction.user.id}")
                        await log_channel.send(embed=embed_log)

            if desconto_total == 0:
                await interaction.response.send_message("❌ Nenhum desconto foi aplicado.", ephemeral=True)
                return

            salvar_usuarios(usuarios)
            
            novo_valor = valor_num - desconto_total
            if novo_valor < 0: novo_valor = 0
            
            self.original_view.valor_atual = f"R$ {novo_valor:.2f}"

            # Atualizar Embed
            embed = interaction.message.embeds[0]
            embed.clear_fields()
            embed.add_field(name="🛍️ Produto/Serviço", value=f"**{self.original_view.produto}**", inline=False)
            embed.add_field(name="💲 Valor Tabela (Estimado)", value=f"~~{valor_texto}~~", inline=True)
            
            for log in logs_txt:
                name, val = log.split(": ", 1)
                embed.add_field(name=name, value=val, inline=True)
                
            embed.add_field(name="💰 Valor Total com Desconto", value=f"**{self.original_view.valor_atual}**", inline=False)
            embed.set_footer(text="⚠️ Regras de limites de desconto aplicadas.")
            embed.color = discord.Color.gold()
            
            # Desabilitar o botão de desconto após o uso
            for child in self.original_view.children:
                if isinstance(child, discord.ui.Button) and child.custom_id == "order_discount":
                    child.disabled = True
                    break

            await interaction.response.edit_message(embed=embed, view=self.original_view)
            await interaction.followup.send(f"✅ Desconto total de **R$ {desconto_total:.2f}** aplicado!", ephemeral=True)

        except Exception as e:
            if interaction.response.is_done():
                await interaction.followup.send(f"❌ Erro ao aplicar desconto: {e}", ephemeral=True)
            else:
                await interaction.response.send_message(f"❌ Erro ao aplicar desconto: {e}", ephemeral=True)

class OrderActionView(discord.ui.View):
    def __init__(self, produto, valor_inicial, game_id):
        super().__init__(timeout=None)
        self.produto = produto
        self.valor_atual = valor_inicial
        self.moedas_usadas = 0
        self.game_id = game_id

    @discord.ui.button(label="Comprar", style=discord.ButtonStyle.success, emoji="🛒", custom_id="order_buy")
    async def buy(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Desabilitar botões
        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(view=self)
        
        await trigger_pix_flow(interaction, self.valor_atual, self.produto, self.game_id)

    @discord.ui.button(label="Desconto", style=discord.ButtonStyle.primary, emoji="✨", custom_id="order_discount")
    async def discount(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(OrderDiscountModal(self))

    @discord.ui.button(label="Cancelar", style=discord.ButtonStyle.danger, emoji="❌", custom_id="order_cancel")
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Estornar moedas se tiver usado? 
        if self.moedas_usadas > 0:
            usuarios = carregar_usuarios()
            u_id = str(interaction.user.id)
            if u_id in usuarios:
                usuarios[u_id]["moedas"] = usuarios[u_id].get("moedas", 0) + self.moedas_usadas
                salvar_usuarios(usuarios)
        
        await interaction.response.edit_message(content="❌ Pedido cancelado.", embed=None, view=None)
        await asyncio.sleep(3)
        try: await interaction.message.delete()
        except: pass

# --- VIEW PARA O BOTÃO NA TABELA DE PREÇOS ---
class TicketLojaPedidoView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🛒 Fazer Pedido", style=discord.ButtonStyle.success, custom_id="btn_fazer_pedido", emoji="🛒")
    async def fazer_pedido(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(TicketLojaModal())

# --- MODAL TICKET LOJA (Agora chamado pelo botão da tabela) ---

class TicketLojaModal(discord.ui.Modal, title="🛒 Fazer Pedido"):
    produto = discord.ui.TextInput(
        label="O que deseja comprar?",
        placeholder="Ex: VIP Ouro, Skin de Arma...",
        style=discord.TextStyle.short,
        required=True,
        max_length=100
    )

    async def on_submit(self, interaction: discord.Interaction):
        # Tentar identificar o preço automaticamente
        produto_nome = self.produto.value.lower().strip()
        valor_estimado = "Consultar Atendente"
        
        # Busca parcial
        for item, preco in TABELA_PRECOS.items():
            if item in produto_nome:
                valor_estimado = f"R$ {preco:.2f}"
                break
        
        # Enviar o pedido no canal
        embed = discord.Embed(
            title="📝 Novo Pedido Registrado",
            description=f"O membro {interaction.user.mention} deseja comprar:",
            color=discord.Color.green()
        )
        embed.add_field(name="🛍️ Produto/Serviço", value=f"**{self.produto.value}**", inline=True)
        embed.add_field(name="🆔 ID do Game", value=f"**{interaction.user.id}**", inline=True)
        embed.add_field(name="💲 Valor Tabela (Estimado)", value=f"**{valor_estimado}**", inline=False)
        
        view = OrderActionView(self.produto.value, valor_estimado, str(interaction.user.id))
        await interaction.response.send_message(embed=embed, view=view)

# --- VIEW DO PAINEL DE TICKETS ---
class TicketPanelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🛒 Abrir Ticket Loja", style=discord.ButtonStyle.green, custom_id="ticket_loja", emoji="🛒")
    async def ticket_loja(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Abre o ticket diretamente
        await criar_ticket(interaction, 'ticket_loja')

    @discord.ui.button(label="🛠️ Abrir Ticket Suporte", style=discord.ButtonStyle.blurple, custom_id="ticket_suporte", emoji="🛠️")
    async def ticket_suporte(self, interaction: discord.Interaction, button: discord.ui.Button):
        await criar_ticket(interaction, 'ticket_suporte')

@bot.tree.command(name="painel_tickets", description="Criar painel de tickets")
async def painel_tickets(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ Você precisa ser administrador para usar este comando!", ephemeral=True)
        return
    
    embed = discord.Embed(
        title="🎫 Sistema de Tickets",
        description="Escolha o tipo de ticket que você precisa:",
        color=discord.Color.blue()
    )
    
    embed.add_field(
        name="🛒 Ticket Loja",
        value="Para questões relacionadas a compras, produtos ou serviços",
        inline=False
    )
    
    embed.add_field(
        name="🛠️ Ticket Suporte",
        value="Para suporte técnico, dúvidas ou problemas",
        inline=False
    )
    
    embed.set_footer(text="Clique nos botões abaixo para abrir um ticket")
    
    view = TicketPanelView()
    
    await interaction.response.send_message(embed=embed, view=view)
    print(f'✅ Painel de tickets criado por {interaction.user.name}')

# Sistema de Tickets
# Lógica interna do sistema de tickets
async def _criar_ticket_logic(interaction: discord.Interaction, tipo: str, produto: str = None):
    """Cria um novo ticket (Lógica Interna)"""
    global config
    
    # Verificar configurações
    # Verificar configurações e criar categoria se não existir
    categoria_id = None
    if tipo == 'ticket_loja':
        if 'ticket_category_loja_id' in config:
            categoria_id = config['ticket_category_loja_id']
    else:
        if 'ticket_category_suporte_id' in config:
            categoria_id = config['ticket_category_suporte_id']
    
    categoria = None
    if categoria_id:
        categoria = bot.get_channel(categoria_id)
    
    # Se categoria não existe, criar automaticamente
    if not categoria:
        try:
            nome_cat = "🛒 Atendimento Loja" if tipo == 'ticket_loja' else "🛠️ Suporte Técnico"
            categoria = await interaction.guild.create_category(nome_cat)
            
            # Salvar nova configuração
            if tipo == 'ticket_loja':
                config['ticket_category_loja_id'] = categoria.id
            else:
                config['ticket_category_suporte_id'] = categoria.id
                
            # Salvar no JSON
            try:
                if os.path.exists(CONFIG_FILE):
                    with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                        saved_config = json.load(f)
                else:
                    saved_config = {}
                
                saved_config['ticket_category_loja_id' if tipo == 'ticket_loja' else 'ticket_category_suporte_id'] = str(categoria.id)
                
                with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                    json.dump(saved_config, f, indent=4)
                
                print(f'✅ Categoria {nome_cat} criada automaticamente')
            except Exception as e:
                print(f'❌ Erro ao salvar config de ticket: {e}')
        except Exception as e:
            await interaction.response.send_message(f"❌ Erro ao criar categoria de tickets: {e}", ephemeral=True)
            return
    
    # Nome do canal (01-username)
    nome_tipo = "loja" if tipo == 'ticket_loja' else "suporte"
    index = len(categoria.channels) + 1
    nome_canal = f"{index:02d}-{interaction.user.name}"
    
    # Verificar se o usuário já tem um ticket (termina com o nome dele)
    for channel in categoria.channels:
        if channel.name.endswith(interaction.user.name.lower().replace(" ", "-")):
            await interaction.response.send_message("❌ Você já tem um ticket aberto!", ephemeral=True)
            return
    
        # Criar canal do ticket
    try:
        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            interaction.guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_channels=True)
        }
        
        # Adicionar permissão para o cargo Atendente
        role_atendente = discord.utils.get(interaction.guild.roles, name="🛡️Atendente")
        if role_atendente:
            overwrites[role_atendente] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
        
        canal_ticket = await categoria.create_text_channel(
            name=nome_canal,
            overwrites=overwrites,
            topic=f"Ticket de {nome_tipo} para {interaction.user.name} | ID: {interaction.user.id}"
        )
        
        # Se tiver produto definido (Ticket Loja via Modal), adiciona ao tópico
        if produto:
             await canal_ticket.edit(topic=f"{canal_ticket.topic} | Interesse: {produto}")
        
        # Embed do ticket
        mention_atendente = role_atendente.mention if role_atendente else "@🛡️Atendente"

        embed = discord.Embed(
            title=f"🎫 Ticket de {nome_tipo.capitalize()}",
            description=f"Olá {interaction.user.mention}!\nAgradecemos por entrar em contato. O {mention_atendente} irá atendê-lo em breve.\n\n**Por favor, descreva sua solicitação abaixo:**",
            color=discord.Color.green() if tipo == 'ticket_loja' else discord.Color.blue()
        )
        
        embed.add_field(name="👤 Criado por", value=interaction.user.mention, inline=True)
        embed.add_field(name="📅 Criado em", value=f"<t:{int(datetime.now().timestamp())}:f>", inline=True)
        embed.add_field(name="🆔 ID do Game", value=f"**{interaction.user.id}**", inline=False)
        
        if produto:
             embed.add_field(name="🛍️ Interesse de Compra", value=f"**{produto}**", inline=False)
        
        embed.set_footer(text="Clique no botão abaixo para encerrar o atendimento", icon_url=bot.user.avatar.url if bot.user.avatar else None)
        embed.set_thumbnail(url=interaction.user.avatar.url if interaction.user.avatar else interaction.user.default_avatar.url)
        
        # Botão para fechar ticket (Apenas Staff)
        view = TicketFecharView()
        
        await canal_ticket.send(embed=embed, view=view)

        # SE FOR TICKET DE LOJA, MANDAR A TABELA DE PREÇOS AUTOMATICAMENTE
        if tipo == 'ticket_loja':
            embed_precos = discord.Embed(
                title="🐦‍🔥 TABELA DE PREÇOS - STAFF 🐦‍🔥",
                description="Confira abaixo os valores dos nossos produtos e serviços.",
                color=discord.Color.orange(),
                timestamp=datetime.now()
            )

            vips_text = (
                "🥉 **Vip bronze** - `R$ 10,00 / mês`\n"
                "🥈 **Vip prata** - `R$ 20,00 / mês`\n"
                "🥇 **Vip ouro** - `R$ 30,00 / mês`\n"
                "⚙️ **Vip Scripts** - `R$ 50,00 / mês`"
            )
            embed_precos.add_field(name="👑 SISTEMA DE VIPS", value=vips_text, inline=False)

            embed_precos.set_footer(text="STAFF • Tabela de Preços Atualizada", icon_url=bot.user.avatar.url if bot.user.avatar else None)
            embed_precos.set_thumbnail(url=interaction.guild.icon.url if interaction.guild.icon else None)
            
            # Adicionar botão "Fazer Pedido" à tabela
            view_pedido = TicketLojaPedidoView()
            await canal_ticket.send(embed=embed_precos, view=view_pedido)

        await interaction.followup.send(f"✅ Ticket criado em {canal_ticket.mention}!", ephemeral=True)
        
        # --- AUTOMAÇÃO TICKET LOJA (DELAYED) ---
        # Removido daqui para ser disparado pelo botão "Fazer Pedido" ou mensagem

        print(f'✅ Ticket {tipo} criado para {interaction.user.name}')
        
    except Exception as e:
        # Se der erro, tenta enviar via followup se já tiver deferido, senão send_message
        try:
            await interaction.followup.send(f"❌ Erro ao criar ticket: {e}", ephemeral=True)
        except:
             try: await interaction.response.send_message(f"❌ Erro ao criar ticket: {e}", ephemeral=True)
             except: pass
        print(f'❌ Erro ao criar ticket: {e}')

# Wrapper para controle de concorrência
async def criar_ticket(interaction: discord.Interaction, tipo: str, produto: str = None):
    if interaction.user.id in tickets_em_criacao:
        if not interaction.response.is_done():
            await interaction.response.send_message("❌ Aguarde, seu ticket já está sendo criado!", ephemeral=True)
        return
        
    tickets_em_criacao.add(interaction.user.id)
    try:
        await _criar_ticket_logic(interaction, tipo, produto)
    finally:
        tickets_em_criacao.discard(interaction.user.id)



# --- INTEGRAÇÃO PUSHINPAY ---
async def pushinpay_create_pix(valor_reais):
    """Cria um PIX na PushinPay e retorna o código e o ID da transação"""
    token = config.get('pushinpay_token')
    if not token:
        return None, None
        
    url = "https://api.pushinpay.com.br/api/pix/cashIn"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    
    # PushinPay usa centavos para o valor
    valor_centavos = int(float(valor_reais) * 100)
    
    payload = {
        "value": valor_centavos,
        "webhook_url": "" # Opcional, se tiver um servidor pra receber
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        data = response.json()
        
        if response.status_code == 201 or 'qr_code' in data:
            return data['qr_code'], data['id']
        else:
            print(f"❌ Erro PushinPay (Create): {data}")
            return None, None
    except Exception as e:
        print(f"❌ Erro PushinPay Request (Create): {e}")
        return None, None

async def pushinpay_check_status(transaction_id):
    """Verifica o status de uma transação na PushinPay"""
    token = config.get('pushinpay_token')
    if not token:
        return "error"
        
    url = f"https://api.pushinpay.com.br/api/transactions/{transaction_id}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json"
    }
    
    try:
        response = requests.get(url, headers=headers)
        data = response.json()
        
        if response.status_code == 200:
            return data.get('status') # created, paid, expired
        else:
            print(f"❌ Erro PushinPay (Status): {data}")
            return "error"
    except Exception as e:
        print(f"❌ Erro PushinPay Request (Status): {e}")
        return "error"

@bot.tree.command(name="configurar_pix", description="Configurar o código PIX copia e cola padrão do servidor")
@app_commands.describe(codigo="O código PIX copia e cola padrão")
async def configurar_pix(interaction: discord.Interaction, codigo: str):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ Você precisa ser administrador para usar este comando!", ephemeral=True)
        return
    
    global config
    config['pix_default_code'] = codigo
    
    # Salvar no JSON
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                saved_config = json.load(f)
        else:
            saved_config = {}
        
        saved_config['pix_default_code'] = codigo
        
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(saved_config, f, indent=4)
            
        print(f"✅ PIX padrão configurado por {interaction.user.name}")
    except Exception as e:
        print(f"❌ Erro ao salvar config de PIX: {e}")

    embed = discord.Embed(
        title="✅ PIX Configurado",
        description="O código PIX padrão foi salvo com sucesso!",
        color=discord.Color.green()
    )
    embed.add_field(name="📝 Código", value=f"```\n{codigo[:1000]}\n```")
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="pix", description="Gerar o QR Code PIX padrão do servidor")
async def pix(interaction: discord.Interaction):
    """Gera o QR Code do PIX padrão"""
    try:
        # Verificar permissões (Apenas Admin ou Atendente)
        role_atendente = discord.utils.get(interaction.guild.roles, name="🛡️Atendente")
        is_atendente = role_atendente in interaction.user.roles if role_atendente else False
        is_admin = interaction.user.guild_permissions.administrator
        
        if not (is_admin or is_atendente):
            await interaction.response.send_message("❌ Apenas administradores ou atendentes podem usar o comando de PIX!", ephemeral=True)
            return

        # Usar o código padrão da config
        valor_pix = config.get('pix_default_code')
        
        if not valor_pix:
            await interaction.response.send_message("❌ Nenhum código PIX padrão está configurado!\nUse `/configurar_pix` para definir um.", ephemeral=True)
            return

        # Deferir para dar tempo de gerar a imagem
        await interaction.response.defer()

        # Gerar o QR Code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(valor_pix)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        
        # Salvar em buffer
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)
        
        file = discord.File(buffer, filename="pix_qr.png")
        
        embed = discord.Embed(
            title="💸 QR Code PIX",
            description="Use o seu aplicativo do banco para escanear o código abaixo.\n\n**Código Copia e Cola:**",
            color=discord.Color.green(),
            timestamp=datetime.now()
        )
        
        # Adicionar o código em um bloco de código para facilitar a cópia
        embed.add_field(name="\u200b", value=f"```\n{valor_pix}\n```", inline=False)
        
        embed.set_image(url="attachment://pix_qr.png")
        embed.set_footer(text=f"Solicitado por {interaction.user.name}", icon_url=interaction.user.avatar.url if interaction.user.avatar else None)
        
        await interaction.followup.send(embed=embed, file=file)
        print(f"✅ QR Code PIX gerado por {interaction.user.name}")
        
    except Exception as e:
        # Se for followup usa send no error
        try:
            await interaction.followup.send(f"❌ Erro ao gerar QR Code: {e}")
        except:
            if not interaction.response.is_done():
                await interaction.response.send_message(f"❌ Erro ao gerar QR Code: {e}", ephemeral=True)
        print(f"❌ Erro ao gerar QR Code PIX: {e}")


@bot.tree.command(name="configurar_logs_convite", description="Configurar canal para logs de quem convidou novos membros")
async def configurar_logs_convite(interaction: discord.Interaction, canal: discord.TextChannel):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ Você precisa ser administrador para usar este comando!", ephemeral=True)
        return
    
    global config
    config['invite_logs_channel_id'] = canal.id
    
    # Salvar no JSON
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                saved_config = json.load(f)
        else:
            saved_config = {}
        
        saved_config['invite_logs_channel_id'] = str(canal.id)
        
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(saved_config, f, indent=4)
    except Exception as e:
        print(f"❌ Erro ao salvar config de logs de convite: {e}")

    embed = discord.Embed(
        title="✅ Configuração Salva",
        description=f"Canal de logs de convites definido para {canal.mention}",
        color=discord.Color.green()
    )
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="configurar_call", description="Configurar o canal 'Master' para criar salas automáticas")
@app_commands.describe(canal="O canal de voz que os membros devem entrar para criar uma sala")
async def configurar_call(interaction: discord.Interaction, canal: discord.VoiceChannel):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ Você precisa ser administrador para usar este comando!", ephemeral=True)
        return
    
    global config
    config['create_call_channel_id'] = canal.id
    
    # Salvar no JSON
    try:
        if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    saved_config = json.load(f)
        else:
            saved_config = {}
        
        saved_config['create_call_channel_id'] = str(canal.id)
        
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(saved_config, f, indent=4)
            
        print(f"✅ Canal de criação de call configurado por {interaction.user.name}")
    except Exception as e:
        print(f"❌ Erro ao salvar config de call: {e}")

    embed = discord.Embed(
        title="✅ Canal de Call Configurado",
        description=f"O canal {canal.mention} foi definido como o criador de salas automáticas!",
        color=discord.Color.green()
    )
    await interaction.response.send_message(embed=embed)


class TicketFecharView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🔒 Fechar Ticket", style=discord.ButtonStyle.red, custom_id="btn_fechar_ticket")
    async def fechar_ticket_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Verificar permissões (Apenas Admin ou Atendente)
        role_atendente = discord.utils.get(interaction.guild.roles, name="🛡️Atendente")
        is_atendente = role_atendente in interaction.user.roles if role_atendente else False
        is_admin = interaction.user.guild_permissions.administrator
        
        if not (is_admin or is_atendente):
            await interaction.response.send_message("❌ Apenas administradores ou atendentes podem fechar tickets!", ephemeral=True)
            return

        embed = discord.Embed(
            title="⚠️ Confirmação",
            description="Você tem certeza que deseja fechar este ticket? O canal será deletado e os registros salvos.",
            color=discord.Color.yellow()
        )
        
        view = discord.ui.View()
        btn_ok = discord.ui.Button(label="OK", style=discord.ButtonStyle.success, custom_id="confirmar_fechar", emoji="✅")
        btn_cancel = discord.ui.Button(label="Cancelar", style=discord.ButtonStyle.danger, custom_id="cancelar_fechar", emoji="❌")
        
        view.add_item(btn_ok)
        view.add_item(btn_cancel)
        
        await interaction.response.send_message(embed=embed, view=view)

# Comando /fechar_ticket removido - Substituído por botão



# --- FUNÇÃO DE INTEGRAÇÃO COM API DE PAGAMENTO (PLACEHOLDER) ---
async def check_payment_api(txid=None):
    """
    Função base para integrar APIs de pagamento reais (Mercado Pago, EFI, Stripe, etc).
    
    Como usar:
    1. Instale a biblioteca da SDK: pip install mercadopago (exemplo)
    2. Importe e configure com suas credenciais (Access Token, Client ID, Client Secret)
    3. Use o endpoint de verificação de status do pagamento (GET /v1/payments/{id})
    """
    
    # EXEMPLO TE ÓRICO (MERCADO PAGO):
    '''
    import mercadopago
    sdk = mercadopago.SDK("SEU_ACCESS_TOKEN")
    
    payment_info = sdk.payment().get(txid)
    status = payment_info["response"]["status"]
    
    if status == "approved":
        return True
    return False
    '''
    
    # Simulação para este bot:
    await asyncio.sleep(1) # Simula tempo de requisição
    return True # Retorna sempre aprovado na simulação


# Comandos para enviar mensagens como bot
@bot.tree.command(name="enviar_mensagem", description="Envia uma mensagem como bot (apenas administradores)")
@app_commands.describe(
    canal="Canal onde a mensagem será enviada",
    mensagem="Texto da mensagem",
    embed="Se deve enviar como embed (padrão: False)",
    titulo_embed="Título do embed (opcional)",
    cor_embed="Cor do embed em hexadecimal (ex: #FF0000)",
    imagem_url="URL da imagem para embed (opcional)"
)
async def enviar_mensagem(
    interaction: discord.Interaction,
    canal: discord.TextChannel,
    mensagem: str,
    embed: bool = False,
    titulo_embed: typing.Optional[str] = None,
    cor_embed: typing.Optional[str] = None,
    imagem_url: typing.Optional[str] = None
):
    """Envia uma mensagem através do bot"""
    
    # Verificar permissões
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message(
            "❌ Você precisa ser administrador para usar este comando!",
            ephemeral=True
        )
        return
    
    try:
        # Se for para enviar como embed
        if embed:
            # Configurar cor do embed
            if cor_embed:
                try:
                    # Converter hexadecimal para inteiro
                    cor = int(cor_embed.replace("#", ""), 16)
                except:
                    cor = discord.Color.blue()
            else:
                cor = discord.Color.blue()
            
            # Criar embed
            embed_msg = discord.Embed(
                description=mensagem,
                color=cor
            )
            
            # Adicionar título se fornecido
            if titulo_embed:
                embed_msg.title = titulo_embed
            
            # Adicionar imagem se fornecida
            if imagem_url:
                embed_msg.set_image(url=imagem_url)
            
            # Enviar embed
            await canal.send(embed=embed_msg)
            
        else:
            # Enviar mensagem normal
            await canal.send(mensagem)
        
        # Confirmar envio
        embed_resposta = discord.Embed(
            title="✅ Mensagem Enviada",
            description=f"Mensagem enviada com sucesso em {canal.mention}!",
            color=discord.Color.green()
        )
        
        embed_resposta.add_field(name="📝 Conteúdo", value=mensagem[:500] + ("..." if len(mensagem) > 500 else ""), inline=False)
        embed_resposta.add_field(name="📤 Canal", value=canal.mention, inline=True)
        embed_resposta.add_field(name="🔧 Tipo", value="Embed" if embed else "Texto Simples", inline=True)
        
        await interaction.response.send_message(embed=embed_resposta, ephemeral=True)
        print(f'✅ Mensagem enviada por {interaction.user.name} em #{canal.name}')
        
    except Exception as e:
        await interaction.response.send_message(
            f"❌ Erro ao enviar mensagem: {e}",
            ephemeral=True
        )
        print(f'❌ Erro ao enviar mensagem: {e}')

# Comando para enviar mensagem direta (DM)
@bot.tree.command(name="enviar_dm", description="Envia uma mensagem direta para um usuário (apenas administradores)")
@app_commands.describe(
    usuario="Usuário para enviar a mensagem",
    mensagem="Texto da mensagem"
)
async def enviar_dm(
    interaction: discord.Interaction,
    usuario: discord.Member,
    mensagem: str
):
    """Envia uma mensagem direta para um usuário"""
    
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message(
            "❌ Você precisa ser administrador para usar este comando!",
            ephemeral=True
        )
        return
    
    try:
        # Enviar mensagem direta
        await usuario.send(mensagem)
        
        # Confirmar apenas para o administrador
        embed_resposta = discord.Embed(
            title="✅ DM Enviada",
            description=f"Mensagem enviada para {usuario.mention}",
            color=discord.Color.green()
        )
        
        embed_resposta.add_field(name="👤 Usuário", value=f"{usuario.name}#{usuario.discriminator}", inline=True)
        embed_resposta.add_field(name="📝 Conteúdo", value=mensagem[:100] + ("..." if len(mensagem) > 100 else ""), inline=False)
        
        await interaction.response.send_message(embed=embed_resposta, ephemeral=True)
        print(f'✅ DM enviada por {interaction.user.name} para {usuario.name}')
        
    except discord.Forbidden:
        await interaction.response.send_message(
            f"❌ Não foi possível enviar DM para {usuario.mention}. O usuário pode ter DMs desativadas.",
            ephemeral=True
        )
    except Exception as e:
        await interaction.response.send_message(
            f"❌ Erro ao enviar DM: {e}",
            ephemeral=True
        )
        print(f'❌ Erro ao enviar DM: {e}')

# Comandos com prefixo !
@bot.command(name="limpar", aliases=["clear"])
@commands.has_permissions(manage_messages=True)
async def limpar(ctx, amount: int = 10):
    """Limpa mensagens do chat"""
    try:
        await ctx.channel.purge(limit=amount + 1)
        msg = await ctx.send(f"🧹 {amount} mensagens excluídas!", delete_after=3)
    except Exception as e:
        await ctx.send(f"❌ Erro ao limpar mensagens: {e}", delete_after=5)

@bot.command(name="teste_entrada")
@commands.has_permissions(administrator=True)
async def teste_entrada(ctx):
    """Simula a entrada de um membro (Teste)"""
    try:
        await on_member_join(ctx.author)
        await ctx.send("✅ Evento de entrada simulado!", delete_after=3)
    except Exception as e:
        await ctx.send(f"❌ Erro ao simular entrada: {e}")

@bot.command(name="teste_saida")
@commands.has_permissions(administrator=True)
async def teste_saida(ctx):
    """Simula a saída de um membro (Teste)"""
    try:
        await on_member_remove(ctx.author)
        await ctx.send("✅ Evento de saída simulado!", delete_after=3)
    except Exception as e:
        await ctx.send(f"❌ Erro ao simular saída: {e}")

@bot.command(name="teste_booster")
@commands.has_permissions(administrator=True)
async def teste_booster(ctx):
    """Simula o impulsionamento do servidor (Teste)"""
    global config
    if 'booster_channel_id' in config and config['booster_channel_id']:
        channel = bot.get_channel(config['booster_channel_id'])
        if channel:
            try:
                # Gerar imagem (GIF)
                buffer = await gerar_imagem_perfil(ctx.author, "BOOSTER", "#ff00ff")
                file = discord.File(buffer, filename="booster.gif")
                
                embed = discord.Embed(
                    title="🚀 Novo Booster! (TESTE)",
                    description=f"Obrigado {ctx.author.mention} por impulsionar o servidor! 🎉",
                    color=discord.Color.purple(),
                    timestamp=datetime.now()
                )
                
                embed.set_thumbnail(url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
                embed.set_image(url="attachment://booster.gif")
                
                await channel.send(embed=embed, file=file)
                await ctx.send(f"✅ Evento de booster simulado em {channel.mention}!", delete_after=3)
            except Exception as e:
                await ctx.send(f"❌ Erro ao simular booster: {e}")
        else:
            await ctx.send("❌ Canal de booster não encontrado!")
    else:
        await ctx.send("❌ Canal de booster não configurado!")

@bot.command(name="ban")
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason=None):
    """Banir um membro"""
    try:
        await member.ban(reason=reason)
        embed = discord.Embed(
            title="🔨 Banimento",
            description=f"**{member.name}** foi banido com sucesso!",
            color=discord.Color.red()
        )
        embed.add_field(name="Motivo", value=reason or "Não especificado")
        embed.set_footer(text=f"Banido por {ctx.author.name}")
        await ctx.send(embed=embed)
    except Exception as e:
        await ctx.send(f"❌ Erro ao banir membro: {e}")

@bot.command(name="kick")
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason=None):
    """Expulsar um membro"""
    try:
        await member.kick(reason=reason)
        embed = discord.Embed(
            title="🦵 Expulsão",
            description=f"**{member.name}** foi expulso do servidor!",
            color=discord.Color.orange()
        )
        embed.add_field(name="Motivo", value=reason or "Não especificado")
        embed.set_footer(text=f"Expulso por {ctx.author.name}")
        await ctx.send(embed=embed)
    except Exception as e:
        await ctx.send(f"❌ Erro ao expulsar membro: {e}")

@bot.command(name="mute")
@commands.has_permissions(moderate_members=True)
async def mute(ctx, member: discord.Member, tempo: int, unidade: str = "m", *, reason=None):
    """Silenciar um membro (Ex: !mute @usuario 10 m)"""
    try:
        if unidade == "m":
            duration = timedelta(minutes=tempo)
        elif unidade == "h":
            duration = timedelta(hours=tempo)
        elif unidade == "d":
            duration = timedelta(days=tempo)
        else:
             await ctx.send("❌ Unidade inválida! Use 'm' (minutos), 'h' (horas) ou 'd' (dias).")
             return

        await member.timeout(discord.utils.utcnow() + duration, reason=reason)
        
        embed = discord.Embed(
            title="🔇 Silenciado",
            description=f"**{member.name}** foi silenciado por {tempo}{unidade}.",
            color=discord.Color.gray()
        )
        embed.add_field(name="Motivo", value=reason or "Não especificado")
        embed.set_footer(text=f"Silenciado por {ctx.author.name}")
        await ctx.send(embed=embed)
    except Exception as e:
        await ctx.send(f"❌ Erro ao silenciar membro: {e}")

@bot.command(name="unmute")
@commands.has_permissions(moderate_members=True)
async def unmute(ctx, member: discord.Member):
    """Remover silenciamento de um membro"""
    try:
        await member.timeout(None)
        await ctx.send(f"🔊 **{member.name}** teve o silenciamento removido!")
    except Exception as e:
        await ctx.send(f"❌ Erro ao remover silenciamento: {e}")

@bot.command(name="unban")
@commands.has_permissions(ban_members=True)
async def unban(ctx, id_usuario: int):
    """Desbanir um usuário pelo ID"""
    try:
        user = await bot.fetch_user(id_usuario)
        await ctx.guild.unban(user)
        await ctx.send(f"✅ **{user.name}** foi desbanido com sucesso!")
    except Exception as e:
        await ctx.send(f"❌ Erro ao desbanir (Verifique se o ID está correto): {e}")

@bot.command(name="lock")
@commands.has_permissions(manage_channels=True)
async def lock(ctx):
    """Trancar o canal atual"""
    try:
        await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=False)
        await ctx.send("🔒 Canal trancado com sucesso!")
    except Exception as e:
        await ctx.send(f"❌ Erro ao trancar canal: {e}")

@bot.command(name="unlock")
@commands.has_permissions(manage_channels=True)
async def unlock(ctx):
    """Destrancar o canal atual"""
    try:
        await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=True)
        await ctx.send("🔓 Canal destrancado com sucesso!")
    except Exception as e:
        await ctx.send(f"❌ Erro ao destrancar canal: {e}")

@bot.command(name="say")
@commands.has_permissions(administrator=True)
async def say(ctx, *, mensagem):
    """Fazer o bot falar algo"""
    try:
        await ctx.message.delete()
        await ctx.send(mensagem)
    except:
        pass

@bot.command(name="dm")
@commands.has_permissions(administrator=True)
async def dm_prefix(ctx, usuario: discord.Member, *, mensagem):
    """Enviar DM para um usuário (!dm @usuario mensagem)"""
    try:
        await usuario.send(mensagem)
        await ctx.send(f"✅ DM enviada para {usuario.name}!")
    except:
        await ctx.send(f"❌ Não foi possível enviar DM para {usuario.name} (Privado bloqueado?)")

@bot.command(name="ajuda_adm")
@commands.has_permissions(manage_messages=True)
async def ajuda_adm(ctx):
    """Lista todos os comandos de administração"""
    embed = discord.Embed(
        title="🛡️ Painel de Comandos Administrativos",
        description="Lista de comandos disponíveis para a staff do STAFF.",
        color=discord.Color.dark_red()
    )
    
    embed.add_field(name="🚔 Moderação", value="`!ban @user [motivo]` - Banir\n`!unban <id>` - Desbanir\n`!kick @user [motivo]` - Expulsar\n`!mute @user <tempo><unidade>` - Silenciar (Ex: 10m)\n`!unmute @user` - Remover silenciamento", inline=False)
    embed.add_field(name="🔧 Utilidades", value="`!clear <qtd>` - Limpar chat\n`!lock` - Trancar canal\n`!unlock` - Destrancar canal\n`!say <msg>` - Bot fala\n`!dm @user <msg>` - Enviar DM", inline=False)
    embed.add_field(name="🧪 Testes", value="`!teste_entrada` - Testar boas-vindas\n`!teste_saida` - Testar saída\n`!teste_booster` - Testar booster\n`!sync` - Sincronizar slash commands", inline=False)
    
    embed.set_thumbnail(url=bot.user.avatar.url if bot.user.avatar else None)
    embed.set_footer(text=f"Solicitado por {ctx.author.name}")
    
    await ctx.send(embed=embed)
@bot.tree.command(name="ajuda", description="Mostra todos os comandos disponíveis")
async def ajuda(interaction: discord.Interaction):
    embed = discord.Embed(
        title="📚 Lista de Comandos - STAFF",
        description="Aqui estão todos os comandos que você pode usar:",
        color=discord.Color.gold(),
        timestamp=datetime.now()
    )
    
    # Comandos de Membros
    embed.add_field(
        name="👤 **Membros**", 
        value=(
            "`/botinfo` - Informações sobre o bot\n"
            "`/perfil` - Ver seu perfil e XP\n"
            "`/set_id` - Definir seu ID do jogo\n"
            "`/sorteio` - Participar de sorteios (quando houver)\n"
            "`/rank` - Ver ranking de XP do servidor\n"
            "`/ajuda` - Ver esta lista"
        ), 
        inline=False
    )
    
    # Comandos Admins (Só mostra se for admin)
    if interaction.user.guild_permissions.administrator:
        embed.add_field(
            name="👮 **Admin & Staff**", 
            value=(
                "`/painel_videos` - Criar painel de envio de vídeos\n"
                "`/painel_sugestoes` - Criar painel de sugestões\n"
                "`/painel_tickets` - Criar painel de tickets\n"
                "`/painel_perfil` - Criar painel de ver perfil\n"
                "`/verificacao` - Criar botão de verificação\n"
                "`/regras` - Enviar regras do servidor\n"
                "`/adicionar_xp` - Adicionar XP a um membro\n"
                "`/remover_xp` - Remover XP de um membro\n"
                "`/trocar_xp` - Trocar seu XP por Moedas (1k XP = 1 Moeda)\n"
                "`/configurar_xp_cargo` - Configurar cargos de nível\n"
                "`/listar_xp_cargos` - Ver cargos de XP\n"
                "`!sync` - Sincronizar comandos (Prefixo !)\n"
                "`!limpar <qtd>` - Limpar mensagens (Prefixo !)\n"
                "`!kick / !ban` - Punições (Prefixo !)"
            ), 
            inline=False
        )

    # Minigames
    embed.add_field(
        name="🎮 **Minigames**",
        value=(
            "`/dado` - Rolar um dado (1-6)\n"
            "`/moeda` - Cara ou Coroa\n"
            "`/ppt` - Pedra, Papel ou Tesoura"
        ),
        inline=False
    )
        
    embed.set_thumbnail(url=bot.user.avatar.url if bot.user.avatar else None)
    embed.set_footer(text="STAFF • Digite / para ver mais detalhes")
    
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.command(name="sync")
@commands.has_permissions(administrator=True)
async def sync_commands(ctx):
    """Sincroniza os comandos e FORÇA a aparição imediata no servidor"""
    try:
        msg = await ctx.send("⌛ Sincronizando comandos e limpando cache...")
        
        # 1. Copia os comandos globais para este servidor específico
        # Isso faz com que eles apareçam NA HORA sem ter que esperar o Discord
        bot.tree.copy_global_to(guild=ctx.guild)
        
        # 2. Sincroniza o servidor
        synced_guild = await bot.tree.sync(guild=ctx.guild)
        
        # 3. Sincroniza globalmente também (para outros servidores, leva mais tempo)
        synced_global = await bot.tree.sync()
        
        await msg.edit(content=(
            f"✅ **Sincronização Concluída com Sucesso!**\n\n"
            f"🔹 **Neste Servidor:** {len(synced_guild)} comandos ativos agora.\n"
            f"🌍 **Globalmente:** {len(synced_global)} comandos em atualização.\n\n"
            f"💡 **Dica:** Se ainda não aparecer, reinicie seu Discord (Ctrl+R no PC)."
        ))
    except Exception as e:
        await ctx.send(f"❌ Erro ao sincronizar: {e}")

@bot.command(name="idbot")
async def get_bot_id(ctx):
    """Comando para obter o ID do bot"""
    embed = discord.Embed(
        title="🤖 Informações do Bot",
        color=discord.Color.blue()
    )
    
    embed.add_field(name="ID do Bot", value=f"`{bot.user.id}`", inline=False)
    embed.add_field(name="Nome", value=bot.user.name, inline=True)
    embed.add_field(name="Discriminador", value=bot.user.discriminator, inline=True)
    embed.add_field(name="Convite", value=f"[Clique aqui](https://discord.com/oauth2/authorize?client_id={bot.user.id}&scope=bot&permissions=8)", inline=False)
    
    await ctx.send(embed=embed)

# Comando !fecharticket removido - Substituído por botão


@bot.command(name="config")
async def mostrar_config(ctx):
    """Mostrar configuração atual do bot"""
    if not ctx.author.guild_permissions.administrator:
        await ctx.send("❌ Você precisa ser administrador para usar este comando!")
        return
    
    embed = discord.Embed(
        title="⚙️ Configurações do Bot",
        color=discord.Color.gold()
    )
    
    if 'welcome_channel_id' in config:
        canal = bot.get_channel(config['welcome_channel_id'])
        embed.add_field(name="📥 Boas-vindas", value=canal.mention if canal else "Não configurado", inline=True)
    
    if 'leave_channel_id' in config:
        canal = bot.get_channel(config['leave_channel_id'])
        embed.add_field(name="📤 Saída", value=canal.mention if canal else "Não configurado", inline=True)
    
    if 'booster_channel_id' in config:
        canal = bot.get_channel(config['booster_channel_id'])
        embed.add_field(name="✨ Booster", value=canal.mention if canal else "Não configurado", inline=True)
    
    if 'member_role_id' in config:
        cargo = ctx.guild.get_role(config['member_role_id'])
        embed.add_field(name="👤 Cargo Membro", value=cargo.mention if cargo else "Não configurado", inline=True)
    
    if 'ticket_category_loja_id' in config:
        categoria = bot.get_channel(config['ticket_category_loja_id'])
        embed.add_field(name="🛒 Tickets Loja", value=categoria.name if categoria else "Não configurado", inline=True)
    
    if 'ticket_category_suporte_id' in config:
        categoria = bot.get_channel(config['ticket_category_suporte_id'])
        embed.add_field(name="🛠️ Tickets Suporte", value=categoria.name if categoria else "Não configurado", inline=True)
    
    await ctx.send(embed=embed)

@bot.command(name="ping")
async def ping(ctx):
    """Comando de ping para testar latência"""
    latency = round(bot.latency * 1000)
    
    embed = discord.Embed(
        title="🏓 Pong!",
        description=f"Latência: `{latency}ms`",
        color=discord.Color.green()
    )
    
    await ctx.send(embed=embed)

# Comando com prefixo para enviar mensagem
@bot.command(name="enviar")
@commands.has_permissions(administrator=True)
async def enviar_prefix(ctx, canal: discord.TextChannel = None, *, mensagem: str):
    """Comando com prefixo para enviar mensagem como bot"""
    
    # Se não especificar canal, usar o atual
    if canal is None:
        canal = ctx.channel
    
    try:
        # Enviar mensagem
        await canal.send(mensagem)
        
        # Confirmar
        embed = discord.Embed(
            title="✅ Mensagem Enviada",
            description=f"Mensagem enviada em {canal.mention}",
            color=discord.Color.green()
        )
        
        await ctx.send(embed=embed)
        print(f'✅ Mensagem enviada por {ctx.author.name} em #{canal.name}')
        
    except Exception as e:
        await ctx.send(f"❌ Erro ao enviar mensagem: {e}")
        print(f'❌ Erro ao enviar mensagem: {e}')

# Tratamento de erro para o comando com prefixo
@enviar_prefix.error
async def enviar_prefix_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ Você precisa ser administrador para usar este comando!")
    elif isinstance(error, commands.ChannelNotFound):
        await ctx.send("❌ Canal não encontrado!")
    else:
        await ctx.send(f"❌ Erro: {error}")

# Handler para botões de confirmação
@bot.event
async def on_interaction(interaction: discord.Interaction):
    try:
        if interaction.type == discord.InteractionType.component:
            custom_id = interaction.data.get('custom_id')
            
            # Tickets
            if custom_id in ['ticket_loja', 'ticket_suporte']:
                await criar_ticket(interaction, custom_id)
            
            # Fechar ticket (Antigo Sistema - Fallback)
            elif custom_id.startswith('fechar_'):
                # Ignorar se for o novo botão (que é btn_fechar_ticket)
                if custom_id == "btn_fechar_ticket":
                    return

                # Responder imediatamente pra não dar erro de interação
                await interaction.response.defer()
                
                try:
                    channel_id = int(custom_id.split('_')[1])
                except ValueError:
                    return # Ignorar IDs mal formatados
                
                channel = bot.get_channel(channel_id)
                
                # Verificar se é um canal de ticket pelas categorias
                cat_loja = config.get('ticket_category_loja_id')
                cat_suporte = config.get('ticket_category_suporte_id')
                
                if channel and channel.category_id in [cat_loja, cat_suporte]:
                    await salvar_e_fechar_ticket_helper(channel, interaction.user)
            
            # Confirmação de fechamento
            elif custom_id == 'confirmar_fechar':
                await interaction.response.edit_message(content="📂 **Fechando ticket...**", view=None, embed=None)
                await salvar_e_fechar_ticket_helper(interaction.channel, interaction.user)
            
            elif custom_id == 'cancelar_fechar':
                try:
                    await interaction.message.delete()
                except:
                    pass
                await interaction.response.send_message("❌ Fechamento cancelado.", ephemeral=True)
    
    except Exception as e:
        print(f"❌ Erro no handler de interação: {e}")

# View para Aprovação de Vídeos
class VideoApprovalView(discord.ui.View):
    def __init__(self, video_link, author_id):
        super().__init__(timeout=None)
        self.video_link = video_link
        self.author_id = author_id

    @discord.ui.button(label="Aprovar", style=discord.ButtonStyle.success, emoji="✅", custom_id="video_aprovar")
    async def aprovar(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Verificar se quem clicou é admin (Opcional, mas recomendado)
        if not interaction.user.guild_permissions.manage_messages:
            await interaction.response.send_message("❌ Apenas staff pode aprovar!", ephemeral=True)
            return

        # Tentar pegar o canal de vídeos públicos
        if 'videos_public_channel_id' in config:
            public_channel = interaction.guild.get_channel(config['videos_public_channel_id'])
            if public_channel:
                await public_channel.send(f"🎥 **Novo vídeo postado por** <@{self.author_id}>\n{self.video_link}")
                await interaction.message.edit(content=f"✅ **Vídeo Aprovado por {interaction.user.mention}**", view=None)
                await interaction.response.send_message("✅ Vídeo postado com sucesso!", ephemeral=True)
                
                # Avisar o dono do vídeo (se possível)
                try:
                    user = interaction.guild.get_member(self.author_id)
                    if user:
                        await user.send(f"✅ Seu vídeo foi aprovado e postado em {public_channel.mention}!")
                except:
                    pass
            else:
                await interaction.response.send_message("❌ Canal público de vídeos não encontrado!", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Canal público de vídeos não configurado!", ephemeral=True)

    @discord.ui.button(label="Reprovar", style=discord.ButtonStyle.danger, emoji="❌", custom_id="video_reprovar")
    async def reprovar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.manage_messages:
            await interaction.response.send_message("❌ Apenas staff pode reprovar!", ephemeral=True)
            return
            
        await interaction.message.edit(content=f"❌ **Vídeo Reprovado por {interaction.user.mention}**", view=None)
        await interaction.response.send_message("❌ Vídeo reprovado.", ephemeral=True)
        
        # Avisar o dono (se possível)
        try:
            user = interaction.guild.get_member(self.author_id)
            if user:
                await user.send("❌ Seu vídeo foi reprovado pela staff.")
        except:
            pass

@bot.command(name="setcvideos")
@commands.has_permissions(administrator=True)
async def setcvideos(ctx, canal_aprovacao: discord.TextChannel, canal_postagem: discord.TextChannel):
    """Configurar sistema de vídeos (!setcvideos #adm-videos #videos)"""
    global config
    config['videos_approval_channel_id'] = canal_aprovacao.id
    config['videos_public_channel_id'] = canal_postagem.id
    
    # Salvar no JSON
    try:
        data = {}
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
        
        data['videos_approval_channel_id'] = canal_aprovacao.id
        data['videos_public_channel_id'] = canal_postagem.id
        
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)
            
        await ctx.send(f"✅ Sistema de vídeos configurado!\n📋 Aprovação: {canal_aprovacao.mention}\n📢 Postagem: {canal_postagem.mention}")
    except Exception as e:
        await ctx.send(f"❌ Erro ao salvar configuração: {e}")

@setcvideos.error
async def setcvideos_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArguments):
        await ctx.send("❌ Uso incorreto! Você precisa marcar os dois canais.\nDigite: `!setcvideos <#canal_aprovacao> <#canal_postagem>`")
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ Você precisa ser administrador para usar este comando!")
    else:
        await ctx.send(f"❌ Ocorreu um erro: {error}")



# --- Novo Sistema de Vídeos (Botão + Modal) ---
class VideoHandlerView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Enviar Vídeo", style=discord.ButtonStyle.primary, emoji="📹", custom_id="video_enviar_btn")
    async def enviar_video_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(VideoModal())

class VideoModal(discord.ui.Modal, title="📹 Enviar Vídeo"):
    link_video = discord.ui.TextInput(
        label="Link do Vídeo",
        placeholder="https://youtube.com/watch?v=...",
        required=True
    )

    async def on_submit(self, interaction: discord.Interaction):
        link = self.link_video.value
        
        # Validação básica
        if "http" not in link:
            await interaction.response.send_message("❌ Link inválido! Certifique-se de incluir http/https.", ephemeral=True)
            return

        if 'videos_approval_channel_id' not in config:
            await interaction.response.send_message("❌ Sistema de vídeos não configurado! Avise a staff.", ephemeral=True)
            return
            
        approval_channel = bot.get_channel(config['videos_approval_channel_id'])
        if not approval_channel:
            await interaction.response.send_message("❌ Canal de aprovação não encontrado!", ephemeral=True)
            return

        # Criar View e Embed para Staff
        # Usamos VideoApprovalView que já existe (precisa garantir que ela aceite custom_id dinâmico ou persistente)
        # Nota: A VideoApprovalView original usa botões sem persistência (sem custom_id fixo na classe, mas sim no decorator)
        # Vamos instanciar normalmente.
        view = VideoApprovalView(link, interaction.user.id)
        
        embed = discord.Embed(
            title="📹 Novo Vídeo para Aprovação",
            description=f"**Autor:** {interaction.user.mention}\n**Link:** {link}",
            color=discord.Color.blue(),
            timestamp=datetime.now()
        )
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        embed.set_footer(text=f"ID: {interaction.user.id}")

        try:
            await approval_channel.send(content=f"Recebido de {interaction.user.mention}", embed=embed, view=view)
            await interaction.response.send_message("✅ Vídeo enviado para aprovação com sucesso!", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Erro ao enviar solicitação: {e}", ephemeral=True)

@bot.tree.command(name="painel_videos", description="Criar painel de envio de vídeos")
async def painel_videos(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ Você precisa ser administrador!", ephemeral=True)
        return
    
    # Preparar imagem local
    file = None
    image_url = None
    
    image_path = os.path.join(BASE_DIR, "banner_videos.png")
    if os.path.exists(image_path):
        file = discord.File(image_path, filename="banner_videos.png")
        image_url = "attachment://banner_videos.png"
    else:
        # Fallback se não tiver imagem
        image_url = "https://i.imgur.com/example.png" 

    embed = discord.Embed(
        title="🎬 Divulgação de Vídeos",
        description="Quer divulgar seu vídeo no servidor?\n\nClique no botão abaixo **Enviar Vídeo** e cole o link do seu conteúdo!\n\n⚠️ **Regras:**\n• Apenas vídeos de MTA/GTA\n• Sem conteúdo ofensivo\n• Aguarde a aprovação da staff",
        color=discord.Color.red()
    )
    
    if image_url:
        embed.set_image(url=image_url)
    
    embed.set_footer(text="STAFF • Sistema de Divulgação")
    
    await interaction.response.send_message("✅ Painel enviado!", ephemeral=True)
    
    if file:
        await interaction.channel.send(embed=embed, view=VideoHandlerView(), file=file)
    else:
        await interaction.channel.send(embed=embed, view=VideoHandlerView())

@bot.command(name="setevento")
@commands.has_permissions(administrator=True)
async def setevento(ctx, canal: discord.TextChannel = None):
    """Configurar o canal de eventos Automático"""
    if canal is None:
        canal = ctx.channel
        
    global config
    config['event_channel_id'] = canal.id
    
    # Salvar no JSON
    try:
        data = {}
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
        
        data['event_channel_id'] = canal.id
        
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)
            
        await ctx.send(f"✅ Canal de eventos configurado para: {canal.mention}")
    except Exception as e:
        await ctx.send(f"❌ Erro ao salvar configuração: {e}")

# --- Sistema de Sugestões e Erros ---
class VotacaoView(discord.ui.View):
    def __init__(self, author_id):
        super().__init__(timeout=None)
        self.author_id = author_id
        self.votos_positivos = set()
        self.votos_negativos = set()

    @discord.ui.button(label="0", style=discord.ButtonStyle.success, emoji="👍", custom_id="voto_positivo")
    async def voto_positivo(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id = interaction.user.id
        # Remover voto negativo se existir
        if user_id in self.votos_negativos:
            self.votos_negativos.remove(user_id)
        # Toggle voto positivo
        if user_id in self.votos_positivos:
            self.votos_positivos.remove(user_id)
        else:
            self.votos_positivos.add(user_id)
        
        # Atualizar botões
        self.children[0].label = str(len(self.votos_positivos))
        self.children[1].label = str(len(self.votos_negativos))
        await interaction.message.edit(view=self)
        await interaction.response.defer()

    @discord.ui.button(label="0", style=discord.ButtonStyle.danger, emoji="👎", custom_id="voto_negativo")
    async def voto_negativo(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id = interaction.user.id
        # Remover voto positivo se existir
        if user_id in self.votos_positivos:
            self.votos_positivos.remove(user_id)
        # Toggle voto negativo
        if user_id in self.votos_negativos:
            self.votos_negativos.remove(user_id)
        else:
            self.votos_negativos.add(user_id)
        
        # Atualizar botões
        self.children[0].label = str(len(self.votos_positivos))
        self.children[1].label = str(len(self.votos_negativos))
        await interaction.message.edit(view=self)
        await interaction.response.defer()

    @discord.ui.button(label="Aprovar", style=discord.ButtonStyle.success, emoji="✅", custom_id="aprovar_sugestao")
    async def aprovar_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Apenas admin pode aprovar
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Apenas administradores podem aprovar!", ephemeral=True)
            return
        
        # Desabilitar todos os botões e mudar para Aprovada
        for child in self.children:
            child.disabled = True
        self.children[2].label = "Aprovada"
        self.children[2].emoji = "✅"
        self.children[2].style = discord.ButtonStyle.success
        self.children[3].label = "—"
        self.children[3].style = discord.ButtonStyle.secondary
        
        await interaction.message.edit(view=self)
        await interaction.response.send_message("✅ Sugestão aprovada!", ephemeral=True)
        
        # Enviar DM para o membro
        try:
            membro = interaction.guild.get_member(self.author_id)
            if membro:
                # Pegar o embed original
                embed_original = interaction.message.embeds[0] if interaction.message.embeds else None
                
                dm_embed = discord.Embed(
                    title="✅ Sua Sugestão foi Aprovada!",
                    description=f"Sua sugestão no servidor **{interaction.guild.name}** foi aprovada pela staff!",
                    color=discord.Color.green(),
                    timestamp=datetime.now()
                )
                
                if embed_original:
                    dm_embed.add_field(name="📝 Sua Sugestão:", value=embed_original.description or "Sem conteúdo", inline=False)
                
                dm_embed.set_footer(text=f"Aprovada por {interaction.user.name}")
                await membro.send(embed=dm_embed)
        except Exception as e:
            print(f"❌ Erro ao enviar DM: {e}")

    @discord.ui.button(label="Reprovar", style=discord.ButtonStyle.danger, emoji="❌", custom_id="reprovar_sugestao")
    async def reprovar_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Apenas admin pode reprovar
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Apenas administradores podem reprovar!", ephemeral=True)
            return
        
        # Desabilitar todos os botões e mudar para Reprovada
        for child in self.children:
            child.disabled = True
        self.children[2].label = "—"
        self.children[2].style = discord.ButtonStyle.secondary
        self.children[3].label = "Reprovada"
        self.children[3].emoji = "❌"
        self.children[3].style = discord.ButtonStyle.danger
        
        await interaction.message.edit(view=self)
        await interaction.response.send_message("❌ Sugestão reprovada!", ephemeral=True)
        
        # Enviar DM para o membro
        try:
            membro = interaction.guild.get_member(self.author_id)
            if membro:
                # Pegar o embed original
                embed_original = interaction.message.embeds[0] if interaction.message.embeds else None
                
                dm_embed = discord.Embed(
                    title="❌ Sua Sugestão foi Reprovada",
                    description=f"Infelizmente sua sugestão no servidor **{interaction.guild.name}** foi reprovada pela staff.",
                    color=discord.Color.red(),
                    timestamp=datetime.now()
                )
                
                if embed_original:
                    dm_embed.add_field(name="📝 Sua Sugestão:", value=embed_original.description or "Sem conteúdo", inline=False)
                
                dm_embed.set_footer(text=f"Reprovada por {interaction.user.name}")
                await membro.send(embed=dm_embed)
        except Exception as e:
            print(f"❌ Erro ao enviar DM: {e}")

class IdeiaModal(discord.ui.Modal, title="💡 Enviar Sua Ideia"):
    ideia = discord.ui.TextInput(
        label="Descreva sua ideia/sugestão",
        style=discord.TextStyle.paragraph,
        placeholder="Digite sua sugestão aqui...",
        min_length=10,
        max_length=1000,
        required=True
    )

    async def on_submit(self, interaction: discord.Interaction):
        if 'sugestao_channel_id' not in config:
            await interaction.response.send_message("❌ Canal de sugestões não configurado!", ephemeral=True)
            return
        
        canal = bot.get_channel(config['sugestao_channel_id'])
        if not canal:
            await interaction.response.send_message("❌ Canal de sugestões não encontrado!", ephemeral=True)
            return
        
        # Buscar ID Game do usuário
        usuarios = carregar_usuarios()
        user_id = str(interaction.user.id)
        id_game = usuarios.get(user_id, {}).get("codigo", "Não definido")
        
        # Embed estilo da imagem com ID Game
        embed = discord.Embed(
            description=f"**{interaction.user.name}**\n`🆔 {id_game}`\n>>> {self.ideia.value}",
            color=0x5865F2,
            timestamp=datetime.now()
        )
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        
        # Enviar com View de votação
        view = VotacaoView(interaction.user.id)
        msg = await canal.send(embed=embed, view=view)
        
        await interaction.response.send_message("✅ Sua sugestão foi enviada com sucesso!", ephemeral=True)

class ErroModal(discord.ui.Modal, title="🐛 Reportar Erro do Servidor"):
    erro = discord.ui.TextInput(
        label="Descreva o erro encontrado",
        style=discord.TextStyle.paragraph,
        placeholder="Descreva o erro/bug que você encontrou...",
        min_length=10,
        max_length=1000,
        required=True
    )

    async def on_submit(self, interaction: discord.Interaction):
        if 'erro_channel_id' not in config:
            await interaction.response.send_message("❌ Canal de erros não configurado!", ephemeral=True)
            return
        
        canal = bot.get_channel(config['erro_channel_id'])
        if not canal:
            await interaction.response.send_message("❌ Canal de erros não encontrado!", ephemeral=True)
            return
        
        # Buscar ID Game do usuário
        usuarios = carregar_usuarios()
        user_id = str(interaction.user.id)
        id_game = usuarios.get(user_id, {}).get("codigo", "Não definido")
        
        # Embed estilo da imagem com ID Game
        embed = discord.Embed(
            description=f"**{interaction.user.name}**\n`🆔 {id_game}`\n>>> {self.erro.value}",
            color=0xED4245,
            timestamp=datetime.now()
        )
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        
        # Enviar com View de votação para ERROS
        view = ErroVotacaoView(interaction.user.id)
        msg = await canal.send(embed=embed, view=view)
        
        await interaction.response.send_message("✅ Seu report de erro foi enviado com sucesso!", ephemeral=True)

# View de Votação para ERROS (com textos específicos)
class ErroVotacaoView(discord.ui.View):
    def __init__(self, author_id):
        super().__init__(timeout=None)
        self.author_id = author_id
        self.votos_positivos = set()
        self.votos_negativos = set()

    @discord.ui.button(label="0", style=discord.ButtonStyle.success, emoji="👍", custom_id="erro_voto_positivo")
    async def voto_positivo(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id = interaction.user.id
        if user_id in self.votos_negativos:
            self.votos_negativos.remove(user_id)
        if user_id in self.votos_positivos:
            self.votos_positivos.remove(user_id)
        else:
            self.votos_positivos.add(user_id)
        
        self.children[0].label = str(len(self.votos_positivos))
        self.children[1].label = str(len(self.votos_negativos))
        await interaction.message.edit(view=self)
        await interaction.response.defer()

    @discord.ui.button(label="0", style=discord.ButtonStyle.danger, emoji="👎", custom_id="erro_voto_negativo")
    async def voto_negativo(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id = interaction.user.id
        if user_id in self.votos_positivos:
            self.votos_positivos.remove(user_id)
        if user_id in self.votos_negativos:
            self.votos_negativos.remove(user_id)
        else:
            self.votos_negativos.add(user_id)
        
        self.children[0].label = str(len(self.votos_positivos))
        self.children[1].label = str(len(self.votos_negativos))
        await interaction.message.edit(view=self)
        await interaction.response.defer()

    @discord.ui.button(label="Corrigido", style=discord.ButtonStyle.success, emoji="✅", custom_id="erro_corrigido")
    async def corrigido_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Apenas administradores podem marcar como corrigido!", ephemeral=True)
            return
        
        for child in self.children:
            child.disabled = True
        self.children[2].label = "Corrigido"
        self.children[2].emoji = "✅"
        self.children[2].style = discord.ButtonStyle.success
        self.children[3].label = "—"
        self.children[3].style = discord.ButtonStyle.secondary
        
        await interaction.message.edit(view=self)
        await interaction.response.send_message("✅ Erro marcado como corrigido!", ephemeral=True)
        
        # Enviar DM para o membro
        try:
            membro = interaction.guild.get_member(self.author_id)
            if membro:
                embed_original = interaction.message.embeds[0] if interaction.message.embeds else None
                
                dm_embed = discord.Embed(
                    title="✅ Seu Report de Erro foi Resolvido!",
                    description=f"O erro que você reportou no servidor **{interaction.guild.name}** foi corrigido pela equipe!",
                    color=discord.Color.green(),
                    timestamp=datetime.now()
                )
                
                if embed_original:
                    dm_embed.add_field(name="🐛 Seu Report:", value=embed_original.description or "Sem conteúdo", inline=False)
                
                dm_embed.set_footer(text=f"Corrigido por {interaction.user.name}")
                await membro.send(embed=dm_embed)
        except Exception as e:
            print(f"❌ Erro ao enviar DM: {e}")

    @discord.ui.button(label="Ignorado", style=discord.ButtonStyle.danger, emoji="❌", custom_id="erro_ignorado")
    async def ignorado_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Apenas administradores podem ignorar!", ephemeral=True)
            return
        
        for child in self.children:
            child.disabled = True
        self.children[2].label = "—"
        self.children[2].style = discord.ButtonStyle.secondary
        self.children[3].label = "Ignorado"
        self.children[3].emoji = "❌"
        self.children[3].style = discord.ButtonStyle.danger
        
        await interaction.message.edit(view=self)
        await interaction.response.send_message("❌ Erro ignorado!", ephemeral=True)
        
        # Enviar DM para o membro
        try:
            membro = interaction.guild.get_member(self.author_id)
            if membro:
                embed_original = interaction.message.embeds[0] if interaction.message.embeds else None
                
                dm_embed = discord.Embed(
                    title="❌ Seu erro não foi encontrado",
                    description=f"O erro que você reportou no servidor **{interaction.guild.name}** não foi encontrado pela equipe.",
                    color=discord.Color.red(),
                    timestamp=datetime.now()
                )
                
                if embed_original:
                    dm_embed.add_field(name="🐛 Seu Report:", value=embed_original.description or "Sem conteúdo", inline=False)
                
                dm_embed.set_footer(text=f"Ignorado por {interaction.user.name}")
                await membro.send(embed=dm_embed)
        except Exception as e:
            print(f"❌ Erro ao enviar DM: {e}")

class SugestaoView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Sua Ideia", style=discord.ButtonStyle.primary, emoji="💡", custom_id="sugestao_ideia")
    async def btn_ideia(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(IdeiaModal())

    @discord.ui.button(label="Erro SV", style=discord.ButtonStyle.danger, emoji="🐛", custom_id="sugestao_erro")
    async def btn_erro(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ErroModal())

@bot.tree.command(name="configurar_sugestoes", description="Configurar canais de sugestões e erros")
@app_commands.describe(
    canal_sugestoes="Canal onde as sugestões serão enviadas",
    canal_erros="Canal onde os erros serão enviados"
)
async def configurar_sugestoes(interaction: discord.Interaction, canal_sugestoes: discord.TextChannel, canal_erros: discord.TextChannel):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ Você precisa ser administrador!", ephemeral=True)
        return
    
    global config
    config['sugestao_channel_id'] = canal_sugestoes.id
    config['erro_channel_id'] = canal_erros.id
    
    # Salvar no JSON
    try:
        data = {}
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
        
        data['sugestao_channel_id'] = canal_sugestoes.id
        data['erro_channel_id'] = canal_erros.id
        
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)
        
        await interaction.response.send_message(f"✅ Configurado!\n💡 Sugestões: {canal_sugestoes.mention}\n🐛 Erros: {canal_erros.mention}", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"❌ Erro ao salvar: {e}", ephemeral=True)

# --- Sistema de Configuração de Parceria (YouTube Monitor) ---
class ConfigParceria(app_commands.Group, name="config_parceria", description="Configurações do sistema de monitoramento automático de YouTube"):
    @app_commands.command(name="adicionar_youtube", description="Adiciona um canal do YouTube para monitoramento automático")
    @app_commands.describe(link_ou_id="Link do canal ou ID do canal do YouTube (Suporta @Handle)")
    async def parceria_add_yt(self, interaction: discord.Interaction, link_ou_id: str):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Você precisa ser administrador!", ephemeral=True)
            return
        
        # Tentar extrair o ID do canal se for um link ou handle
        channel_id = link_ou_id.strip()
        
        # Se for um link completo com @, /c/, /user/ ou apenas o @
        if "@" in channel_id or "/c/" in channel_id or "/user/" in channel_id or not channel_id.startswith("UC"):
            if not interaction.response.is_done():
                await interaction.response.defer(ephemeral=True)
            
            try:
                # Normalizar link
                url = channel_id
                if not url.startswith("http"):
                    if url.startswith("@"):
                        url = f"https://www.youtube.com/{url}"
                    else:
                        url = f"https://www.youtube.com/channel/{url}" if url.startswith("UC") else f"https://www.youtube.com/@{url.replace('@','')}"
                
                headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"}
                response = requests.get(url, headers=headers, timeout=10)
                
                if response.status_code == 200:
                    # Tentar encontrar o UC... no HTML
                    # Padrão 1: "channelId":"UC..."
                    match = re.search(r'channelId":"(UC[a-zA-Z0-9_-]+)"', response.text)
                    if not match:
                        # Padrão 2: meta tag identifier
                        match = re.search(r'<meta itemprop="identifier" content="(UC[a-zA-Z0-9_-]+)">', response.text)
                    if not match:
                        # Padrão 3: links de browse
                        match = re.search(r'youtube\.com/channel/(UC[a-zA-Z0-9_-]+)"', response.text)
                    
                    if match:
                        channel_id = match.group(1)
                    else:
                        await interaction.followup.send("❌ Não consegui encontrar o ID do canal nesse link. Certifique-se de que é um canal válido (ex: @STAFFmtaoficial).", ephemeral=True)
                        return
                else:
                    # Se falhou, mas já parece ser um ID (UC...), ignoramos o erro e tentamos usar como ID
                    if not channel_id.startswith("UC"):
                        await interaction.followup.send(f"❌ Erro ao acessar o link: Código {response.status_code}. Tente usar o ID UC... direto.", ephemeral=True)
                        return
            except Exception as e:
                if not channel_id.startswith("UC"):
                    await interaction.followup.send(f"❌ Erro ao processar o link: {e}", ephemeral=True)
                    return

        # Agora temos (ou achamos que temos) o channel_id UC...
        if not channel_id.startswith("UC"):
             msg = "⚠️ Não foi possível identificar o ID do canal. Use o link direto `/channel/UC...` ou o ID UC..."
             if interaction.response.is_done(): await interaction.followup.send(msg, ephemeral=True)
             else: await interaction.response.send_message(msg, ephemeral=True)
             return

        global config
        if "partner_youtube_channels" not in config:
            config["partner_youtube_channels"] = {}
        
        if channel_id in config["partner_youtube_channels"]:
            msg = f"❌ O canal `{channel_id}` já está na lista!"
            if interaction.response.is_done():
                await interaction.followup.send(msg, ephemeral=True)
            else:
                await interaction.response.send_message(msg, ephemeral=True)
            return
        
        # Inicializar com o vídeo mais recente atual para não postar vídeos antigos
        last_id = None
        try:
            url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                v_ids = re.findall(r'<yt:videoId>(.*?)</yt:videoId>', response.text)
                if v_ids:
                    last_id = v_ids[0]
        except:
            pass

        config["partner_youtube_channels"][channel_id] = {
            "last_video_id": last_id,
            "adicionado_em": datetime.now().isoformat()
        }
        salvar_config(config)
        msg = f"✅ Canal do YouTube `{channel_id}` adicionado com sucesso!"
        if interaction.response.is_done():
            await interaction.followup.send(msg, ephemeral=True)
        else:
            await interaction.response.send_message(msg, ephemeral=True)

    @app_commands.command(name="remover_youtube", description="Remove um canal do YouTube do monitoramento")
    @app_commands.describe(channel_id="O ID do canal do YouTube (UC...)")
    async def parceria_remove_yt(self, interaction: discord.Interaction, channel_id: str):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Você precisa ser administrador!", ephemeral=True)
            return
        
        global config
        if "partner_youtube_channels" not in config or channel_id not in config["partner_youtube_channels"]:
            await interaction.response.send_message(f"❌ O canal `{channel_id}` não está na lista!", ephemeral=True)
            return
        
        del config["partner_youtube_channels"][channel_id]
        salvar_config(config)
        await interaction.response.send_message(f"✅ Canal `{channel_id}` removido da lista!", ephemeral=True)

    @app_commands.command(name="set_destino", description="Define o canal para onde os vídeos serão postados")
    @app_commands.describe(canal="O canal de destino no Discord")
    async def parceria_set_destino(self, interaction: discord.Interaction, canal: discord.TextChannel):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Você precisa ser administrador!", ephemeral=True)
            return
        
        global config
        config["partner_forward_target_id"] = canal.id
        salvar_config(config)
        await interaction.response.send_message(f"✅ Canal de destino definido para: {canal.mention}", ephemeral=True)

    @app_commands.command(name="listar", description="Lista os canais do YouTube monitorados")
    async def parceria_listar(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Você precisa ser administrador!", ephemeral=True)
            return
        
        global config
        yt_channels = config.get("partner_youtube_channels", {})
        target_id = config.get("partner_forward_target_id")
        
        desc = "**📺 Canais do YouTube Monitorados:**\n"
        if yt_channels:
            for cid in yt_channels.keys():
                desc += f"• `{cid}` (https://www.youtube.com/channel/{cid})\n"
        else:
            desc += "• Nenhum canal configurado.\n"
        
        desc += f"\n**🎯 Canal de Destino no Discord:**\n"
        if target_id:
            tc = bot.get_channel(int(target_id))
            desc += f"• {tc.mention if tc else f'ID: {target_id}'}"
        else:
            desc += "• Não configurado."
            
        embed = discord.Embed(title="📋 Monitoramento de Parceiros", description=desc, color=discord.Color.red())
        await interaction.response.send_message(embed=embed, ephemeral=True)

bot.tree.add_command(ConfigParceria())

# View para o Sorteio e Roleta Coletiva
class SorteioView(discord.ui.View):
    def __init__(self, timeout=None):
        super().__init__(timeout=timeout)
        self.participantes = set()

    @discord.ui.button(label="Participar", style=discord.ButtonStyle.success, emoji="🎟️", custom_id="sorteio_join")
    async def join(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id in self.participantes:
            self.participantes.remove(interaction.user.id)
            await interaction.response.send_message("❌ Você saiu do sorteio!", ephemeral=True)
        else:
            self.participantes.add(interaction.user.id)
            await interaction.response.send_message("✅ Você entrou no sorteio! Boa sorte!", ephemeral=True)

@bot.tree.command(name="painel_sugestoes", description="Enviar painel de sugestões e erros")
async def painel_sugestoes(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ Você precisa ser administrador!", ephemeral=True)
        return
    
    embed = discord.Embed(
        title="📋 Central de Sugestões",
        description="**Ajude-nos a melhorar o servidor!**\n\n"
                    "💡 **Sua Ideia** - Envie sugestões para melhorias\n"
                    "🐛 **Erro SV** - Reporte bugs e problemas do servidor\n\n"
                    "Clique em um dos botões abaixo para enviar!",
        color=discord.Color.purple()
    )
    embed.set_footer(text="STAFF • Sistema de Sugestões")
    
    await interaction.response.send_message("✅ Painel enviado!", ephemeral=True)
    await interaction.channel.send(embed=embed, view=SugestaoView())

# View para o Sorteio
class SorteioView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None) # Não expira enquanto o bot estiver on
        self.participantes = set() # Usar set para evitar duplicatas

    @discord.ui.button(label="Participar", style=discord.ButtonStyle.success, emoji="🎉", custom_id="sorteio_participar")
    async def participar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id in self.participantes:
            self.participantes.remove(interaction.user.id)
            await interaction.response.send_message("❌ Você saiu do sorteio!", ephemeral=True)
        else:
            self.participantes.add(interaction.user.id)
            await interaction.response.send_message("✅ Você entrou no sorteio! Boa sorte!", ephemeral=True)
        
        # Atualizar contador no botão (Opcional, mas legal)
        button.label = f"Participar ({len(self.participantes)})"
        await interaction.message.edit(view=self)

# --- Comando Slash para Sorteio (/sorteioxp) ---
@bot.tree.command(name="sorteioxp", description="Iniciar um sorteio com prêmio de XP ou itens")
@app_commands.describe(
    tempo="Duração do sorteio (ex: 10s, 5m, 1h, 1d)",
    premio="Prêmio do sorteio",
    xp_premio="Quantidade de XP para o ganhador (opcional, padrão: 100)"
)
async def sorteioxp(interaction: discord.Interaction, tempo: str, premio: str, xp_premio: int = 100):
    """Comando slash para realizar sorteios com XP"""
    
    # Verificar permissões
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ Você precisa ser administrador para usar este comando!", ephemeral=True)
        return
    
    # Definir canal do sorteio
    target_channel = interaction.channel
    if 'event_channel_id' in config:
        found_channel = bot.get_channel(config['event_channel_id'])
        if found_channel:
            target_channel = found_channel
    
    # Converter tempo
    try:
        unidade = tempo[-1].lower()
        valor = int(tempo[:-1])
        segundos = 0
        
        if unidade == 's':
            segundos = valor
        elif unidade == 'm':
            segundos = valor * 60
        elif unidade == 'h':
            segundos = valor * 3600
        elif unidade == 'd':
            segundos = valor * 86400
        else:
            await interaction.response.send_message("❌ Use s, m, h ou d para o tempo (Ex: 10m, 1h, 2d).", ephemeral=True)
            return
    except ValueError:
        await interaction.response.send_message("❌ Formato de tempo inválido! Use: 10s, 5m, 1h, 1d", ephemeral=True)
        return

    # Data de término para o timestamp
    termino = datetime.now() + timedelta(seconds=segundos)
    timestamp = int(termino.timestamp())

    embed = discord.Embed(
        title="🎉 Sorteio Iniciado!",
        description=f"**Prêmio:** {premio}\n\n**Tempo:** {tempo}\n**Termina:** <t:{timestamp}:R>\n\nClique no botão abaixo para participar!",
        color=discord.Color.purple()
    )
    embed.set_footer(text=f"Iniciado por {interaction.user.name}")
    
    # Criar a View
    view = SorteioView()
    
    # Responder a interação
    if target_channel == interaction.channel:
        await interaction.response.send_message(embed=embed, view=view)
        mensagem = await interaction.original_response()
    else:
        await interaction.response.send_message(f"✅ Sorteio iniciado em {target_channel.mention}!", ephemeral=True)
        mensagem = await target_channel.send(embed=embed, view=view)

    # Esperar o tempo
    await asyncio.sleep(segundos)

    # Desabilitar botão
    view.children[0].disabled = True
    await mensagem.edit(view=view)

    # Escolher ganhador
    users = list(view.participantes)

    if len(users) > 0:
        vencedor_id = random.choice(users)
        
        # Dar XP ao ganhador automaticamente (com limite)
        usuarios = carregar_usuarios()
        user_id_str = str(vencedor_id)
        if user_id_str not in usuarios:
            usuarios[user_id_str] = {"xp": 0, "level": 0}
            
        nivel_atual = usuarios[user_id_str].get("level", 0)
        
        msg_xp = f"(+{xp_premio} XP)"
        
        if nivel_atual >= 100:
            msg_xp = "(XP Máximo Atingido!)"
        else:
            novo_xp = usuarios[user_id_str].get("xp", 0) + xp_premio
            if novo_xp >= 50000: novo_xp = 50000
            
            usuarios[user_id_str]["xp"] = novo_xp
            novo_nivel = novo_xp // 500
            usuarios[user_id_str]["level"] = novo_nivel
            salvar_usuarios(usuarios)
            
            # Atualizar cargos do ganhador
            try:
                guild = mensagem.guild
                member = guild.get_member(vencedor_id)
                if member:
                     await gerenciar_cargos_nivel(member, novo_nivel)
            except: pass
            
        embed_fim = discord.Embed(
            title="🎉 Sorteio Encerrado!",
            description=f"**Prêmio:** {premio}\n**Ganhador:** <@{vencedor_id}>\n**{msg_xp}**",
            color=discord.Color.gold()
        )
        embed_fim.set_footer(text="Parabéns!")
        
        await mensagem.edit(embed=embed_fim, view=None)
        # Enviar resposta mencionando o ganhador
        await mensagem.reply(f"🎉 **Parabéns** <@{vencedor_id}>! Você ganhou: **{premio}** {msg_xp}")
    else:
        embed_fim = discord.Embed(
            title="❌ Sorteio Cancelado",
            description=f"Ninguém participou do sorteio de **{premio}**.",
            color=discord.Color.red()
        )
        await mensagem.edit(embed=embed_fim, view=None)
        await target_channel.send("❌ Ninguém participou do sorteio.")

# --- Comando Slash para Sorteio (/sorteio) ---
@bot.tree.command(name="sorteio", description="Iniciar um sorteio com prêmio")
@app_commands.describe(
    tempo="Duração do sorteio (ex: 10s, 5m, 1h, 1d)",
    premio="Prêmio do sorteio"
)
async def sorteio_slash(interaction: discord.Interaction, tempo: str, premio: str):
    """Comando slash para realizar sorteios"""
    
    # Verificar permissões
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ Você precisa ser administrador para usar este comando!", ephemeral=True)
        return
    
    # Definir canal do sorteio
    target_channel = interaction.channel
    if 'event_channel_id' in config:
        found_channel = bot.get_channel(config['event_channel_id'])
        if found_channel:
            target_channel = found_channel
    
    # Converter tempo
    try:
        unidade = tempo[-1].lower()
        valor = int(tempo[:-1])
        segundos = 0
        
        if unidade == 's':
            segundos = valor
        elif unidade == 'm':
            segundos = valor * 60
        elif unidade == 'h':
            segundos = valor * 3600
        elif unidade == 'd':
            segundos = valor * 86400
        else:
            await interaction.response.send_message("❌ Use s, m, h ou d para o tempo (Ex: 10m, 1h, 2d).", ephemeral=True)
            return
    except ValueError:
        await interaction.response.send_message("❌ Formato de tempo inválido! Use: 10s, 5m, 1h, 1d", ephemeral=True)
        return

    # Data de término para o timestamp
    termino = datetime.now() + timedelta(seconds=segundos)
    timestamp = int(termino.timestamp())

    embed = discord.Embed(
        title="🎉 Sorteio Iniciado!",
        description=f"**Prêmio:** {premio}\n\n**Tempo:** {tempo}\n**Termina:** <t:{timestamp}:R>\n\nClique no botão abaixo para participar!",
        color=discord.Color.purple()
    )
    embed.set_footer(text=f"Iniciado por {interaction.user.name}")
    
    # Criar a View
    view = SorteioView()
    
    # Responder a interação
    if target_channel == interaction.channel:
        await interaction.response.send_message(embed=embed, view=view)
        mensagem = await interaction.original_response()
    else:
        await interaction.response.send_message(f"✅ Sorteio iniciado em {target_channel.mention}!", ephemeral=True)
        mensagem = await target_channel.send(embed=embed, view=view)

    # Esperar o tempo
    await asyncio.sleep(segundos)

    # Desabilitar botão
    view.children[0].disabled = True
    await mensagem.edit(view=view)

    # Escolher ganhador
    users = list(view.participantes)

    if len(users) > 0:
        # --- Efeito de Roleta Animada ---
        for i in range(5):
            u_temp_id = random.choice(users)
            try: u_temp = await bot.fetch_user(u_temp_id)
            except: u_temp = None
            
            nome_temp = u_temp.display_name if u_temp else "???"
            
            embed_roleta = discord.Embed(
                title="🎰 ┃ SORTEANDO GANHADOR...",
                description=f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n🌀 **A roleta está girando...**\n> 👤 `{nome_temp}`\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
                color=random.choice([0x7E57C2, 0x4FC3F7, 0xF57C00])
            )
            embed_roleta.set_footer(text="A sorte está sendo decidida...")
            await mensagem.edit(embed=embed_roleta)
            await asyncio.sleep(1.2)

        vencedor_id = random.choice(users)
        vencedor = await bot.fetch_user(vencedor_id)
        
        embed_fim = discord.Embed(
            title="🎊 ┃ SORTEIO ENCERRADO!",
            description=(
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"🎉 **PARABÉNS AO GANHADOR!**\n\n"
                f"🎁 **Prêmio:** `{premio}`\n"
                f"🏆 **Vencedor:** <@{vencedor_id}>\n"
                f"🆔 **ID:** `{vencedor_id}`\n\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            ),
            color=0xFFD700, # Gold
            timestamp=datetime.now()
        )
        if vencedor.avatar: embed_fim.set_thumbnail(url=vencedor.avatar.url)
        embed_fim.set_image(url="https://media.giphy.com/media/26DOoD3XY675lW8Wc/giphy.gif") # Efeito de confetes
        embed_fim.set_footer(text=f"Total de participantes: {len(users)} • Sorteio realizado com sucesso!", icon_url=bot.user.avatar.url if bot.user.avatar else None)
        
        await mensagem.edit(embed=embed_fim, view=None)
        await mensagem.reply(f"👑 **{vencedor.mention}**, você é o grande vencedor do sorteio de **{premio}**! Entre em contato com a STAFF para resgatar.")
    else:
        embed_fim = discord.Embed(
            title="❌ Sorteio Cancelado",
            description=f"Ninguém participou do sorteio de **{premio}**.",
            color=discord.Color.red()
        )
        await mensagem.edit(embed=embed_fim, view=None)
        await target_channel.send("❌ Sorteio encerrado sem participantes.")

@bot.tree.command(name="link_convite", description="🔗 Gera um link de convite oficial do servidor para novos membros")
async def link_convite(interaction: discord.Interaction):
    """Gera um link de convite temporário"""
    try:
        # Criar convite com 24h de duração
        invite = await interaction.channel.create_invite(max_age=86400, reason=f"Gerado via comando por {interaction.user.name}")
        
        embed = discord.Embed(
            title="🔗 Convite do Servidor",
            description=f"Aqui está o seu link de convite para chamar amigos:\n\n**{invite.url}**\n\n*Este link expira em 24 horas.*",
            color=0x4FC3F7
        )
        embed.set_footer(text="Use com sabedoria!")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"❌ Erro ao gerar convite: {e}", ephemeral=True)

@bot.tree.command(name="booster", description="🚀 Exibe informações detalhadas sobre os impulsos do servidor")
async def booster(interaction: discord.Interaction):
    """Mostra informações sobre os boosters do servidor"""
    guild = interaction.guild
    boost_count = guild.premium_subscription_count
    boost_tier = guild.premium_tier
    boosters = guild.premium_subscribers
    
    embed = discord.Embed(
        title=f"🚀 Status de Boosters • {guild.name}",
        description="Confira as estatísticas de impulsos do nosso servidor:",
        color=0xFF73FA, # Rosa Discord Booster
        timestamp=datetime.now()
    )
    
    embed.add_field(name="⚡ Total de Boosts", value=f"**{boost_count} Boosts**", inline=True)
    embed.add_field(name="💎 Nível do Servidor", value=f"**Nível {boost_tier}**", inline=True)
    
    if boosters:
        nomes_boosters = "\n".join([f"✨ {b.mention}" for b in boosters[:15]])
        if len(boosters) > 15:
            nomes_boosters += f"\n*... e mais {len(boosters)-15} boosters!*"
        embed.add_field(name="🏆 Nossos Heróis (Boosters)", value=nomes_boosters or "Ninguém ainda.", inline=False)
    else:
        embed.add_field(name="🏆 Nossos Heróis (Boosters)", value="Nenhum booster ativo no momento.", inline=False)
        
    embed.set_thumbnail(url="https://cdn.discordapp.com/emojis/1109033333333333333.gif?v=1" if not guild.icon else guild.icon.url)
    embed.set_footer(text="Obrigado por apoiar o servidor!", icon_url=bot.user.avatar.url if bot.user.avatar else None)
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="roleta", description="🎰 Sorteio coletivo com roleta de prêmios (XP/VIP)")
@app_commands.describe(tempo="Duração do sorteio (ex: 30s, 5m, 1h)")
async def roleta(interaction: discord.Interaction, tempo: str):
    """Sistema de sorteio coletivo com roleta de prêmios solicitados"""
    
    # Verificar permissões STAFF
    if not interaction.user.guild_permissions.manage_messages:
        await interaction.response.send_message("❌ Apenas membros da STAFF podem iniciar a roleta!", ephemeral=True)
        return

    # Converter tempo
    try:
        unidade = tempo[-1].lower()
        valor = int(tempo[:-1])
        segundos = 0
        if unidade == 's': segundos = valor
        elif unidade == 'm': segundos = valor * 60
        elif unidade == 'h': segundos = valor * 3600
        else:
            await interaction.response.send_message("❌ Use s, m ou h (Ex: 30s, 5m).", ephemeral=True)
            return
    except:
        await interaction.response.send_message("❌ Formato de tempo inválido! Use: 30s, 5m", ephemeral=True)
        return

    termino = int((datetime.now() + timedelta(seconds=segundos)).timestamp())
    
    embed = discord.Embed(
        title="🎰 ┃ ROLETA COLETIVA DA SORTE",
        description=(
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"🎁 **Prêmios em Jogo:** `Vips e XP Variados`\n"
            f"⏳ **Termina em:** <t:{termino}:R>\n\n"
            f"🚀 **Clique no botão abaixo para participar!**\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        ),
        color=0xFFD700
    )
    embed.set_footer(text=f"Iniciado por {interaction.user.display_name}")
    embed.set_image(url="https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExOHcyeHExZ3R6Z3R6Z3R6Z3R6Z3R6Z3R6Z3R6Z3R6Z3R6Z3R6JmVwPXYxX2ludGVybmFsX2dpZl9ieV9pZCZjdD1n/M90mJvC88S77t7G0vK/giphy.gif")
    
    view = SorteioView()
    await interaction.response.send_message(embed=embed, view=view)
    msg = await interaction.original_response()

    # Aguardar tempo do sorteio
    await asyncio.sleep(segundos)
    
    # Escolher ganhador
    users = list(view.participantes)
    if len(users) == 0:
        embed_fail = discord.Embed(
            title="❌ Roleta Cancelada",
            description="Ninguém participou da roleta coletiva desta vez.",
            color=discord.Color.red()
        )
        await msg.edit(embed=embed_fail, view=None)
        return

    # 1. Roleta de MEMBROS (Escolher quem ganha)
    for i in range(5):
        u_temp_id = random.choice(users)
        try: u_temp = await bot.fetch_user(u_temp_id)
        except: u_temp = None
        nome_temp = u_temp.display_name if u_temp else "???"
        
        embed_r1 = discord.Embed(
            title="🎰 ┃ SORTEANDO GANHADOR...",
            description=f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n🌀 **A roleta está girando...**\n> 👤 `{nome_temp}`\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            color=0x4FC3F7
        )
        await msg.edit(embed=embed_r1, view=None)
        await asyncio.sleep(1)

    ganhador_id = random.choice(users)
    ganhador = await bot.fetch_user(ganhador_id)

    # 2. Roleta de PRÊMIOS (Escolher o que ganha)
    premios = [
        {"nome": "VIP Bronze", "tipo": "vip"},
        {"nome": "100 XP", "tipo": "xp", "valor": 100},
        {"nome": "10 XP", "tipo": "xp", "valor": 10},
        {"nome": "20 XP", "tipo": "xp", "valor": 20},
        {"nome": "45 XP", "tipo": "xp", "valor": 45},
        {"nome": "200 XP", "tipo": "xp", "valor": 200},
        {"nome": "VIP Ouro", "tipo": "vip"},
        {"nome": "299 XP", "tipo": "xp", "valor": 299},
        {"nome": "430 XP", "tipo": "xp", "valor": 430},
        {"nome": "231 XP", "tipo": "xp", "valor": 231},
        {"nome": "102 XP", "tipo": "xp", "valor": 102}
    ]

    for i in range(4):
        p_temp = random.choice(premios)
        embed_r2 = discord.Embed(
            title="🎁 ┃ SORTEANDO PRÊMIO...",
            description=f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n💰 **Para:** {ganhador.mention}\n🌀 **Prêmio girando:** `{p_temp['nome']}`\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            color=0xF57C00
        )
        await msg.edit(embed=embed_r2)
        await asyncio.sleep(1)

    # Resultado Final
    ganhou = random.choice(premios)
    info_p = ""
    
    if ganhou["tipo"] == "xp":
        usuarios = carregar_usuarios()
        u_id = str(ganhador_id)
        if u_id not in usuarios: usuarios[u_id] = {"xp": 0, "level": 0}
        usuarios[u_id]["xp"] = usuarios[u_id].get("xp", 0) + ganhou["valor"]
        salvar_usuarios(usuarios)
        info_p = f"✨ **+{ganhou['valor']} XP** adicionados!"
    elif ganhou["tipo"] == "vip":
        info_p = f"👑 Reivindique seu **{ganhou['nome']}** com a STAFF!"

    embed_final = discord.Embed(
        title="🎊 ┃ RESULTADO DA ROLETA!",
        description=(
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"👤 **VENCEDOR:** {ganhador.mention}\n"
            f"🎁 **PRÊMIO:** `{ganhou['nome']}`\n\n"
            f"✅ **STATUS:** {info_p}\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        ),
        color=0x00FF00
    )
    if ganhador.avatar: embed_final.set_thumbnail(url=ganhador.avatar.url)
    embed_final.set_image(url="https://media.giphy.com/media/26DOoD3XY675lW8Wc/giphy.gif")
    embed_final.set_footer(text="Parabéns ao novo vencedor!")
    
    await msg.edit(embed=embed_final)
    await msg.reply(f"👑 {ganhador.mention} ganhou **{ganhou['nome']}** na roleta coletiva!")

@bot.command(name="sorteio")
@commands.has_permissions(administrator=True)
async def sorteio(ctx, tempo: str, *, premio: str):
    """Realizar um sorteio automático com BOTÃO"""
    
    # Definir canal do sorteio
    target_channel = ctx.channel
    if 'event_channel_id' in config:
        found_channel = bot.get_channel(config['event_channel_id'])
        if found_channel:
            target_channel = found_channel
    
    # Converter tempo
    unidade = tempo[-1]
    valor = int(tempo[:-1])
    segundos = 0
    
    if unidade == 's':
        segundos = valor
    elif unidade == 'm':
        segundos = valor * 60
    elif unidade == 'h':
        segundos = valor * 3600
    elif unidade == 'd':
        segundos = valor * 86400
    else:
        await ctx.send("❌ Use s, m, h ou d para o tempo (Ex: 10m).")
        return

    # Data de término para o timestamp
    termino = datetime.now() + timedelta(seconds=segundos)
    timestamp = int(termino.timestamp())

    embed = discord.Embed(
        title="🎉 Sorteio Iniciado!",
        description=f"**Prêmio:** {premio}\n\n**Tempo:** {tempo}\n**Termina:** <t:{timestamp}:R>\n\nClique no botão abaixo para participar!",
        color=discord.Color.purple()
    )
    embed.set_footer(text=f"Iniciado por {ctx.author.name}")
    
    # Criar a View
    view = SorteioView()
    
    # Enviar no canal de destino
    mensagem = await target_channel.send(embed=embed, view=view)
    
    if target_channel != ctx.channel:
        await ctx.send(f"✅ Sorteio iniciado em {target_channel.mention}!")

    # Esperar o tempo
    await asyncio.sleep(segundos)

    # Desabilitar botão
    view.children[0].disabled = True
    await mensagem.edit(view=view)

    # Escolher ganhador
    users = list(view.participantes)

    if len(users) > 0:
        vencedor_id = random.choice(users)
        
        embed_fim = discord.Embed(
            title="🎉 Sorteio Encerrado!",
            description=f"**Prêmio:** {premio}\n**Ganhador:** <@{vencedor_id}>",
            color=discord.Color.gold()
        )
        embed_fim.set_footer(text="Parabéns!")
        
        await mensagem.edit(embed=embed_fim, view=None) # Remove botão no fim
        # Enviar resposta mencionando o ganhador no formato solicitado
        await mensagem.reply(f"🎉 **Parabéns** <@{vencedor_id}>! Você ganhou: **{premio}**")
    else:
        embed_fim = discord.Embed(
            title="❌ Sorteio Cancelado",
            description=f"Ninguém participou do sorteio de **{premio}**.",
            color=discord.Color.red()
        )
        await mensagem.edit(embed=embed_fim, view=None)
        await target_channel.send("❌ Ninguém participou do sorteio.")

@sorteio.error
async def sorteio_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArguments):
        await ctx.send("❌ Uso incorreto! Digite: `!sorteio <tempo> <prêmio>`\nExemplo: `!sorteio 10m VIP Gold`")
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ Você precisa ser administrador para usar este comando!")
    else:
        await ctx.send(f"❌ Ocorreu um erro: {error}")

@bot.command(name="botinfo")
async def botinfo(ctx):
    """Mostra informações sobre o bot"""
    embed = discord.Embed(
        title=f"🤖 Informações do {bot.user.name}",
        color=discord.Color.gold(),
        timestamp=datetime.now()
    )
    
    embed.add_field(name="🆔 ID", value=bot.user.id, inline=True)
    embed.add_field(name="👥 Servidores", value=len(bot.guilds), inline=True)
    embed.add_field(name="📶 Latência", value=f"{round(bot.latency * 1000)}ms", inline=True)
    embed.add_field(name="🐍 Python", value="3.11.9", inline=True)
    embed.add_field(name="📚 Biblioteca", value=f"discord.py {discord.__version__}", inline=True)
    embed.add_field(name="👑 Criador", value="Owner", inline=True)
    
    embed.set_thumbnail(url=bot.user.avatar.url if bot.user.avatar else None)
    embed.set_footer(text="STAFF System")
    
    await ctx.send(embed=embed)

# --- Sistema de Perfil (View e Modal) ---
class PerfilView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Ver Meu Perfil", style=discord.ButtonStyle.secondary, emoji="👤", custom_id="perf_ver_perfil")
    async def ver_perfil(self, interaction: discord.Interaction, button: discord.ui.Button):
        await logic_perfil(interaction, interaction.user)

    @discord.ui.button(label="Adicionar ID", style=discord.ButtonStyle.secondary, emoji="🆔", custom_id="perf_add_id")
    async def add_id(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(IDModal())

class IDModal(discord.ui.Modal, title="🆔 Adicionar ID Game"):
    id_input = discord.ui.TextInput(label="ID do Jogo", min_length=1, max_length=30, required=True)

    async def on_submit(self, interaction: discord.Interaction):
        usuarios = carregar_usuarios()
        user_id = str(interaction.user.id)
        novo_id = self.id_input.value
        
        # Removido: if not novo_id.isdigit(): pois pode ser qualquer ID
            
        for id_discord, dados in usuarios.items():
            if id_discord != user_id and dados.get("codigo") == novo_id:
                await interaction.response.send_message(f"❌ O ID **{novo_id}** já está sendo usado!", ephemeral=True)
                return

        if user_id not in usuarios: usuarios[user_id] = {"xp": 0, "level": 0}
        old_id = usuarios[user_id].get("codigo")
        usuarios[user_id]["codigo"] = novo_id
        salvar_usuarios(usuarios)
        
        # Log de alteração de ID
        log_channel_id = 1460477431684268225
        try:
            log_channel = bot.get_channel(log_channel_id) or await interaction.client.fetch_channel(log_channel_id)
            if log_channel:
                msg = f"🔄 **{interaction.user.name}** alterou o ID para: **{novo_id}**" if old_id else f"✅ **{interaction.user.name}** adicionou novo ID: **{novo_id}**"
                await log_channel.send(f"{msg} ({interaction.user.mention})")
        except:
            pass

        await interaction.response.send_message(f"✅ ID atualizado para: **{novo_id}**", ephemeral=True)

async def logic_perfil(ctx_or_inter, membro: discord.Member = None):
    is_interaction = isinstance(ctx_or_inter, discord.Interaction)
    membro = membro or (ctx_or_inter.user if is_interaction else ctx_or_inter.author)
    usuarios = carregar_usuarios()
    user_id = str(membro.id)
    
    if user_id not in usuarios:
        usuarios[user_id] = {"xp": 0, "level": 0}
        salvar_usuarios(usuarios)
    
    dados = usuarios[user_id]
    xp, level = dados.get("xp", 0), dados.get("level", 0)
    codigo = dados.get("codigo", "Não definido")

    embed = discord.Embed(title=f"👤 Perfil de {membro.display_name}", color=0x000000, timestamp=datetime.now())
    embed.set_thumbnail(url=membro.display_avatar.url)
    embed.add_field(name="⭐ Nível", value=f"**{level}**", inline=True)
    embed.add_field(name="✨ XP Atual", value=f"**{xp}**", inline=True)
    moedas = dados.get("moedas", 0)
    embed.add_field(name="💰 Moedas", value=f"**{moedas}**", inline=True)
    
    comissao = dados.get("comissao", 0.0)
    embed.add_field(name="💳 Comissão", value=f"**R$ {comissao:.2f}**", inline=True)

        
    embed.add_field(name="🆔 ID Game", value=f"`{codigo}`", inline=True)
    embed.add_field(name="🛡️ Cargos", value=", ".join([r.mention for r in membro.roles if r.name != "@everyone"]) or "Nenhum", inline=False)
    
    if level >= 100:
        embed.add_field(name="📊 Progresso (MAX)", value="🏆 **Você é uma Lenda! Nível Máximo Atingido!** 🔥", inline=False)
    else:
        xp_faltante = ((level + 1) * 500) - xp
        percentual = int(((xp % 500) / 500) * 100)
        embed.add_field(name=f"📊 Progresso ({percentual}%)", value=f"Faltam **{xp_faltante} XP** para o nível {level + 1}", inline=False)

    embed.set_footer(text=f"ID: {membro.id}")

    if is_interaction:
        if not ctx_or_inter.response.is_done():
            await ctx_or_inter.response.send_message(embed=embed, ephemeral=True)
        else:
            await ctx_or_inter.followup.send(embed=embed, ephemeral=True)
    else:
        await ctx_or_inter.send(embed=embed)

@bot.tree.command(name="money", description="Gerencia as moedas de um usuário (Apenas Dono)")
@app_commands.describe(acao="Escolha o que fazer", membro="O membro alvo", valor="Quantidade de moedas")
@app_commands.choices(acao=[
    app_commands.Choice(name="Adicionar (+)", value="add"),
    app_commands.Choice(name="Remover (-)", value="remove"),
    app_commands.Choice(name="Definir (=)", value="set")
])
async def money_cmd(interaction: discord.Interaction, acao: str, membro: discord.Member, valor: int):
    # Check if dono (owner)
    is_dono = interaction.user.id == interaction.guild.owner_id
    if not is_dono:
        for role in interaction.user.roles:
            if "dono" in role.name.lower() or "fundador" in role.name.lower():
                is_dono = True
                break
    if not is_dono:
        return await interaction.response.send_message("❌ Apenas um **Dono** pode usar este comando!", ephemeral=True)
        
    if valor < 0:
        return await interaction.response.send_message("❌ O valor não pode ser negativo!", ephemeral=True)
        
    usuarios = carregar_usuarios()
    user_id = str(membro.id)
    if user_id not in usuarios:
        usuarios[user_id] = {"xp": 0, "level": 0}
        
    moedas_atuais = usuarios[user_id].get("moedas", 0)
    
    if acao == "add":
        usuarios[user_id]["moedas"] = moedas_atuais + valor
        msg = f"✅ Adicionado **{valor} moedas** para {membro.mention}!"
    elif acao == "remove":
        usuarios[user_id]["moedas"] = max(0, moedas_atuais - valor)
        msg = f"✅ Removido **{valor} moedas** de {membro.mention}!"
    else:
        usuarios[user_id]["moedas"] = valor
        msg = f"✅ As moedas de {membro.mention} foram definidas para **{valor}**!"
        
    salvar_usuarios(usuarios)
    await interaction.response.send_message(msg, ephemeral=True)

@bot.tree.command(name="mis", description="Gerencia a comissão de um atendente ou membro (Apenas Dono)")
@app_commands.describe(acao="Escolha o que fazer", membro="O membro alvo", valor="Valor em R$")
@app_commands.choices(acao=[
    app_commands.Choice(name="Adicionar (+)", value="add"),
    app_commands.Choice(name="Remover (-)", value="remove"),
    app_commands.Choice(name="Definir (=)", value="set")
])
async def mis_cmd(interaction: discord.Interaction, acao: str, membro: discord.Member, valor: float):
    # Check if dono (owner)
    is_dono = interaction.user.id == interaction.guild.owner_id
    if not is_dono:
        for role in interaction.user.roles:
            if "dono" in role.name.lower() or "fundador" in role.name.lower():
                is_dono = True
                break
    if not is_dono:
        return await interaction.response.send_message("❌ Apenas um **Dono** pode usar este comando!", ephemeral=True)
        
    if valor < 0:
        return await interaction.response.send_message("❌ O valor não pode ser negativo!", ephemeral=True)
        
    usuarios = carregar_usuarios()
    user_id = str(membro.id)
    if user_id not in usuarios:
        usuarios[user_id] = {"xp": 0, "level": 0}
        
    comissao_atual = usuarios[user_id].get("comissao", 0.0)
    
    if acao == "add":
        usuarios[user_id]["comissao"] = comissao_atual + valor
        msg = f"✅ Adicionado **R$ {valor:.2f}** de comissão para {membro.mention}!"
    elif acao == "remove":
        usuarios[user_id]["comissao"] = max(0.0, comissao_atual - valor)
        msg = f"✅ Removido **R$ {valor:.2f}** da comissão de {membro.mention}!"
    else:
        usuarios[user_id]["comissao"] = valor
        msg = f"✅ A comissão de {membro.mention} foi definida para **R$ {valor:.2f}**!"
        
    salvar_usuarios(usuarios)
    await interaction.response.send_message(msg, ephemeral=True)

@bot.tree.command(name="perfil", description="Ver o seu perfil ou de outro membro")
async def perfil(interaction: discord.Interaction, membro: discord.Member = None):
    await logic_perfil(interaction, membro)

@bot.tree.command(name="set_id", description="Configura um ID de jogo para você ou para outro membro")
@app_commands.describe(novo_id="O ID a ser definido", membro="Membro que receberá o ID (apenas Staff/Admin)")
async def set_id_cmd(interaction: discord.Interaction, novo_id: str, membro: discord.Member = None):
    # Determine o target
    if membro and membro != interaction.user:
        is_staff = False
        if interaction.user.guild_permissions.administrator or interaction.user.id == interaction.guild.owner_id:
            is_staff = True
        else:
            for role in interaction.user.roles:
                if any(n in role.name.lower() for n in ["adm", "dono", "staff", "atendente"]):
                    is_staff = True
                    break
        if not is_staff:
            return await interaction.response.send_message("❌ Apenas administradores ou staff podem alterar o ID de outros membros!", ephemeral=True)
        target = membro
    else:
        target = interaction.user

    usuarios = carregar_usuarios()
    user_id = str(target.id)
        
    for id_discord, dados in usuarios.items():
        if id_discord != user_id and dados.get("codigo") == novo_id:
            return await interaction.response.send_message(f"❌ O ID **{novo_id}** já está sendo usado por outra pessoa!", ephemeral=True)

    if user_id not in usuarios: usuarios[user_id] = {"xp": 0, "level": 0}
    old_id = usuarios[user_id].get("codigo")
    usuarios[user_id]["codigo"] = novo_id
    salvar_usuarios(usuarios)
    
    # Log de alteração de ID
    log_channel_id = 1460477431684268225
    try:
        log_channel = bot.get_channel(log_channel_id) or await interaction.client.fetch_channel(log_channel_id)
        if log_channel:
            msg = f"🔄 **{interaction.user.name}** alterou o ID de **{target.name}** para: **{novo_id}**" if old_id else f"✅ **{interaction.user.name}** adicionou novo ID para **{target.name}**: **{novo_id}**"
            await log_channel.send(f"{msg} ({target.mention})")
    except:
        pass

    if target == interaction.user:
        await interaction.response.send_message(f"✅ Seu ID foi atualizado para: **{novo_id}**", ephemeral=True)
    else:
        await interaction.response.send_message(f"✅ O ID de {target.mention} foi atualizado para: **{novo_id}**", ephemeral=True)

# --- MODAL DE SAQUE DE PARCEIRO ---
class SacarParceiroModal(discord.ui.Modal, title="💸 Solicitar Saque de Comissão"):
    valor_input = discord.ui.TextInput(
        label="Valor do Saque",
        placeholder="Quanto você deseja sacar? (Ex: 50.00)",
        required=True,
        min_length=1
    )
    pix_key = discord.ui.TextInput(
        label="Chave PIX",
        placeholder="Digite sua chave PIX para recebimento...",
        required=True,
        min_length=5,
        max_length=100
    )

    def __init__(self, saldo_disponivel):
        super().__init__()
        self.saldo_disponivel = saldo_disponivel

    async def on_submit(self, interaction: discord.Interaction):
        usuarios = carregar_usuarios()
        user_id = str(interaction.user.id)
        
        # Validar Valor
        try:
            valor_text = self.valor_input.value.replace('R$', '').replace(',', '.').strip()
            valor_solicitado = float(valor_text)
            if valor_solicitado <= 0:
                 raise ValueError("Valor deve ser positivo")
        except ValueError:
            await interaction.response.send_message("❌ Valor inválido! Use o formato: `50.00`", ephemeral=True)
            return

        if valor_solicitado > self.saldo_disponivel:
            await interaction.response.send_message(f"❌ Saldo insuficiente! Você tem **R$ {self.saldo_disponivel:.2f}** disponível.", ephemeral=True)
            return

        # Deduzir saldo
        usuarios[user_id]["comissao"] -= valor_solicitado
        salvar_usuarios(usuarios)

        # Enviar Log de Saque (Canal: 1463258096330739744)
        log_channel_id = 1463258096330739744
        log_channel = bot.get_channel(log_channel_id) or await bot.fetch_channel(log_channel_id)
        
        if log_channel:
            # Busca o cargo ADM priorizando o emoji de adaga 🗡️
            role_adm = discord.utils.get(interaction.guild.roles, name="🗡️ ADM") or \
                       discord.utils.get(interaction.guild.roles, name="⚔️ ADM") or \
                       discord.utils.find(lambda r: "ADM" in r.name.upper(), interaction.guild.roles)
            
            mention_adm = role_adm.mention if role_adm else "@🗡️ ADM"

            embed_log = discord.Embed(
                title="🏦 Nova Solicitação de Saque",
                color=discord.Color.blue(),
                timestamp=datetime.now()
            )
            embed_log.add_field(name="👤 Parceiro", value=f"{interaction.user.mention} ({interaction.user.name})", inline=True)
            embed_log.add_field(name="💵 Valor Solicitado", value=f"**R$ {valor_solicitado:.2f}**", inline=True)
            embed_log.add_field(name="💰 Saldo Restante", value=f"R$ {usuarios[user_id].get('comissao', 0.0):.2f}", inline=True)
            embed_log.add_field(name="🔑 Chave PIX", value=f"`{self.pix_key.value}`", inline=False)
            
            p_data = usuarios.get(user_id, {})
            id_game = p_data.get("codigo", "Não Definido")
            embed_log.set_footer(text=f"ID Game: {id_game} • Requisite seu pagamento com a staff.")
            
            await log_channel.send(content=f"🔔 **Pagamento Pendente:** {mention_adm}", embed=embed_log)

        await interaction.response.send_message(
            f"✅ **Solicitação enviada!**\nO valor de **R$ {valor_solicitado:.2f}** foi debitado do seu saldo e a staff foi notificada.\nSaldo restante: **R$ {usuarios[user_id]['comissao']:.2f}**",
            ephemeral=True
        )

@bot.tree.command(name="sacar", description="Solicita o saque do seu saldo de comissão de parceiro")
async def sacar(interaction: discord.Interaction):
    usuarios = carregar_usuarios()
    user_id = str(interaction.user.id)
    
    saldo = usuarios.get(user_id, {}).get("comissao", 0.0)
    
    if saldo <= 0:
        await interaction.response.send_message("❌ Você não possui saldo de comissão para sacar!", ephemeral=True)
        return
    
    # Abrir o modal passando o saldo disponível
    await interaction.response.send_modal(SacarParceiroModal(saldo))

@bot.tree.command(name="remover_moedas", description="Remove uma quantidade de moedas de um membro (Apenas Staff)")
@app_commands.describe(membro="O membro que terá as moedas removidas", quantidade="Quantidade de moedas para remover")
async def remover_moedas(interaction: discord.Interaction, membro: discord.Member, quantidade: int):
    # Apenas administradores podem usar
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ Você precisa ser administrador para usar este comando!", ephemeral=True)
        return
    
    if quantidade <= 0:
        await interaction.response.send_message("❌ A quantidade deve ser maior que zero!", ephemeral=True)
        return

    usuarios = carregar_usuarios()
    user_id = str(membro.id)
    
    if user_id not in usuarios or "moedas" not in usuarios[user_id]:
        await interaction.response.send_message(f"❌ O membro {membro.mention} não possui moedas registradas!", ephemeral=True)
        return
    
    moedas_atuais = usuarios[user_id].get("moedas", 0)
    
    if moedas_atuais < quantidade:
        await interaction.response.send_message(f"❌ O membro possui apenas **{moedas_atuais}** moedas. Não é possível remover {quantidade}!", ephemeral=True)
        return

    usuarios[user_id]["moedas"] -= quantidade
    salvar_usuarios(usuarios)
    
    embed = discord.Embed(
        title="🪙 Moedas Removidas",
        description=f"Foi removido moedas de {membro.mention} com sucesso.",
        color=discord.Color.red(),
        timestamp=datetime.now()
    )
    embed.add_field(name="👤 Membro", value=membro.mention, inline=True)
    embed.add_field(name="🪙 Quantidade Removida", value=str(quantidade), inline=True)
    embed.add_field(name="💰 Novo Saldo", value=str(usuarios[user_id]["moedas"]), inline=True)
    embed.set_footer(text=f"Executado por {interaction.user.name}")
    
    await interaction.response.send_message(embed=embed)
    print(f"🪙 {quantidade} moedas de {membro.name} removidas por {interaction.user.name}")

@bot.tree.command(name="adicionar_xp", description="Dar XP para um membro (Apenas Admins)")
@app_commands.describe(membro="Membro que receberá XP", quantidade="Quantidade de XP")
async def adicionar_xp(interaction: discord.Interaction, membro: discord.Member, quantidade: int):
    if not interaction.user.guild_permissions.administrator:
        return await interaction.response.send_message("❌ Sem permissão!", ephemeral=True)
    
    usuarios = carregar_usuarios()
    user_id = str(membro.id)
    if user_id not in usuarios:
        usuarios[user_id] = {"xp": 0, "level": 0}
    
    if usuarios[user_id]["level"] >= 100:
        return await interaction.response.send_message(f"⚠️ {membro.mention} já está no nível máximo (100)!", ephemeral=True)

    novo_xp = usuarios[user_id]["xp"] + quantidade
    if novo_xp >= 50000:
        novo_xp = 50000
    
    
    # Sistema de Moedas: REMOVIDO DAQUI (Agora é por troca)
    
    usuarios[user_id]["xp"] = novo_xp
    novo_nivel = usuarios[user_id]["xp"] // 500
    usuarios[user_id]["level"] = novo_nivel
    salvar_usuarios(usuarios)
    
    await gerenciar_cargos_nivel(membro, novo_nivel)
    
    await interaction.response.send_message(f"✅ Adicionado **{quantidade} XP** para {membro.mention}! (Nível: {novo_nivel})")

@bot.tree.command(name="trocar_xp", description="Trocar seu XP por Moedas (1000 XP = 1 Moeda)")
@app_commands.describe(quantidade="Quantidade de XP para trocar (Múltiplos de 1000)")
async def trocar_xp(interaction: discord.Interaction, quantidade: int):
    """Comando para o membro trocar XP por Moedas"""
    user_id = str(interaction.user.id)
    usuarios = carregar_usuarios()
    
    if user_id not in usuarios:
        await interaction.response.send_message("❌ Verifique seu perfil primeiro antes de usar!", ephemeral=True)
        return

    xp_atual = usuarios[user_id].get("xp", 0)
    
    if quantidade <= 0:
        await interaction.response.send_message("❌ Digite um valor válido maior que 0!", ephemeral=True)
        return
        
    if xp_atual < quantidade:
        await interaction.response.send_message(f"❌ Você não tem XP suficiente! Você tem: **{xp_atual} XP**", ephemeral=True)
        return
        
    # Calcular moedas (1000 XP = 1 Moeda)
    moedas_ganhas = quantidade // 1000
    
    if moedas_ganhas < 1:
         await interaction.response.send_message("❌ Você precisa trocar pelo menos **1000 XP** para ganhar 1 moeda!", ephemeral=True)
         return

    # --- LIMITE SEMANAL ---
    hoje = datetime.now()
    semana_atual = hoje.isocalendar()[1]
    ano_atual = hoje.year
    
    ultima_troca_semana = usuarios[user_id].get("ultima_troca_semana", 0)
    ultima_troca_ano = usuarios[user_id].get("ultima_troca_ano", 0)
    trocas_semana = usuarios[user_id].get("trocas_semana", 0)
    
    if ultima_troca_semana != semana_atual or ultima_troca_ano != ano_atual:
        # Resetar limite semanal
        trocas_semana = 0
        
    LIMITE_MOEDAS_SEMANA = 10 # Limite de 10 moedas por semana (Ajustável)
    
    if trocas_semana + moedas_ganhas > LIMITE_MOEDAS_SEMANA:
        moedas_restantes = LIMITE_MOEDAS_SEMANA - trocas_semana
        if moedas_restantes <= 0:
            await interaction.response.send_message(f"❌ Você já atingiu o limite semanal de trocas (**{LIMITE_MOEDAS_SEMANA} Moedas**). Aguarde a próxima semana!", ephemeral=True)
        else:
            await interaction.response.send_message(f"❌ Você só pode trocar mais **{moedas_restantes} Moedas** esta semana. (Limite: {LIMITE_MOEDAS_SEMANA})", ephemeral=True)
        return
         
    custo_real_xp = moedas_ganhas * 1000 # Garante que só desconta o que foi usado para moedas inteiras
    
    # Atualizar dados
    vencimento = datetime.now() + timedelta(days=30)
    vencimento_ts = vencimento.timestamp()
    
    usuarios[user_id]["xp"] -= custo_real_xp
    usuarios[user_id]["moedas"] = usuarios[user_id].get("moedas", 0) + moedas_ganhas
    usuarios[user_id]["data_vencimento_moedas"] = vencimento_ts
    usuarios[user_id]["trocas_semana"] = trocas_semana + moedas_ganhas
    usuarios[user_id]["ultima_troca_semana"] = semana_atual
    usuarios[user_id]["ultima_troca_ano"] = ano_atual
    
    # Atualizar Nível
    novo_nivel = usuarios[user_id]["xp"] // 500
    usuarios[user_id]["level"] = novo_nivel
    
    salvar_usuarios(usuarios)
    
    # Atualizar cargos (se caiu de nível, remove cargos)
    await gerenciar_cargos_nivel(interaction.user, novo_nivel)
    
    embed = discord.Embed(
        title="💰 Troca Realizada!",
        description=f"Você trocou **{custo_real_xp} XP** por **{moedas_ganhas} Moedas**!",
        color=discord.Color.gold()
    )
    embed.add_field(name="XP Restante", value=f"{usuarios[user_id]['xp']}", inline=True)
    embed.add_field(name="Saldo de Moedas", value=f"{usuarios[user_id]['moedas']}", inline=True)
    
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="remover_xp", description="Remover XP de um membro (Apenas Admins)")
@app_commands.describe(membro="Membro que perderá XP", quantidade="Quantidade de XP")
async def remover_xp(interaction: discord.Interaction, membro: discord.Member, quantidade: int):
    if not interaction.user.guild_permissions.administrator:
        return await interaction.response.send_message("❌ Sem permissão!", ephemeral=True)
    
    usuarios = carregar_usuarios()
    user_id = str(membro.id)
    if user_id not in usuarios:
        usuarios[user_id] = {"xp": 0, "level": 0}
    
    # Garantir que o XP não fique negativo
    usuarios[user_id]["xp"] = max(0, usuarios[user_id]["xp"] - quantidade)
    novo_nivel = usuarios[user_id]["xp"] // 500
    usuarios[user_id]["level"] = novo_nivel
    salvar_usuarios(usuarios)
    
    # Atualizar cargos (vai remover cargos de nvl alto se ele cair de nível)
    await gerenciar_cargos_nivel(membro, novo_nivel)
    
    await interaction.response.send_message(f"✅ Removido **{quantidade} XP** de {membro.mention}! (Nível atual: {novo_nivel})")

@bot.tree.command(name="painel_perfil", description="Enviar o painel de perfil (Apenas Admins)")
async def painel_perfil(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ Sem permissão!", ephemeral=True)
        return

    embed = discord.Embed(
        title="🌚 SISTEMA DE PERFIL - STAFF",
        description="Clique no botão abaixo para gerenciar seu perfil, conferir seu nível atual e ver seu progresso de XP no servidor!\n\n👑 **Benefícios de Nível:**\n• Cargos exclusivos\n• Permissões em canais especiais\n• Reconhecimento na comunidade",
        color=0x2b2d31
    )
    
    # Se houver uma imagem de logo/perfil, podemos adicionar (baseado na imagem do usuário)
    # embed.set_thumbnail(url="URL_DA_IMAGEM_AQUI") 

    await interaction.response.send_message("✅ Painel enviado!", ephemeral=True)
    await interaction.channel.send(embed=embed, view=PerfilView())

# --- Sistema de Cargos por Nível ---
async def gerenciar_cargos_nivel(member, nivel_atual):
    """Gerencia a troca de cargos baseada no nível"""
    global config
    if 'xp_roles' not in config: return
    
    try:
        # Ordenar níveis configurados (converter chaves str para int)
        niveis_configurados = sorted([int(k) for k in config['xp_roles'].keys()])
        
        cargo_para_adicionar = None
        cargos_para_remover = []
        
        # Encontrar o cargo correto para o nível atual
        for nivel in niveis_configurados:
            role_id = config['xp_roles'][str(nivel)]
            
            # Se o nível do cargo for menor ou igual ao nível atual, é um candidato
            if nivel <= nivel_atual:
                cargo_para_adicionar = role_id
            
            # Todos os cargos configurados são candidatos a remoção (limpeza)
            cargos_para_remover.append(role_id)
        
        # Se encontrou um cargo para adicionar
        if cargo_para_adicionar:
            # Não remover o cargo que vamos adicionar
            if cargo_para_adicionar in cargos_para_remover:
                cargos_para_remover.remove(cargo_para_adicionar)
            
            guild = member.guild
            role_add = guild.get_role(cargo_para_adicionar)
            
            # Adicionar o novo cargo
            if role_add and role_add not in member.roles:
                try:
                    await member.add_roles(role_add)
                    print(f"✅ Cargo {role_add.name} adicionado para {member.name}")
                except Exception as e:
                    print(f"❌ Erro ao adicionar cargo de nível: {e}")

            # Remover cargos antigos (lógica de substituição)
            roles_to_remove = []
            for r_id in cargos_para_remover:
                r = guild.get_role(r_id)
                if r and r in member.roles:
                    roles_to_remove.append(r)
            
            if roles_to_remove:
                try:
                    await member.remove_roles(*roles_to_remove)
                    print(f"♻️ Cargos antigos removidos de {member.name}")
                except Exception as e:
                    print(f"❌ Erro ao remover cargos antigos: {e}")

    except Exception as e:
        print(f"❌ Erro na função gerenciar_cargos_nivel: {e}")

@bot.tree.command(name="configurar_xp_cargo", description="Configurar cargo para um nível específico")
@app_commands.describe(nivel="Nível para ganhar o cargo", cargo="Cargo que será ganho")
async def configurar_xp_cargo(interaction: discord.Interaction, nivel: int, cargo: discord.Role):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ Sem permissão!", ephemeral=True)
        return
    
    global config
    if 'xp_roles' not in config:
        config['xp_roles'] = {}
    
    # Salvar configuração (chave string para JSON)
    config['xp_roles'][str(nivel)] = cargo.id
    
    # Salvar no arquivo
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4)
            
        embed = discord.Embed(
            title="✅ Configuração de XP Salva",
            description=f"Quando atingir **Nível {nivel}**, ganhará o cargo {cargo.mention}",
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed)
    except Exception as e:
        await interaction.response.send_message(f"❌ Erro ao salvar: {e}", ephemeral=True)

@bot.tree.command(name="listar_xp_cargos", description="Listar cargos de XP configurados")
async def listar_xp_cargos(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ Sem permissão!", ephemeral=True)
        return
    
    global config
    if 'xp_roles' not in config or not config['xp_roles']:
        await interaction.response.send_message("❌ Nenhum cargo de XP configurado!", ephemeral=True)
        return
    
    desc = ""
    # Ordenar por nível
    for nivel in sorted([int(k) for k in config['xp_roles'].keys()]):
        role_id = config['xp_roles'][str(nivel)]
        role = interaction.guild.get_role(role_id)
        role_chk = role.mention if role else "Cargo não encontrado"
        desc += f"**Nível {nivel}:** {role_chk}\n"
        
    embed = discord.Embed(title="📊 Cargos de XP", description=desc, color=discord.Color.blue())
    await interaction.response.send_message(embed=embed)



# --- Minigames ---

@bot.tree.command(name="dado", description="🎲 Rolar um dado. Padrão: 6 lados.")
@app_commands.describe(lados="Número de lados do dado (Padrão: 6)")
async def dado(interaction: discord.Interaction, lados: int = 6):
    if lados < 2:
        await interaction.response.send_message("❌ O dado precisa ter pelo menos 2 lados!", ephemeral=True)
        return
        
    resultado = random.randint(1, lados)
    embed = discord.Embed(
        title=f"🎲 Dado de {lados} lados!",
        description=f"O resultado foi: **{resultado}**",
        color=discord.Color.blue()
    )
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="moeda", description="🪙 Cara ou Coroa")
@app_commands.describe(escolha="Escolha Cara ou Coroa")
@app_commands.choices(escolha=[
    app_commands.Choice(name="Cara", value="Cara"),
    app_commands.Choice(name="Coroa", value="Coroa")
])
async def moeda(interaction: discord.Interaction, escolha: str):
    resultado = random.choice(["Cara", "Coroa"])
    venceu = escolha == resultado
    
    embed = discord.Embed(
        title="🪙 Cara ou Coroa",
        description=f"Você escolheu: **{escolha}**\nO resultado foi: **{resultado}**",
        color=discord.Color.green() if venceu else discord.Color.red()
    )
    
    if venceu:
        embed.set_footer(text="Você ganhou! 🎉")
    else:
        embed.set_footer(text="Você perdeu! 😔")
        
    await interaction.response.send_message(embed=embed)



# --- View do Ranking Pagina ---
class RankView(discord.ui.View):
    def __init__(self, ranking, user_pos, user_data, guild):
        super().__init__(timeout=60)
        self.ranking = ranking
        self.user_pos = user_pos
        self.user_data = user_data
        self.guild = guild
        self.pagina = 0
        self.por_pagina = 10
        self.max_paginas = min(10, (len(ranking) + self.por_pagina - 1) // self.por_pagina)

    async def obter_imagem_e_embed(self):
        inicio = self.pagina * self.por_pagina
        fim = inicio + self.por_pagina
        pagina_atual = self.ranking[inicio:fim]

        buffer = await gerar_imagem_rank(
            pagina_atual, 
            self.pagina + 1, 
            self.max_paginas, 
            self.user_pos, 
            self.user_data.get("xp", 0) if self.user_data else 0,
            self.guild
        )
        
        file = discord.File(buffer, filename="ranking.png")
        embed = discord.Embed(
            title=f"🏆 Ranking - Página {self.pagina + 1}",
            color=discord.Color.blue()
        )
        embed.set_image(url="attachment://ranking.png")
        embed.set_footer(text=f"Use os botões para navegar • Top 100")
        
        return file, embed

    @discord.ui.button(label="⬅️ Página Anterior", style=discord.ButtonStyle.primary)
    async def anterior(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.pagina > 0:
            self.pagina -= 1
            await interaction.response.defer()
            file, embed = await self.obter_imagem_e_embed()
            await interaction.edit_original_response(attachments=[file], embed=embed, view=self)
        else:
            await interaction.response.send_message("❌ Você já está na primeira página!", ephemeral=True)

    @discord.ui.button(label="Próxima Página ➡️", style=discord.ButtonStyle.primary)
    async def proximo(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.pagina < self.max_paginas - 1:
            self.pagina += 1
            await interaction.response.defer()
            file, embed = await self.obter_imagem_e_embed()
            await interaction.edit_original_response(attachments=[file], embed=embed, view=self)
        else:
            await interaction.response.send_message("❌ Você atingiu o limite de páginas (Top 100)!", ephemeral=True)

@bot.tree.command(name="rank", description="🏆 Ver o ranking de XP do servidor (Gráfico)")
async def rank(interaction: discord.Interaction):
    usuarios = carregar_usuarios()
    if not usuarios:
        await interaction.response.send_message("❌ Ninguém tem XP ainda!", ephemeral=True)
        return

    # Ordenar por XP decrescente
    ranking = sorted(usuarios.items(), key=lambda x: x[1].get("xp", 0), reverse=True)
    
    # Encontrar posição do usuário
    user_pos = 0
    user_data = None
    for i, (u_id, data) in enumerate(ranking, 1):
        if int(u_id) == interaction.user.id:
            user_pos = i
            user_data = data
            break
            
    view = RankView(ranking, user_pos, user_data, interaction.guild)
    await interaction.response.defer()
    file, embed = await view.obter_imagem_e_embed()
    await interaction.followup.send(file=file, embed=embed, view=view)

# --- View do PPT PvP ---
class PptView(discord.ui.View):
    def __init__(self, player1, player2):
        super().__init__(timeout=60)
        self.p1 = player1
        self.p2 = player2
        self.escolhas = {} # {user_id: "escolha"}

    @discord.ui.button(label="Pedra", emoji="🪨", style=discord.ButtonStyle.secondary, custom_id="ppt_pedra")
    async def pedra(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.processar_jogada(interaction, "Pedra")

    @discord.ui.button(label="Papel", emoji="📄", style=discord.ButtonStyle.secondary, custom_id="ppt_papel")
    async def papel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.processar_jogada(interaction, "Papel")

    @discord.ui.button(label="Tesoura", emoji="✂️", style=discord.ButtonStyle.secondary, custom_id="ppt_tesoura")
    async def tesoura(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.processar_jogada(interaction, "Tesoura")

    async def processar_jogada(self, interaction: discord.Interaction, escolha: str):
        if interaction.user.id not in [self.p1.id, self.p2.id]:
            await interaction.response.send_message("❌ Você não está nesse jogo!", ephemeral=True)
            return

        if interaction.user.id in self.escolhas:
             await interaction.response.send_message("❌ Você já escolheu!", ephemeral=True)
             return

        self.escolhas[interaction.user.id] = escolha
        await interaction.response.send_message(f"✅ Você escolheu **{escolha}**!", ephemeral=True)

        # Se os dois escolheram
        if len(self.escolhas) == 2:
            p1_choice = self.escolhas[self.p1.id]
            p2_choice = self.escolhas[self.p2.id]
            
            w_p1 = False
            empate = False

            if p1_choice == p2_choice:
                empate = True
            elif (p1_choice == "Pedra" and p2_choice == "Tesoura") or \
                 (p1_choice == "Papel" and p2_choice == "Pedra") or \
                 (p1_choice == "Tesoura" and p2_choice == "Papel"):
                w_p1 = True
            
            if empate:
                res_text = f"**EMPATE!** 😐\nAmbos escolheram {p1_choice}."
                color = discord.Color.gold()
            elif w_p1:
                res_text = f"🏆 **{self.p1.mention} VENCEU!**\n{p1_choice} vence {p2_choice}."
                color = discord.Color.green()
            else:
                res_text = f"🏆 **{self.p2.mention} VENCEU!**\n{p2_choice} vence {p1_choice}."
                color = discord.Color.green()
            
            embed_final = discord.Embed(title="🎮 Resultado do PPT", description=res_text, color=color)
            embed_final.add_field(name=self.p1.name, value=p1_choice, inline=True)
            embed_final.add_field(name=self.p2.name, value=p2_choice, inline=True)
            
            await interaction.followup.send(embed=embed_final)
            self.stop() 


@bot.tree.command(name="ppt", description="✂️ Jogo Pedra, Papel e Tesoura (Bot ou PvP)")
@app_commands.describe(jogada="Escolha para jogar contra o Bot", oponente="Mencione alguém para desafiar (PvP)")
@app_commands.choices(jogada=[
    app_commands.Choice(name="Pedra 🪨", value="Pedra"),
    app_commands.Choice(name="Papel 📄", value="Papel"),
    app_commands.Choice(name="Tesoura ✂️", value="Tesoura")
])
async def ppt(interaction: discord.Interaction, jogada: str = None, oponente: discord.Member = None):
    # Modo PvP
    if oponente:
        if oponente.bot:
             await interaction.response.send_message("❌ Você não pode desafiar bots (além de mim)!", ephemeral=True)
             return
        if oponente.id == interaction.user.id:
             await interaction.response.send_message("❌ Você não pode desafiar a si mesmo!", ephemeral=True)
             return
        
        embed = discord.Embed(
            title="⚔️ Desafio de PPT!",
            description=f"{interaction.user.mention} desafiou {oponente.mention}!\n\n**Escolham suas jogadas abaixo!** 👇",
            color=discord.Color.orange()
        )
        view = PptView(player1=interaction.user, player2=oponente)
        await interaction.response.send_message(content=f"{interaction.user.mention} vs {oponente.mention}", embed=embed, view=view)
        return

    # Modo Bot (padrão)
    if not jogada:
        await interaction.response.send_message("❌ Para jogar contra o Bot, você PRECISA escolher uma opção na lista 'jogada'!", ephemeral=True)
        return

    opcoes = ["Pedra", "Papel", "Tesoura"]
    bot_jogada = random.choice(opcoes)
    
    # Lógica do jogo
    if jogada == bot_jogada:
        resultado = "Empate! 😐"
        cor = discord.Color.gold()
    elif (jogada == "Pedra" and bot_jogada == "Tesoura") or \
         (jogada == "Papel" and bot_jogada == "Pedra") or \
         (jogada == "Tesoura" and bot_jogada == "Papel"):
        resultado = "Você Ganhou! 🎉"
        cor = discord.Color.green()
    else:
        resultado = "Você Perdeu! 😔"
        cor = discord.Color.red()
        
    embed = discord.Embed(
        title="🎮 Pedra, Papel ou Tesoura",
        color=cor
    )
    embed.add_field(name="Sua Jogada", value=jogada, inline=True)
    embed.add_field(name="Jogada do Bot", value=bot_jogada, inline=True)
    embed.add_field(name="Resultado", value=resultado, inline=False)
    
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="pokemon", description="🐾 Ver um Pokémon aleatório!")
async def pokemon(interaction: discord.Interaction):
    # Sortear um ID aleatório (atualmente existem 1025 Pokémon)
    poke_id = random.randint(1, 1025)
    
    # URL da imagem oficial de alta qualidade
    # Usando o GitHub do PokeAPI para pegar a imagem diretamente pelo ID (mais rápido)
    image_url = f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/{poke_id}.png"
    
    embed = discord.Embed(
        title="🐾 Qual é esse Pokémon?",
        description=f"Você encontrou um Pokémon selvagem!\n\n🆔 **ID:** `#{poke_id}`",
        color=discord.Color.red(),
        timestamp=datetime.now()
    )
    
    embed.set_image(url=image_url)
    embed.set_footer(text=f"Solicitado por {interaction.user.name}", icon_url=interaction.user.avatar.url if interaction.user.avatar else None)
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="projeto", description="🦅 Informações sobre o Projeto STAFF")
async def projeto(interaction: discord.Interaction):
    # Preparar imagem local
    file = None
    image_url = None
    
    image_path = os.path.join(BASE_DIR, "banner_projeto.png")
    if os.path.exists(image_path):
        file = discord.File(image_path, filename="banner_projeto.png")
        image_url = "attachment://banner_projeto.png"
    
    embed = discord.Embed(
        title="🐦‍🔥 PROJETO STAFF - O ORIGINAL 🐦‍🔥",
        description=(
            "Cansado de jogar em qualquer lugar?\n"
            "**Vem pro STAFF! Qualidade e diversão garantida.**"
        ),
        color=discord.Color.orange(),
        timestamp=datetime.now()
    )
    
    embed.add_field(
        name="🏆 **DIFERENCIAIS**",
        value=(
            "✅ Sistema de Elos e Patentes: Suba de nível jogando!\n"
            "✅ Arsenal Exclusivo: Skins de AWP Dragon, Barret e muito mais.\n"
            "✅ Feedback de Hit/Kill: Sons e efeitos visuais satisfatórios.\n"
            "✅ Inventário Moderno e Organizado.\n"
            "✅ Bots com IA: Treine sua mira mesmo sozinho!"
        ),
        inline=False
    )
    
    embed.add_field(
        name="🛡️ **PROTEÇÃO & QUALIDADE**",
        value=(
            "✅ Sistema Exclusivo de Proteção (Sem falsos positivos).\n"
            "✅ FPS Otimizado: Roda liso em qualquer PC.\n"
            "✅ Hospedagem BR: Ping baixo e estável.\n"
            "✅ Jogabilidade Solta: Mecânicas avançadas liberadas!"
        ),
        inline=False
    )
    
    embed.add_field(
        name="🌐 **COMUNIDADE**",
        value="Integração total e eventos diários.",
        inline=False
    )
    
    embed.add_field(
        name="🔗 **ENTRE AGORA**",
        value="[Clique aqui para entrar](https://discord.gg/5YWbbBZc8y)",
        inline=False
    )
    
    if image_url:
        embed.set_image(url=image_url)
    
    embed.set_footer(text="Projeto STAFF • Qualidade em primeiro lugar", icon_url=bot.user.avatar.url if bot.user.avatar else None)
    
    if file:
        await interaction.response.send_message(embed=embed, file=file)
    else:
        await interaction.response.send_message(embed=embed)


async def salvar_e_fechar_ticket_helper(channel: discord.TextChannel, closed_by: discord.Member):
    # Trava de Segurança Global
    if channel.id in canais_em_fechamento:
        return
    canais_em_fechamento.add(channel.id)

    try:
        global config
        
        # Pega a categoria do canal
        category = channel.category
        if not category:
            return

        await channel.send("📂 **Gerando registro do atendimento...**")
        
        messages = []
        raw_contents = []
        messages_obj_list = [] # Necessário para a automação de comissão
        comprovante_url = None
        
        async for msg in channel.history(limit=1000, oldest_first=True):
            # Não ignorar mensagens do bot para salvar os embeds da loja
            # if msg.author.bot:
            #     continue
                
            timestamp = (msg.created_at - timedelta(hours=3)).strftime("%d/%m/%Y %H:%M:%S")
            content = msg.content if msg.content else "[Sem texto]"
            
            # Incluir links de anexos (comprovantes, imagens, etc)
            if msg.attachments:
                for att in msg.attachments:
                    content += f"\n[ANEXO] {att.url}"
                    # Pegar a imagem (Sempre sobrescreve para pegar a MAIS RECENTE no final)
                    extensoes_img = ['.png', '.jpg', '.jpeg', '.gif', '.webp']
                    if any(att.filename.lower().endswith(ext) for ext in extensoes_img):
                        comprovante_url = att.url

            # Incluir conteúdo de EMBEDS (para salvar tabelas, pix, etc)
            if msg.embeds:
                for embed in msg.embeds:
                    if embed.title: content += f"\n[EMBED TITLE] {embed.title}"
                    if embed.description: content += f"\n[EMBED DESC] {embed.description}"
                    for field in embed.fields:
                        content += f"\n   🔹 {field.name}: {field.value}"
                    
            messages.append(f"[{timestamp}] {msg.author.name}: {content}")
            messages.append("-" * 50) # Separador visual
            raw_contents.append(msg.content if msg.content else "")
            messages_obj_list.append(msg)
        
        transcript_text = "\n".join(messages)
        filename = f"transcript-{channel.name}.txt"
        file_bytes = BytesIO(transcript_text.encode('utf-8'))
        
        # Identificar dono do ticket pelo tópico (Parsing robusto)
        ticket_owner = None
        owner_id = None
        if channel.topic:
            partes = [p.strip() for p in channel.topic.split("|")]
            for parte in partes:
                if parte.startswith("ID:"):
                    try:
                        owner_id = int(parte.replace("ID:", "").strip())
                        break
                    except:
                        pass
        
        if owner_id:
            ticket_owner = channel.guild.get_member(owner_id)
            if not ticket_owner:
                try:
                    ticket_owner = await bot.fetch_user(owner_id)
                except:
                    pass
                
        # Buscar usuários para pegar o ID Game
        usuarios = carregar_usuarios()
        
        # --- PROCESSAR COMISSÃO DE PARCEIRO PENDENTE ---
        if channel.topic:
            try:
                partes = [p.strip() for p in channel.topic.split("|")]
                p_id = None
                p_val = 0.0
                p_venda = 0.0
                for p in partes:
                    if p.startswith("Parceiro:"):
                        p_id = p.replace("Parceiro:", "").strip()
                    elif p.startswith("ComissaoP:"):
                        p_val = float(p.replace("ComissaoP:", "").strip())
                    elif p.startswith("VendaP:"):
                        p_venda = float(p.replace("VendaP:", "").strip())
                
                if p_id and p_val > 0:
                    usuarios[p_id] = usuarios.get(p_id, {"xp": 0, "level": 0})
                    usuarios[p_id]["comissao"] = usuarios[p_id].get("comissao", 0.0) + p_val
                    print(f"💰 Comissão de parceiro aplicada no fechamento: R$ {p_val:.2f} para ID {p_id}")
                    salvar_usuarios(usuarios) # Salvar imediatamente
                    
                    # Log no canal de comissões de parceiros (Pedido no Step 357)
                    canal_comissao_parceiro_id = 1461478321685532931
                    canal_log_p = bot.get_channel(canal_comissao_parceiro_id)
                    if canal_log_p:
                        # Identificar o parceiro
                        partner_member = channel.guild.get_member(int(p_id))
                        if not partner_member:
                            try: partner_member = await channel.guild.fetch_user(int(p_id))
                            except: pass
                        
                        client_user = ticket_owner # Já identificado acima
                        
                        # Cálculo da porcentagem para o log
                        percentStr = "5.0%" # Fallback
                        if p_venda > 0:
                            percent = (p_val / p_venda) * 100
                            percentStr = f"{percent:.1f}%"
                        
                        # Content mentionando o cargo @🗡️ ADM conforme pedido
                        # Busca o cargo ADM priorizando o emoji de adaga 🗡️
                        role_adm = discord.utils.get(channel.guild.roles, name="🗡️ ADM") or \
                                   discord.utils.get(channel.guild.roles, name="⚔️ ADM") or \
                                   discord.utils.find(lambda r: "ADM" in r.name.upper(), channel.guild.roles)
                                   
                        mention_adm = role_adm.mention if role_adm else "@🗡️ ADM"
                        
                        # O @parceiro fica no embed, no texto fica o nome (Mudado de Atendente para Parceiro no texto também)
                        p_nome = partner_member.display_name if partner_member else f'ID {p_id}'
                        content_txt = f"💰 **Comissão:** {mention_adm} | **Parceiro:** **{p_nome}** | **Venda:** R$ {p_venda:.2f}"
                        
                        # Embed Seguindo a Imagem enviada
                        embed_p = discord.Embed(
                            title="💰 Registro de Comissão",
                            description="Um ticket foi finalizado e a comissão foi processada.",
                            color=discord.Color.gold(),
                            timestamp=datetime.now()
                        )
                        # Pedido: Mudar 🛡️ Atendente para 🎥 Parceiro
                        embed_p.add_field(name="🎥 Parceiro", value=f"{partner_member.mention if partner_member else f'<@{p_id}>'}", inline=True)
                        embed_p.add_field(name="👤 Cliente", value=f"{client_user.mention if client_user else 'Desconhecido'}", inline=True)
                        embed_p.add_field(name="💵 Venda", value=f"R$ {p_venda:.2f}", inline=True)
                        embed_p.add_field(name="📈 Comissão", value=f"**{percentStr} (R$ {p_val:.2f})**", inline=False)
                        
                        # ID Game do Parceiro
                        p_data = usuarios.get(p_id, {})
                        id_game = p_data.get("codigo", "Não Definido")
                        
                        embed_p.set_footer(text=f"ID Game: {id_game} • {datetime.now().strftime('%d/%m/%Y %H:%M')}")
                        
                        await canal_log_p.send(content=content_txt, embed=embed_p)
            except Exception as e:
                print(f"⚠️ Erro ao processar comissão na closure: {e}")

        owner_id_str = str(owner_id) if owner_id else None
        id_game = usuarios.get(owner_id_str, {}).get("codigo", "Não Definido") if owner_id_str else "Não Encontrado"



        # Criar embed de log
        fechado_em = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

        # Modificado para seguir o layout pedido: Nome Ticket | @Membro | Valor | Comprovante
        embed_log = discord.Embed(
            title=f"📦 Registro: {channel.name}",
            color=discord.Color.gold(),
            timestamp=datetime.now()
        )
        
        embed_log.add_field(name="👤 Cliente", value=f"{ticket_owner.mention if ticket_owner else 'Desconhecido'}", inline=True)
        
        embed_log.add_field(name="💲 Valor", value="A confirmar", inline=True)

        # Adicionar preview da imagem (comprovante) se existir (Logo abaixo)
        if comprovante_url:
            embed_log.set_image(url=comprovante_url)
            embed_log.set_footer(text="📸 Comprovante anexado")
        else:
             embed_log.set_footer(text="Sem comprovante detectado")
        
        # Enviar para logs da staff
        # Identificar canal de log correto
        canal_log_id = None
        if channel.topic and "Ticket de loja" in channel.topic:
            canal_log_id = config.get('ticket_logs_loja_channel_id')
        elif channel.topic and "Ticket de suporte" in channel.topic:
            canal_log_id = config.get('ticket_logs_suporte_channel_id')
        
        # Se não tiver canal específico, usa o geral
        if not canal_log_id:
            canal_log_id = config.get('ticket_logs_channel_id')

        if canal_log_id:
            logs_channel = bot.get_channel(int(canal_log_id))
            if logs_channel:
                file_bytes.seek(0)
                await logs_channel.send(embed=embed_log, file=discord.File(file_bytes, filename=filename))
                
        # Enviar para o usuário (DESATIVADO A PEDIDO)
        # if ticket_owner:
        #     try:
        #         embed_user = discord.Embed(
        #             title="📦 Pedido Entregue!",
        #             description=f"Seu atendimento no servidor **{channel.guild.name}** foi finalizado e seu pedido foi entregue com sucesso! 🎉\n\nSegue abaixo o registro das mensagens para sua conferência.",
        #             color=discord.Color.green()
        #         )
        #         embed_user.set_footer(text="Obrigado por comprar conosco! Avalie nosso atendimento no servidor.")
        #         file_bytes.seek(0)
        #         await ticket_owner.send(embed=embed_user, file=discord.File(file_bytes, filename=filename))
        #         print(f"✅ DM enviada para {ticket_owner.name}")
        #     except Exception as e:
        #         print(f"⚠️ Não foi possível enviar DM para {ticket_owner.name}: {e}")
        # else:
        #      print("⚠️ Dono do ticket não encontrado para enviar DM.")
                
        await channel.send("🔒 **Ticket fechado com sucesso! Deletando em 10 segundos...**")
    except Exception as e:
        print(f"❌ Erro ao fechar ticket: {e}")
    finally:
        await asyncio.sleep(10)
        try:
            await channel.delete()
        except:
            pass
        finally:
            canais_em_fechamento.discard(channel.id)

# --- Sistema de VIPs ---

@tasks.loop(minutes=30)
async def check_event_coupons():
    """Limpa cupons de evento expirados a cada 30 minutos"""
    global config
    if 'eventos' not in config:
        return
    
    alterado = False
    agora = datetime.now()
    expirados = []
    
    for codigo, data in config['eventos'].items():
        exp_str = data.get('expiracao')
        if exp_str:
            exp_dt = datetime.fromisoformat(exp_str)
            if agora > exp_dt:
                expirados.append(codigo)
    
    for codigo in expirados:
        del config['eventos'][codigo]
        print(f"🗑️ Cupom de evento expirado removido: {codigo}")
        alterado = True
        
    if alterado:
        try:
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4)
        except Exception as e:
            print(f"❌ Erro ao salvar limpeza de cupons: {e}")

@tasks.loop(minutes=30)
async def check_vips():
    """Verifica periodicamente se algum VIP expirou"""
    await bot.wait_until_ready()
    try:
        vips = carregar_vips()
        if not vips:
            return
            
        agora = datetime.now().timestamp()
        alterado = False
        msgs_to_send = [] # (user_id, msg)
        
        for user_id in list(vips.keys()):
            data = vips[user_id]
            expiracao_ts = data.get("expiracao", 0)
            
            if agora >= expiracao_ts:
                # VIP Expirou
                guild_id = data.get("guild_id")
                role_id = data.get("role_id")
                deletar_do_banco = False
                
                if guild_id and role_id:
                    guild = bot.get_guild(guild_id)
                    if guild:
                        member = guild.get_member(int(user_id))
                        if not member:
                            try:
                                member = await guild.fetch_member(int(user_id))
                            except: 
                                # Membro saiu do servidor, podemos deletar do banco
                                deletar_do_banco = True
                            
                        if member:
                            role = guild.get_role(role_id)
                            if role:
                                try:
                                    if role in member.roles:
                                        await member.remove_roles(role)
                                        print(f"📉 VIP expirado removido de {member.name}")
                                        msgs_to_send.append((member, f"⚠️ **Atenção:** Seu **{role.name}** expirou hoje! Renove seu VIP para continuar aproveitando os benefícios."))
                                    deletar_do_banco = True
                                except Exception as e:
                                    print(f"❌ Erro ao remover VIP expirado de {member.name}: {e}")
                                    # Não deletamos do banco para tentar novamente no próximo loop
                            else:
                                # Role não existe mais
                                deletar_do_banco = True
                    else:
                        # Bot não está mais no servidor ou ID inválido
                        # Se não achamos a guild por muito tempo, talvez remover? 
                        # Por segurança, mantemos por enquanto ou limpamos se for erro crítico
                        pass
                else:
                    deletar_do_banco = True # Dados inválidos
                
                if deletar_do_banco:
                    # Remover do banco apenas se sucesso ou irrecuperável (ex: saiu do sv)
                    del vips[user_id]
                    alterado = True
        
        if alterado:
            salvar_vips(vips)
            
        # Enviar avisos
        for member, msg in msgs_to_send:
            try:
                await member.send(msg)
            except: pass
            
    except Exception as e:
        print(f"❌ Erro no check_vips: {e}")

@tasks.loop(hours=24)
async def check_coin_expiration():
    """Verifica se as moedas de algum usuário expiraram"""
    try:
        usuarios = carregar_usuarios()
        agora = datetime.now().timestamp()
        alterado = False
        
        for u_id, data in usuarios.items():
            vencimento = data.get("data_vencimento_moedas")
            saldo = data.get("moedas", 0)
            
            if vencimento and saldo > 0:
                if agora >= vencimento:
                    # Moedas expiraram
                    usuarios[u_id]["moedas"] = 0
                    usuarios[u_id]["data_vencimento_moedas"] = None
                    alterado = True
                    
                    # Notificar usuário
                    try:
                        user = await bot.fetch_user(int(u_id))
                        if user:
                            embed = discord.Embed(
                                title="🕒 Suas Moedas Expiraram!",
                                description=f"Olá {user.name}, suas moedas acumuladas expiraram e seu saldo foi resetado.\n\nSempre utilize suas moedas antes do prazo de 30 dias!",
                                color=discord.Color.red()
                            )
                            await user.send(embed=embed)
                    except: pass
                
                # Aviso de 2 dias antes (opcional, mas bom)
                elif agora >= (vencimento - 172800) and not data.get("aviso_vencimento_enviado"):
                     try:
                        user = await bot.fetch_user(int(u_id))
                        if user:
                            embed = discord.Embed(
                                title="⚠️ Suas Moedas vencem em breve!",
                                description=f"Olá {user.name}, você possui **{saldo} moedas** que irão expirar em menos de 48 horas!\n\nUse-as agora em nossa loja para garantir seu desconto.",
                                color=discord.Color.orange()
                            )
                            await user.send(embed=embed)
                            usuarios[u_id]["aviso_vencimento_enviado"] = True
                            alterado = True
                     except: pass

        if alterado:
            salvar_usuarios(usuarios)
            
    except Exception as e:
        print(f"❌ Erro no check_coin_expiration: {e}")

@bot.tree.command(name="configurar_vip_cargo", description="Configura um cargo para um tipo de VIP")
@app_commands.describe(nome_vip="Ex: bronze, prata, ouro", cargo="O cargo correspondente")
async def configurar_vip_cargo(interaction: discord.Interaction, nome_vip: str, cargo: discord.Role):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ Apenas administradores!", ephemeral=True)
        return

    global config
    if 'vip_roles' not in config:
        config['vip_roles'] = {}
    
    config['vip_roles'][nome_vip.lower().strip()] = cargo.id
    salvar_config(config)
    
    await interaction.response.send_message(f"✅ VIP **{nome_vip}** configurado para o cargo {cargo.mention}!")
    

# --- COMANDOS DE CUPONS E PARCEIROS ---

@bot.tree.command(name="cupom_evento", description="Cria um cupom de desconto temporário para eventos")
@app_commands.describe(codigo="Código do cupom (Ex: NATAL20)", desconto="Porcentagem de desconto (Ex: 10)", duracao="Duração (Ex: 24h para 24 horas, 7d para 7 dias)")
async def cupom_evento(interaction: discord.Interaction, codigo: str, desconto: int, duracao: str):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ Sem permissão!", ephemeral=True)
        return

    global config
    if 'eventos' not in config:
        config['eventos'] = {}
    
    # Processar duração com sufixo
    duracao = duracao.strip().lower()
    try:
        if duracao.endswith('h'):
            # Horas
            numero = int(duracao[:-1])
            expiracao = datetime.now() + timedelta(hours=numero)
            tempo_txt = f"{numero} hora{'s' if numero != 1 else ''}"
        elif duracao.endswith('d'):
            # Dias
            numero = int(duracao[:-1])
            expiracao = datetime.now() + timedelta(days=numero)
            tempo_txt = f"{numero} dia{'s' if numero != 1 else ''}"
        else:
            # Fallback: tentar interpretar como horas se for só número
            numero = int(duracao)
            expiracao = datetime.now() + timedelta(hours=numero)
            tempo_txt = f"{numero} hora{'s' if numero != 1 else ''}"
    except ValueError:
        await interaction.response.send_message("❌ Formato inválido! Use formato como: 24h (horas) ou 7d (dias).", ephemeral=True)
        return
    
    config['eventos'][codigo] = {
        "desconto": desconto,
        "expiracao": expiracao.isoformat()
    }
    
    # Salvar
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4)
        await interaction.response.send_message(f"✅ Cupom **{codigo}** criado com **{desconto}%** de desconto!\nExpira em: **{tempo_txt}**.", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"❌ Erro ao salvar cupom: {e}", ephemeral=True)

@bot.tree.command(name="remover_cupom", description="Remove um código de parceiro ou cupom de evento")
@app_commands.describe(codigo="O código que deseja remover")
async def remover_cupom(interaction: discord.Interaction, codigo: str):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ Sem permissão!", ephemeral=True)
        return

    global config
    removido = False
    
    # Tentar nos parceiros
    if 'parceiros' in config and codigo in config['parceiros']:
        del config['parceiros'][codigo]
        removido = True
        
    # Tentar nos eventos
    if 'eventos' in config and codigo in config['eventos']:
        del config['eventos'][codigo]
        removido = True

    if removido:
        try:
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4)
            await interaction.response.send_message(f"✅ O código **{codigo}** foi removido do sistema.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Erro ao salvar: {e}", ephemeral=True)
    else:
        await interaction.response.send_message("❌ Código não encontrado!", ephemeral=True)

@bot.tree.command(name="adicionar_parceiro", description="Adiciona ou atualiza um código de parceiro")
@app_commands.describe(codigo="Nome do código (ex: Lobo5%)", parceiro="Membro que receberá a comissão")
async def adicionar_parceiro(interaction: discord.Interaction, codigo: str, parceiro: discord.Member):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ Apenas administradores!", ephemeral=True)
        return

    global config
    if 'parceiros' not in config:
        config['parceiros'] = {}
    
    config['parceiros'][codigo.strip()] = str(parceiro.id)
    salvar_config(config)
    
    await interaction.response.send_message(f"✅ Código **{codigo}** configurado para o parceiro {parceiro.mention}!", ephemeral=True)


# --- SISTEMA DE CLÃS ---

@bot.tree.command(name="criar_cla", description="Cria um novo clã (Apenas para quem tem o cargo Dono Clã)")
@app_commands.describe(nome_cla="Nome do seu clã", emoji="Emoji do seu clã (ex: 🔥)", cor="Cor do cargo em Hex (ex: #ff0000)")
async def criar_cla(interaction: discord.Interaction, nome_cla: str, emoji: str, cor: str):
    # ID do cargo Dono Clã fornecido pelo usuário
    ROLE_DONO_CLA_ID = 1462900859896860724
    role_dono_cla_base = interaction.guild.get_role(ROLE_DONO_CLA_ID)
    
    if not role_dono_cla_base or role_dono_cla_base not in interaction.user.roles:
        await interaction.response.send_message("❌ Você precisa do cargo **🏯 Dono Clã** para criar um clã!", ephemeral=True)
        return

    clans = carregar_clans()
    user_id = str(interaction.user.id)
    
    # Verificar se já tem clã
    if user_id in clans:
        await interaction.response.send_message("❌ Você já possui um clã registrado!", ephemeral=True)
        return

    # Validar cor
    try:
        cor_hex = cor.replace("#", "")
        role_color = discord.Color(int(cor_hex, 16))
    except:
        role_color = discord.Color.gold() # Fallback

    await interaction.response.defer(ephemeral=True)
    
    try:
        # Categorias de Clãs
        cat_text_id = 1445070619258388620
        cat_voice_id = 1463222224130674845
        
        # Data de Expiração (30 dias por padrão)
        expiracao = (datetime.now() + timedelta(days=30)).isoformat()
        
        cat_text = interaction.guild.get_channel(cat_text_id)
        cat_voice = interaction.guild.get_channel(cat_voice_id)
        
        if not cat_text or not cat_voice:
            await interaction.followup.send("❌ Uma ou mais categorias de clãs não foram encontradas!", ephemeral=True)
            return

        # Nomes formatados: 『emoji』nome
        formatted_name = f"『{emoji}』{nome_cla}"

        # Criar Cargos (Com hoist=True para serem visíveis no painel)
        role_dono = await interaction.guild.create_role(name=f"👑 Dono | {nome_cla}", color=role_color, mentionable=True, hoist=True)
        role_membro = await interaction.guild.create_role(name=f"🛡️ Membro | {nome_cla}", color=role_color, mentionable=True, hoist=True)
        
        # Posicionar cargos: Dono acima de XP/VIP, Membro abaixo de XP
        # Buscar posições de XP e VIP
        max_pos_xp_vip = 0
        min_pos_xp = 999
        
        # Verificar VIPs (para o Dono ficar acima)
        vip_roles_config = config.get('vip_roles', {})
        for v_role_id in vip_roles_config.values():
            r = interaction.guild.get_role(int(v_role_id))
            if r:
                if r.position > max_pos_xp_vip:
                    max_pos_xp_vip = r.position
                
        # Verificar XP Roles
        xp_roles_config = config.get('xp_roles', {})
        for x_role_id in xp_roles_config.values():
            r = interaction.guild.get_role(int(x_role_id))
            if r:
                if r.position > max_pos_xp_vip:
                    max_pos_xp_vip = r.position
                if r.position < min_pos_xp:
                    min_pos_xp = r.position
        
        # Se não houver cargos de XP, usa um fallback
        if min_pos_xp == 999:
            min_pos_xp = max_pos_xp_vip # Fica logo abaixo do dono se não houver XP
            
        # Tentar mover para as posições desejadas
        try:
            # Dono: Acima de tudo (XP e VIP)
            await role_dono.edit(position=max_pos_xp_vip + 1)
            # Membro: Abaixo de todos os cargos de XP
            # (Se VIPs forem ainda mais baixos, ele fica entre XP e VIP ou logo acima de VIP)
            await role_membro.edit(position=min_pos_xp - 1)
        except Exception as pos_e:
            print(f"⚠️ Erro ao posicionar cargos de clã: {pos_e}")

        # Dar cargo de dono para quem criou
        await interaction.user.add_roles(role_dono)
        
        # Permissões do canal
        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            role_dono: discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_messages=True, connect=True, speak=True),
            role_membro: discord.PermissionOverwrite(read_messages=True, send_messages=True, connect=True, speak=True),
            interaction.guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_channels=True)
        }
        
        # Criar Canais
        txt_channel = await interaction.guild.create_text_channel(name=formatted_name, category=cat_text, overwrites=overwrites)
        vc_channel = await interaction.guild.create_voice_channel(name=formatted_name, category=cat_voice, overwrites=overwrites)
        
        # Salvar no Banco
        clans[user_id] = {
            "nome": nome_cla,
            "emoji": emoji,
            "cor": cor,
            "role_dono_id": role_dono.id,
            "role_membro_id": role_membro.id,
            "txt_channel_id": txt_channel.id,
            "vc_channel_id": vc_channel.id,
            "expiracao": expiracao,
            "membros": [user_id]
        }
        salvar_clans(clans)
        
        embed = discord.Embed(
            title="🏰 Clã Criado com Sucesso!",
            description=f"Seu clã **{formatted_name}** foi estabelecido!",
            color=role_color
        )
        embed.add_field(name="👑 Cargo Dono", value=role_dono.mention, inline=True)
        embed.add_field(name="🛡️ Cargo Membro", value=role_membro.mention, inline=True)
        embed.add_field(name="💬 Canal", value=txt_channel.mention, inline=False)
        
        await interaction.followup.send(embed=embed, ephemeral=True)
        await txt_channel.send(f"🎊 Bem-vindo ao canal do clã **{formatted_name}**! {interaction.user.mention} você é o líder.")
        
    except Exception as e:
        await interaction.followup.send(f"❌ Erro ao criar clã: {e}", ephemeral=True)

@bot.tree.command(name="convidar_cla", description="Envia um convite público para entrar no seu clã")
async def convidar_cla(interaction: discord.Interaction):
    clans = carregar_clans()
    user_id = str(interaction.user.id)
    
    if user_id not in clans:
        await interaction.response.send_message("❌ Você não é dono de nenhum clã!", ephemeral=True)
        return
        
    clan_data = clans[user_id]
    nome_cla = clan_data["nome"]
    emoji = clan_data.get("emoji", "🏰")
    
    embed = discord.Embed(
        title=f"✉️ Convite para Clã: 『{emoji}』{nome_cla}",
        description=f"O clã **{nome_cla}** está recrutando novos membros!\n\nClique no botão abaixo para enviar sua solicitação ao líder {interaction.user.mention}.",
        color=discord.Color.blue()
    )
    
    view = ClanJoinView(interaction.user, clan_data) # owner, clan_data
    await interaction.response.send_message(embed=embed, view=view)

class ClanJoinView(discord.ui.View):
    def __init__(self, owner, clan_data):
        super().__init__(timeout=None)
        self.owner = owner
        self.clan_data = clan_data

    @discord.ui.button(label="Entrar no Clã", style=discord.ButtonStyle.success, emoji="🛡️")
    async def join(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Impedir que o dono ou quem já é membro peça pra entrar (opcional mas bom)
        if str(interaction.user.id) in self.clan_data["membros"]:
            await interaction.response.send_message("❌ Você já faz parte deste clã!", ephemeral=True)
            return

        await interaction.response.send_message("⏳ Sua solicitação foi enviada ao dono do clã. Aguarde a aprovação!", ephemeral=True)
        
        # Mandar DM para o dono
        try:
            embed_dm = discord.Embed(
                title="🔔 Solicitação de Entrada no Clã",
                description=f"O membro {interaction.user.mention} deseja entrar no seu clã **{self.clan_data['nome']}**.",
                color=discord.Color.blue()
            )
            view_req = ClanJoinRequestView(interaction.user, self.clan_data, self.owner)
            await self.owner.send(embed=embed_dm, view=view_req)
        except Exception as e:
            print(f"❌ Erro ao enviar DM para o dono do clã: {e}")

class ClanJoinRequestView(discord.ui.View):
    def __init__(self, target_user, clan_data, owner):
        super().__init__(timeout=None)
        self.target_user = target_user
        self.clan_data = clan_data
        self.owner = owner

    @discord.ui.button(label="Aceitar", style=discord.ButtonStyle.success)
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        clans = carregar_clans()
        owner_id = str(self.owner.id)
        
        if owner_id not in clans:
            await interaction.response.send_message("❌ Erro: Dados do clã não encontrados.", ephemeral=True)
            return
            
        # Adicionar cargos
        guild = self.owner.guild
        role_membro = guild.get_role(self.clan_data["role_membro_id"])
        member = guild.get_member(self.target_user.id)
        
        if role_membro and member:
            await member.add_roles(role_membro)
            
            # Atualizar banco
            if str(member.id) not in clans[owner_id]["membros"]:
                clans[owner_id]["membros"].append(str(member.id))
                salvar_clans(clans)
            
            # Notificar membro
            try:
                await member.send(f"✅ Sua solicitação para entrar no clã **{self.clan_data['nome']}** foi **ACEITA**!")
            except: pass
            
            # Log no canal do clã
            txt_channel = bot.get_channel(self.clan_data["txt_channel_id"])
            if txt_channel:
                await txt_channel.send(f"🎊 {member.mention} foi aceito no clã pelo líder {self.owner.mention}!")
            
            await interaction.response.send_message(f"✅ Você aceitou {member.display_name} no clã!")
            
            # Desabilitar botões
            for item in self.children:
                item.disabled = True
            await interaction.message.edit(view=self)
        else:
            await interaction.response.send_message("❌ Erro ao adicionar cargo ou encontrar membro.", ephemeral=True)

    @discord.ui.button(label="Recusar", style=discord.ButtonStyle.danger)
    async def decline(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            await self.target_user.send(f"❌ Sua solicitação para entrar no clã **{self.clan_data['nome']}** foi **RECUSADA**.")
        except: pass
        
        await interaction.response.send_message(f"❌ Você recusou a entrada de {self.target_user.display_name}.")
        
        # Desabilitar botões
        for item in self.children:
            item.disabled = True
        await interaction.message.edit(view=self)

@bot.tree.command(name="transferir_lideranca", description="Transfere a liderança do seu clã para outro membro")
@app_commands.describe(novo_lider="Membro que será o novo dono")
async def transferir_lideranca(interaction: discord.Interaction, novo_lider: discord.Member):
    clans = carregar_clans()
    old_owner_id = str(interaction.user.id)
    new_owner_id = str(novo_lider.id)
    
    if old_owner_id not in clans:
        await interaction.response.send_message("❌ Você não é dono de nenhum clã!", ephemeral=True)
        return
        
    clan_data = clans[old_owner_id]
    
    if new_owner_id not in clan_data["membros"]:
        await interaction.response.send_message("❌ O novo líder precisa ser um membro do clã!", ephemeral=True)
        return
        
    # Trocar cargos
    role_dono = interaction.guild.get_role(clan_data["role_dono_id"])
    role_membro = interaction.guild.get_role(clan_data["role_membro_id"])
    
    if role_dono:
        await interaction.user.remove_roles(role_dono)
        if role_membro:
            await interaction.user.add_roles(role_membro)
        await novo_lider.add_roles(role_dono)
        if role_membro and role_membro in novo_lider.roles:
            await novo_lider.remove_roles(role_membro)
        
    # Atualizar dados
    clans[new_owner_id] = clans.pop(old_owner_id)
    salvar_clans(clans)
    
    await interaction.response.send_message(f"👑 Liderança do clã **{clan_data['nome']}** transferida para {novo_lider.mention}!")
    
    # Avisar no canal
    txt_channel = bot.get_channel(clan_data["txt_channel_id"])
    if txt_channel:
        await txt_channel.send(f"👑 **ATENÇÃO:** {interaction.user.mention} transferiu a liderança do clã para {novo_lider.mention}!")


# --- MODAL E VIEW PARA PAINEL VIP ---


# --- NOVO COMANDO VIP CONSOLIDADO ---

class VipGlobalModal(discord.ui.Modal, title="✨ Gerenciamento VIP"):
    def __init__(self, membro: discord.Member):
        super().__init__()
        self.membro = membro

    tipo_vip = discord.ui.TextInput(
        label="Tipo do VIP",
        placeholder="Ex: vip bronze, vip ouro...",
        style=discord.TextStyle.short,
        required=True
    )
    dias = discord.ui.TextInput(
        label="Duração (Dias)",
        placeholder="Digite o número de dias (0 para 1min)",
        style=discord.TextStyle.short,
        required=True
    )

    async def on_submit(self, interaction: discord.Interaction):
        try:
            dias_int = int(self.dias.value)
        except:
            await interaction.response.send_message("❌ O campo 'Dias' deve ser um número inteiro.", ephemeral=True)
            return

        # Chamar a lógica de ativação
        await adicionar_vip_logic(interaction, self.membro, self.tipo_vip.value, dias_int)

async def adicionar_vip_logic(interaction: discord.Interaction, membro: discord.Member, tipo_vip: str, dias: int):
    global config
    chave = tipo_vip.lower().strip()
    
    # Verificar se o cargo está configurado
    if 'vip_roles' not in config or chave not in config['vip_roles']:
        msg = f"❌ O VIP '{chave}' não está configurado! Use `/configurar_vip_cargo` primeiro."
        if interaction.response.is_done():
            await interaction.followup.send(msg, ephemeral=True)
        else:
            await interaction.response.send_message(msg, ephemeral=True)
        return
        
    role_id = config['vip_roles'][chave]
    role = interaction.guild.get_role(role_id)
    
    if not role:
        msg = "❌ O cargo configurado para este VIP não existe mais no servidor."
        if interaction.response.is_done():
            await interaction.followup.send(msg, ephemeral=True)
        else:
            await interaction.response.send_message(msg, ephemeral=True)
        return
        
    # Calcular validade
    agora = datetime.now()
    if dias == 0:
        validade = agora + timedelta(minutes=1) # Teste rápido
        msg_tempo = "1 minuto (Teste)"
    else:
        validade = agora + timedelta(days=dias)
        msg_tempo = f"{dias} dias"
        
    # Salvar
    vips = carregar_vips()
    vips[str(membro.id)] = {
        "tipo": chave,
        "role_id": role_id,
        "guild_id": interaction.guild.id,
        "expiracao": validade.timestamp(),
        "data_inicio": agora.timestamp()
    }
    salvar_vips(vips)
    
    # Dar cargo
    try:
        if role not in membro.roles:
            await membro.add_roles(role)
    except Exception as e:
        msg = f"⚠️ VIP salvo, mas erro ao dar cargo (permissão?): {e}"
        if interaction.response.is_done():
            await interaction.followup.send(msg, ephemeral=True)
        else:
            await interaction.response.send_message(msg, ephemeral=True)
        return

    # Embed de confirmação (Efêmera)
    embed = discord.Embed(
        title="✨ VIP Ativado com Sucesso!",
        description=f"O membro {membro.mention} recebeu o cargo {role.mention}!",
        color=discord.Color.gold()
    )
    embed.add_field(name="📅 Duração", value=f"**{msg_tempo}**", inline=True)
    embed.add_field(name="🛑 Expira em", value=f"<t:{int(validade.timestamp())}:f>", inline=True)
    embed.set_thumbnail(url=membro.display_avatar.url)
    embed.set_footer(text=f"Ativado por {interaction.user.name}", icon_url=interaction.user.display_avatar.url)
    
    if interaction.response.is_done():
        await interaction.followup.send(embed=embed, ephemeral=True)
    else:
        await interaction.response.send_message(embed=embed, ephemeral=True)

    # Notificação via DM
    try:
        embed_dm = discord.Embed(
            title="💎 VIP Ativado!",
            description=f"Olá {membro.name}!\nSeu VIP **{chave.title()}** foi ativado no servidor **{interaction.guild.name}**.",
            color=discord.Color.purple()
        )
        embed_dm.add_field(name="⏳ Duração", value=msg_tempo, inline=True)
        embed_dm.add_field(name="📅 Expira em", value=f"<t:{int(validade.timestamp())}:f>", inline=True)
        embed_dm.set_footer(text="Aproveite seus benefícios! 🎉")
        await membro.send(embed=embed_dm)
    except: pass

@bot.tree.command(name="vip", description="Abrir a janela de gerenciamento de VIP (Admin/Staff)")
@app_commands.describe(membro="Selecione o membro para gerenciar o VIP")
async def vip_cmd(interaction: discord.Interaction, membro: discord.Member):
    # Verificar permissão (Admin ou Atendente)
    if not interaction.user.guild_permissions.administrator:
        role_atendente = discord.utils.get(interaction.guild.roles, name="🛡️Atendente")
        if not role_atendente or role_atendente not in interaction.user.roles:
            await interaction.response.send_message("❌ Você não tem permissão para gerenciar VIPs.", ephemeral=True)
            return
            
    await interaction.response.send_modal(VipGlobalModal(membro=membro))

@bot.tree.command(name="meuvip", description="Verificar o tempo restante do seu VIP")
async def meuvip(interaction: discord.Interaction):
    vips = carregar_vips()
    str_id = str(interaction.user.id)
    
    if str_id not in vips:
        await interaction.response.send_message("❌ Você não possui nenhum VIP ativo registrado.", ephemeral=True)
        return
        
    data = vips[str_id]
    tipo = data.get("tipo", "VIP").title()
    expiracao_ts = data.get("expiracao", 0)
    
    embed = discord.Embed(
        title=f"💎 Seu Status VIP ({tipo})",
        color=discord.Color.purple()
    )
    
    # Calcular dias restantes visualmente
    agora = datetime.now().timestamp()
    if agora > expiracao_ts:
        embed.description = "⚠️ Seu VIP expirou e será removido em breve."
        embed.color = discord.Color.red()
    else:
        embed.description = f"Seu benefício está ativo!\n\n📅 **Expira em:** <t:{int(expiracao_ts)}:F>\n⏳ **Relativo:** <t:{int(expiracao_ts)}:R>"
        
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="vips", description="Listar todos os VIPs ativos (Admin)")
async def lista_vips(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ Apenas administradores!", ephemeral=True)
        return
        
    vips = carregar_vips()
    if not vips:
        await interaction.response.send_message("📂 Nenhum VIP ativo no momento.", ephemeral=True)
        return
        
    desc = ""
    for u_id, data in vips.items():
        tipo = data.get("tipo", "VIP")
        exp = int(data.get("expiracao", 0))
        desc += f"• <@{u_id}> - **{tipo.title()}** (Expira <t:{exp}:R>)\n"
        
    embed = discord.Embed(
        title=f"💎 Lista de VIPs Ativos ({len(vips)})",
        description=desc if len(desc) < 4000 else desc[:4000] + "...",
        color=discord.Color.gold()
    )
    
    await interaction.response.send_message(embed=embed)


# --- SISTEMA DE SKINS CONSOLIDADO ---

class SkinGlobalModal(discord.ui.Modal, title="✨ Gerenciamento de SKINS"):
    def __init__(self, membro: discord.Member):
        super().__init__()
        self.membro = membro

    tipo_skin = discord.ui.TextInput(
        label="Nome da Skin/Item",
        placeholder="Ex: AK47, Carro STAFF, Skin Policial...",
        style=discord.TextStyle.short,
        required=True
    )

    async def on_submit(self, interaction: discord.Interaction):
        await adicionar_skin_logic(interaction, self.membro, self.tipo_skin.value)

async def adicionar_skin_logic(interaction: discord.Interaction, membro: discord.Member, tipo_skin: str):
    global config
    
    agora = datetime.now()
    skins = carregar_skins()
    
    # Se o membro já tem skins registradas, vamos adicionar à lista ou atualizar
    # Para simplificar, manteremos um registro da última skin ativada
    # Mas o usuário pediu "nome da skin, arma, carro e de mais", sugerindo múltiplos itens.
    # No entanto, para manter a consistência com o sistema anterior (vips.json style):
    skins[str(membro.id)] = {
        "tipo": tipo_skin,
        "guild_id": interaction.guild.id,
        "data_inicio": agora.timestamp()
    }
    salvar_skins(skins)
    
    embed = discord.Embed(
        title="✨ Skin Ativada com Sucesso!",
        description=f"O membro {membro.mention} teve a skin/item **{tipo_skin}** ativado no jogo!",
        color=discord.Color.blue()
    )
    embed.set_thumbnail(url=membro.display_avatar.url)
    embed.set_footer(text=f"Ativado por {interaction.user.name}", icon_url=interaction.user.display_avatar.url)
    
    if interaction.response.is_done():
        await interaction.followup.send(embed=embed, ephemeral=True)
    else:
        await interaction.response.send_message(embed=embed, ephemeral=True)

    try:
        embed_dm = discord.Embed(
            title="🧥 Skin Ativada!",
            description=f"Olá {membro.name}!\nSua skin/item **{tipo_skin}** foi ativado permanentemente no servidor **{interaction.guild.name}**.",
            color=discord.Color.blue()
        )
        embed_dm.set_footer(text="Aproveite seus novos itens no jogo! 🎭")
        await membro.send(embed=embed_dm)
    except: pass

@bot.tree.command(name="skin", description="Abrir a janela de gerenciamento de Skin (Admin/Staff)")
@app_commands.describe(membro="Selecione o membro para gerenciar a Skin")
async def skin_cmd(interaction: discord.Interaction, membro: discord.Member):
    if not interaction.user.guild_permissions.administrator:
        role_atendente = discord.utils.get(interaction.guild.roles, name="🛡️Atendente")
        if not role_atendente or role_atendente not in interaction.user.roles:
            await interaction.response.send_message("❌ Você não tem permissão para gerenciar Skins.", ephemeral=True)
            return
            
    await interaction.response.send_modal(SkinGlobalModal(membro=membro))

@bot.tree.command(name="minhasskins", description="Verificar o tempo restante das suas Skins")
async def minhasskins(interaction: discord.Interaction):
    skins = carregar_skins()
    str_id = str(interaction.user.id)
    
    if str_id not in skins:
        await interaction.response.send_message("❌ Você não possui nenhuma Skin ativa registrada.", ephemeral=True)
        return
        
    data = skins[str_id]
    tipo = data.get("tipo", "Skin/Item")
    
    embed = discord.Embed(
        title=f"🧥 Seus Itens no Jogo",
        description=f"Seu item **{tipo}** está ativo!",
        color=discord.Color.blue()
    )
        
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="itensexp", description="Listar todos os itens/skins ativos (Admin)")
async def lista_skins(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ Apenas administradores!", ephemeral=True)
        return
        
    skins = carregar_skins()
    if not skins:
        await interaction.response.send_message("📂 Nenhum item ativo no momento.", ephemeral=True)
        return
        
    desc = ""
    for u_id, data in skins.items():
        tipo = data.get("tipo", "Item")
        desc += f"• <@{u_id}> - **{tipo}**\n"
        
    embed = discord.Embed(
        title=f"🧥 Lista de Itens Ativos ({len(skins)})",
        description=desc if len(desc) < 4000 else desc[:4000] + "...",
        color=discord.Color.blue()
    )
    
    await interaction.response.send_message(embed=embed)

# --- Comandos de Configuração Efipay ---

@bot.tree.command(name="config_efipay", description="Configurar credenciais da API Efipay (Admin)")
@app_commands.describe(
    client_id="Client ID da Efipay",
    client_secret="Client Secret da Efipay",
    chave_pix="Chave PIX cadastrada na Efipay",
    cert_arquivo="Nome do arquivo .pem (ex: cert.pem)",
    ambiente="Ambiente: producao ou homologacao",
    ativar="Ativar ou desativar a integração Efipay"
)
async def configurar_efipay(
    interaction: discord.Interaction, 
    client_id: typing.Optional[str] = None, 
    client_secret: typing.Optional[str] = None,
    chave_pix: typing.Optional[str] = None,
    cert_arquivo: typing.Optional[str] = None,
    ambiente: typing.Literal["producao", "homologacao"] = "homologacao",
    ativar: typing.Optional[bool] = True
):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ Apenas administradores podem configurar a Efipay!", ephemeral=True)
        return
    
    global config
    
    # Se forneceu credenciais, salvar
    if client_id and client_secret and chave_pix and cert_arquivo:
        config["efipay_client_id"] = client_id
        config["efipay_client_secret"] = client_secret
        config["efipay_chave_pix"] = chave_pix
        config["efipay_cert_path"] = cert_arquivo
        config["efipay_ambiente"] = ambiente
        config["efipay_enabled"] = ativar
        salvar_config(config)
        
        await interaction.response.defer(ephemeral=True)
        
        # Verificar se o arquivo existe
        if not os.path.exists(os.path.join(BASE_DIR, cert_arquivo)):
            await interaction.followup.send(f"⚠️ Aviso: Credenciais salvas, mas o arquivo `{cert_arquivo}` não foi encontrado na pasta do bot!", ephemeral=True)
            return

        # Testar as credenciais fazendo uma requisição
        test_payment = await criar_pagamento_efipay(0.01, "Teste de Configuração")
        
        if test_payment:
            embed = discord.Embed(
                title="✅ Efipay Configurada com Sucesso!",
                description="As credenciais e o certificado foram validados com sucesso!",
                color=discord.Color.green()
            )
            embed.add_field(name="🆔 Client ID", value=f"||{client_id[:10]}...||", inline=True)
            embed.add_field(name="🔑 Chave PIX", value=chave_pix, inline=True)
            embed.add_field(name="📜 Certificado", value=cert_arquivo, inline=True)
            embed.add_field(name="🌐 Ambiente", value=ambiente.capitalize(), inline=True)
            embed.add_field(name="✅ Status", value="Ativa" if ativar else "Inativa", inline=False)
            embed.set_footer(text="⚠️ Mantenha essas credenciais em segredo!")
            
            await interaction.followup.send(embed=embed, ephemeral=True)
        else:
            embed = discord.Embed(
                title="⚠️ Erro ao Testar Credenciais",
                description="Houve um erro ao testar a conexão. \n\n**Possíveis Causas:**\n1. O arquivo `.pem` é inválido ou não corresponde às credenciais.\n2. O ambiente selecionado está incorreto.\n3. A Chave PIX não está vinculada a este Client ID.",
                color=discord.Color.orange()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
    
    # Se só ativou/desativou
    elif client_id is None and client_secret is None:
        config["efipay_enabled"] = ativar
        salvar_config(config)
        
        status = "✅ Ativada" if ativar else "❌ Desativada"
        embed = discord.Embed(
            title="⚙️ Status da Efipay Atualizado",
            description=f"Efipay está agora: **{status}**",
            color=discord.Color.blue()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    else:
        embed = discord.Embed(
            title="❌ Erro na Configuração",
            description="Você precisa fornecer `client_id`, `client_secret`, `chave_pix` e `cert_arquivo` para configurar a Efipay.",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="gerar_pagamento", description="Gerar pagamento PIX via Efipay para o ticket atual (Staff)")
@app_commands.describe(valor="Valor do pagamento em R$")
async def gerar_pagamento(interaction: discord.Interaction, valor: float):
    # Verificar se é staff
    role_parceiro = discord.utils.get(interaction.guild.roles, name="🎥Parceiros")
    is_staff = (role_parceiro in interaction.user.roles) or interaction.user.guild_permissions.administrator
    
    if not is_staff:
        await interaction.response.send_message("❌ Apenas staff pode gerar pagamentos!", ephemeral=True)
        return
    
    # Verificar se está em um ticket de loja
    cat_loja = config.get('ticket_category_loja_id')
    if interaction.channel.category_id != cat_loja:
        await interaction.response.send_message("❌ Este comando só pode ser usado em tickets de loja!", ephemeral=True)
        return
    
    # Verificar se Efipay está ativa
    if not config.get("efipay_enabled", False):
        await interaction.response.send_message("❌ A integração Efipay não está ativada! Use `/config_efipay` primeiro.", ephemeral=True)
        return
    
    await interaction.response.defer()
    
    # Criar pagamento
    payment_data = await criar_pagamento_efipay(valor, f"Compra STAFF - Ticket {interaction.channel.name}")
    
    if not payment_data:
        await interaction.followup.send("❌ Erro ao criar pagamento. Verifique as configurações da Efipay.", ephemeral=True)
        return
    
    # Salvar nos pagamentos pendentes
    global pagamentos_pendentes
    pagamentos_pendentes[str(interaction.channel.id)] = {
        "txid": payment_data["txid"],
        "valor": valor,
        "atendente_id": str(interaction.user.id)
    }
    
    # Gerar QR Code da imagem
    qr_code_text = payment_data["qr_code"]
    
    if payment_data.get("qr_code_base64"):
        # Usar a imagem enviada pela API se disponível
        import base64
        image_data = base64.b64decode(payment_data["qr_code_base64"].split(",")[-1])
        buffer = BytesIO(image_data)
    else:
        # Fallback para gerar QR Code localmente
        qr = qrcode.QRCode(version=1, box_size=10, border=4)
        qr.add_data(qr_code_text)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        
    buffer.seek(0)
    file = discord.File(buffer, filename="pix_efipay.png")
    
    # Criar embed
    embed = discord.Embed(
        title="💳 Pagamento via PIX - Efipay",
        description=f"**Valor:** R$ {valor:.2f}\n\nEscaneie o QR Code ou copie o código abaixo para pagar!",
        color=discord.Color.green()
    )
    embed.add_field(name="📱 Código Copia e Cola PIX", value=f"```{qr_code_text}```", inline=False)
    embed.add_field(name="🆔 ID da Transação (TXID)", value=payment_data["txid"], inline=False)
    
    embed.set_image(url="attachment://pix_efipay.png")
    embed.set_footer(text="✅ O pagamento será confirmado automaticamente!")
    
    await interaction.followup.send(embed=embed, file=file)
    
    # Notificar o atendente
    embed_staff = discord.Embed(
        title="✅ Pagamento Gerado",
        description=f"Pagamento de **R$ {valor:.2f}** gerado com sucesso!\n\nO sistema verificará automaticamente quando o cliente pagar.",
        color=discord.Color.blue()
    )
    await interaction.followup.send(embed=embed_staff, ephemeral=True)


# =====================================================
# SISTEMA DE MINI GAMES - /minigames
# 50 jogos por dia | 10 XP por vitória
# =====================================================

MINIGAMES_FILE = os.path.join(BASE_DIR, 'minigames_cooldown.json')

def carregar_minigames_data():
    if not os.path.exists(MINIGAMES_FILE):
        return {}
    with open(MINIGAMES_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except:
            return {}

def salvar_minigames_data(data):
    with open(MINIGAMES_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

def obter_jogos_restantes(user_id: str):
    """Retorna quantos jogos o usuario ainda pode jogar hoje"""
    data = carregar_minigames_data()
    user_data = data.get(user_id, {})
    ultimo_dia = user_data.get("ultimo_dia", "")
    hoje = datetime.now().strftime("%Y-%m-%d")
    
    if ultimo_dia != hoje:
        return 50  # Novo dia, reseta
    
    jogos_feitos = user_data.get("jogos_feitos", 0)
    return max(0, 50 - jogos_feitos)

def registrar_jogo(user_id: str, ganhou: bool):
    """Registra um jogo e dá XP se ganhou. Retorna (xp_ganho, jogos_restantes)"""
    data = carregar_minigames_data()
    hoje = datetime.now().strftime("%Y-%m-%d")
    
    if user_id not in data:
        data[user_id] = {"ultimo_dia": hoje, "jogos_feitos": 0, "vitorias": 0, "derrotas": 0}
    
    # Reset se for novo dia
    if data[user_id].get("ultimo_dia", "") != hoje:
        data[user_id] = {"ultimo_dia": hoje, "jogos_feitos": 0, "vitorias": 0, "derrotas": 0}
    
    data[user_id]["jogos_feitos"] = data[user_id].get("jogos_feitos", 0) + 1
    
    xp_ganho = 0
    if ganhou:
        data[user_id]["vitorias"] = data[user_id].get("vitorias", 0) + 1
        xp_ganho = 10
        # Dar XP ao usuario
        usuarios = carregar_usuarios()
        if user_id not in usuarios:
            usuarios[user_id] = {"xp": 0, "level": 0}
        usuarios[user_id]["xp"] = usuarios[user_id].get("xp", 0) + 10
        novo_nivel = usuarios[user_id]["xp"] // 500
        usuarios[user_id]["level"] = novo_nivel
        salvar_usuarios(usuarios)
    else:
        data[user_id]["derrotas"] = data[user_id].get("derrotas", 0) + 1
    
    salvar_minigames_data(data)
    restantes = max(0, 50 - data[user_id]["jogos_feitos"])
    return xp_ganho, restantes

# --- Perguntas do Quiz ---
QUIZ_PERGUNTAS = [
    {"pergunta": "Qual o maior planeta do Sistema Solar?", "opcoes": ["Terra", "Jupiter", "Saturno", "Marte"], "correta": 1},
    {"pergunta": "Quantos lados tem um hexagono?", "opcoes": ["5", "6", "7", "8"], "correta": 1},
    {"pergunta": "Qual a capital do Brasil?", "opcoes": ["Sao Paulo", "Rio de Janeiro", "Brasilia", "Salvador"], "correta": 2},
    {"pergunta": "Qual elemento quimico tem o simbolo 'O'?", "opcoes": ["Ouro", "Osmio", "Oxigenio", "Oganesson"], "correta": 2},
    {"pergunta": "Em que ano o homem pisou na Lua pela primeira vez?", "opcoes": ["1965", "1969", "1972", "1975"], "correta": 1},
    {"pergunta": "Qual o menor pais do mundo?", "opcoes": ["Monaco", "Vaticano", "San Marino", "Liechtenstein"], "correta": 1},
    {"pergunta": "Quantos ossos tem o corpo humano adulto?", "opcoes": ["196", "206", "216", "226"], "correta": 1},
    {"pergunta": "Qual a velocidade da luz em km/s (aprox.)?", "opcoes": ["150.000", "200.000", "300.000", "400.000"], "correta": 2},
    {"pergunta": "Qual o animal mais rapido do mundo?", "opcoes": ["Leopardo", "Guepardo", "Leao", "Cavalo"], "correta": 1},
    {"pergunta": "Quantas cores tem o arco-iris?", "opcoes": ["5", "6", "7", "8"], "correta": 2},
    {"pergunta": "Qual o oceano mais profundo?", "opcoes": ["Atlantico", "Indico", "Pacifico", "Artico"], "correta": 2},
    {"pergunta": "Qual o metal mais leve?", "opcoes": ["Aluminio", "Litio", "Titanio", "Magnesio"], "correta": 1},
    {"pergunta": "Qual planeta e conhecido como 'Planeta Vermelho'?", "opcoes": ["Venus", "Marte", "Jupiter", "Mercurio"], "correta": 1},
    {"pergunta": "Quantos continentes existem?", "opcoes": ["5", "6", "7", "8"], "correta": 2},
    {"pergunta": "Qual e o rio mais longo do mundo?", "opcoes": ["Amazonas", "Nilo", "Mississipi", "Yangtzé"], "correta": 1},
    {"pergunta": "Qual instrumento tem 88 teclas?", "opcoes": ["Orgao", "Piano", "Acordeao", "Sintetizador"], "correta": 1},
    {"pergunta": "Qual a formula quimica da agua?", "opcoes": ["H2O", "CO2", "NaCl", "O2"], "correta": 0},
    {"pergunta": "Quantos graus tem um circulo?", "opcoes": ["180", "270", "360", "420"], "correta": 2},
    {"pergunta": "Qual pais inventou a pizza?", "opcoes": ["Franca", "Espanha", "Italia", "Grecia"], "correta": 2},
    {"pergunta": "Qual o maior deserto do mundo?", "opcoes": ["Saara", "Antartica", "Gobi", "Kalahari"], "correta": 1},
]
# --- Views dos Mini Games ---

class MiniGameMenuView(discord.ui.View):
    """Menu principal de selecao de mini games"""
    def __init__(self, user_id: str, jogos_restantes: int):
        super().__init__(timeout=120)
        self.user_id = user_id
        self.jogos_restantes = jogos_restantes

    @discord.ui.button(label="🧠 Quiz", style=discord.ButtonStyle.primary, custom_id="mg_quiz", row=0)
    async def quiz_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if str(interaction.user.id) != self.user_id:
            return await interaction.response.send_message("❌ Este menu nao e seu!", ephemeral=True)
        restantes = obter_jogos_restantes(self.user_id)
        if restantes <= 0:
            return await interaction.response.send_message("❌ Voce ja usou todos os 50 jogos de hoje! Volte amanha.", ephemeral=True)
        await iniciar_quiz(interaction, self.user_id)

    @discord.ui.button(label="🎲 Dados", style=discord.ButtonStyle.primary, custom_id="mg_dados", row=0)
    async def dados_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if str(interaction.user.id) != self.user_id:
            return await interaction.response.send_message("❌ Este menu nao e seu!", ephemeral=True)
        restantes = obter_jogos_restantes(self.user_id)
        if restantes <= 0:
            return await interaction.response.send_message("❌ Voce ja usou todos os 50 jogos de hoje! Volte amanha.", ephemeral=True)
        await iniciar_dados(interaction, self.user_id)

    @discord.ui.button(label="🔢 Adivinhe o Numero", style=discord.ButtonStyle.primary, custom_id="mg_numero", row=0)
    async def numero_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if str(interaction.user.id) != self.user_id:
            return await interaction.response.send_message("❌ Este menu nao e seu!", ephemeral=True)
        restantes = obter_jogos_restantes(self.user_id)
        if restantes <= 0:
            return await interaction.response.send_message("❌ Voce ja usou todos os 50 jogos de hoje! Volte amanha.", ephemeral=True)
        await iniciar_numero(interaction, self.user_id)

    @discord.ui.button(label="✂️ Pedra Papel Tesoura", style=discord.ButtonStyle.primary, custom_id="mg_ppt", row=1)
    async def ppt_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if str(interaction.user.id) != self.user_id:
            return await interaction.response.send_message("❌ Este menu nao e seu!", ephemeral=True)
        restantes = obter_jogos_restantes(self.user_id)
        if restantes <= 0:
            return await interaction.response.send_message("❌ Voce ja usou todos os 50 jogos de hoje! Volte amanha.", ephemeral=True)
        await iniciar_ppt(interaction, self.user_id)

    @discord.ui.button(label="🃏 Cara ou Coroa", style=discord.ButtonStyle.primary, custom_id="mg_moeda", row=1)
    async def moeda_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if str(interaction.user.id) != self.user_id:
            return await interaction.response.send_message("❌ Este menu nao e seu!", ephemeral=True)
        restantes = obter_jogos_restantes(self.user_id)
        if restantes <= 0:
            return await interaction.response.send_message("❌ Voce ja usou todos os 50 jogos de hoje! Volte amanha.", ephemeral=True)
        class iniciar_moeda:
            class Interaction:
                pass
            def __init__(self, interaction: Interaction, user_id: str):
                pass
        await iniciar_moeda(interaction, self.user_id)


# --- Comando /minigames ---
@bot.tree.command(name="minigames", description="Acesse os mini games e ganhe XP!")
async def minigames(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    restantes = obter_jogos_restantes(user_id)

    embed = discord.Embed(
        title="🎮 Mini Games - STAFF",
        description=(
            f"Bem-vindo aos Mini Games, {interaction.user.mention}!\n\n"
            f"Ganhe **10 XP** por vitória, com limite de **50 jogos por dia**.\n\n"
            f"📊 **Jogos restantes hoje:** `{restantes}/50`\n\n"
            "Escolha um jogo abaixo para começar:"
        ),
        color=discord.Color.purple()
    )
    embed.add_field(name="🧠 Quiz", value="Responda perguntas gerais", inline=True)
    embed.add_field(name="🎲 Dados", value="Role os dados e torça!", inline=True)
    embed.add_field(name="🔢 Adivinhe o Número", value="Acerte o número secreto (1-10)", inline=True)
    embed.add_field(name="✂️ Pedra Papel Tesoura", value="Bata o bot no clássico jogo", inline=True)
    embed.add_field(name="🃏 Cara ou Coroa", value="50% de chance de ganhar", inline=True)
    embed.set_footer(text="Os jogos resetam à meia-noite!")

    if restantes <= 0:
        embed.color = discord.Color.red()
        embed.set_footer(text="⛔ Você usou todos os 50 jogos de hoje! Volte amanhã.")
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    view = MiniGameMenuView(user_id, restantes)
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


# --- QUIZ ---
class QuizView(discord.ui.View):
    def __init__(self, user_id: str, pergunta_data: dict):
        super().__init__(timeout=30)
        self.user_id = user_id
        self.pergunta_data = pergunta_data
        self.respondido = False
        
        for i, opcao in enumerate(pergunta_data["opcoes"]):
            btn = discord.ui.Button(
                label=opcao, 
                style=discord.ButtonStyle.secondary, 
                custom_id=f"quiz_{i}_{random.randint(1000,9999)}",
                row=i // 2
            )
            btn.callback = self.criar_callback(i)
            self.add_item(btn)
    
    def criar_callback(self, index):
        async def callback(interaction: discord.Interaction):
            if str(interaction.user.id) != self.user_id:
                return await interaction.response.send_message("❌ Este quiz nao e seu!", ephemeral=True)
            if self.respondido:
                return await interaction.response.send_message("❌ Voce ja respondeu!", ephemeral=True)
            self.respondido = True
            
            correta = self.pergunta_data["correta"]
            ganhou = index == correta
            xp, restantes = registrar_jogo(self.user_id, ganhou)
            
            if ganhou:
                embed = discord.Embed(
                    title="✅ Resposta Correta!",
                    description=f"Parabens! Voce ganhou **+{xp} XP**!\n\n🎮 Jogos restantes hoje: **{restantes}/50**",
                    color=discord.Color.green()
                )
            else:
                opcao_certa = self.pergunta_data["opcoes"][correta]
                embed = discord.Embed(
                    title="❌ Resposta Errada!",
                    description=f"A resposta correta era: **{opcao_certa}**\n\n🎮 Jogos restantes hoje: **{restantes}/50**",
                    color=discord.Color.red()
                )
            
            for item in self.children:
                item.disabled = True
            
            await interaction.response.edit_message(embed=embed, view=self)
            self.stop()
        return callback

async def iniciar_quiz(interaction: discord.Interaction, user_id: str):
    pergunta = random.choice(QUIZ_PERGUNTAS)
    
    embed = discord.Embed(
        title="🧠 Quiz - Teste seus conhecimentos!",
        description=f"**{pergunta['pergunta']}**",
        color=discord.Color.blue()
    )
    embed.set_footer(text="Voce tem 30 segundos para responder!")
    
    view = QuizView(user_id, pergunta)
    await interaction.response.edit_message(embed=embed, view=view)


# --- DADOS ---
class DadosApostaView(discord.ui.View):
    def __init__(self, user_id: str):
        super().__init__(timeout=30)
        self.user_id = user_id

    @discord.ui.button(label="⬆️ ALTO (4, 5, 6)", style=discord.ButtonStyle.green, custom_id="dados_alto_x")
    async def alto_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if str(interaction.user.id) != self.user_id:
            return await interaction.response.send_message("❌ Este jogo nao e seu!", ephemeral=True)
        await jogar_dados(interaction, self.user_id, "alto")

    @discord.ui.button(label="⬇️ BAIXO (1, 2, 3)", style=discord.ButtonStyle.red, custom_id="dados_baixo_x")
    async def baixo_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if str(interaction.user.id) != self.user_id:
            return await interaction.response.send_message("❌ Este jogo nao e seu!", ephemeral=True)
        await jogar_dados(interaction, self.user_id, "baixo")

    @discord.ui.button(label="🎯 PAR", style=discord.ButtonStyle.primary, custom_id="dados_par_x")
    async def par_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if str(interaction.user.id) != self.user_id:
            return await interaction.response.send_message("❌ Este jogo nao e seu!", ephemeral=True)
        await jogar_dados(interaction, self.user_id, "par")

    @discord.ui.button(label="🎯 IMPAR", style=discord.ButtonStyle.primary, custom_id="dados_impar_x")
    async def impar_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if str(interaction.user.id) != self.user_id:
            return await interaction.response.send_message("❌ Este jogo nao e seu!", ephemeral=True)
        await jogar_dados(interaction, self.user_id, "impar")

async def iniciar_dados(interaction: discord.Interaction, user_id: str):
    embed = discord.Embed(
        title="🎲 Jogo de Dados",
        description="O bot vai rolar um dado de 6 lados!\nEscolha sua aposta:",
        color=discord.Color.gold()
    )
    embed.add_field(name="⬆️ Alto", value="Resultado sera 4, 5 ou 6", inline=True)
    embed.add_field(name="⬇️ Baixo", value="Resultado sera 1, 2 ou 3", inline=True)
    embed.add_field(name="🎯 Par/Impar", value="Resultado sera par ou impar", inline=False)
    
    view = DadosApostaView(user_id)
    await interaction.response.edit_message(embed=embed, view=view)

async def jogar_dados(interaction: discord.Interaction, user_id: str, aposta: str):
    dado = random.randint(1, 6)
    dados_emoji = {1: "⚀", 2: "⚁", 3: "⚂", 4: "⚃", 5: "⚄", 6: "⚅"}
    
    ganhou = False
    if aposta == "alto" and dado >= 4:
        ganhou = True
    elif aposta == "baixo" and dado <= 3:
        ganhou = True
    elif aposta == "par" and dado % 2 == 0:
        ganhou = True
    elif aposta == "impar" and dado % 2 != 0:
        ganhou = True
    
    xp, restantes = registrar_jogo(user_id, ganhou)
    
    aposta_texto = {"alto": "Alto (4-6)", "baixo": "Baixo (1-3)", "par": "Par", "impar": "Impar"}
    
    if ganhou:
        embed = discord.Embed(
            title=f"🎲 Dado: {dados_emoji[dado]} ({dado})",
            description=f"Sua aposta: **{aposta_texto[aposta]}**\n\n✅ **Voce ganhou! +{xp} XP**\n\n🎮 Jogos restantes: **{restantes}/50**",
            color=discord.Color.green()
        )
    else:
        embed = discord.Embed(
            title=f"🎲 Dado: {dados_emoji[dado]} ({dado})",
            description=f"Sua aposta: **{aposta_texto[aposta]}**\n\n❌ **Voce perdeu!**\n\n🎮 Jogos restantes: **{restantes}/50**",
            color=discord.Color.red()
        )
    
    await interaction.response.edit_message(embed=embed, view=None)


# --- ADIVINHE O NUMERO ---
class NumeroView(discord.ui.View):
    def __init__(self, user_id: str, numero_secreto: int, tentativas: int = 3):
        super().__init__(timeout=60)
        self.user_id = user_id
        self.numero_secreto = numero_secreto
        self.tentativas = tentativas
        self.finalizado = False
    
    @discord.ui.button(label="Chutar Numero", style=discord.ButtonStyle.green, custom_id="numero_chutar_x", emoji="🔢")
    async def chutar_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if str(interaction.user.id) != self.user_id:
            return await interaction.response.send_message("❌ Este jogo nao e seu!", ephemeral=True)
        if self.finalizado:
            return
        modal = NumeroModal(self)
        await interaction.response.send_modal(modal)

class NumeroModal(discord.ui.Modal, title="🔢 Adivinhe o Numero"):
    numero = discord.ui.TextInput(
        label="Digite um numero de 1 a 20",
        placeholder="Ex: 12",
        max_length=2,
        required=True
    )
    
    def __init__(self, game_view: NumeroView):
        super().__init__()
        self.game_view = game_view
    
    async def on_submit(self, interaction: discord.Interaction):
        if self.game_view.finalizado:
            return await interaction.response.send_message("❌ Jogo ja finalizado!", ephemeral=True)
            
        try:
            chute = int(self.numero.value)
        except ValueError:
            return await interaction.response.send_message("❌ Digite um numero valido!", ephemeral=True)
        
        if chute < 1 or chute > 20:
            return await interaction.response.send_message("❌ O numero deve ser entre 1 e 20!", ephemeral=True)
        
        self.game_view.tentativas -= 1
        secreto = self.game_view.numero_secreto
        
        if chute == secreto:
            self.game_view.finalizado = True
            xp, restantes = registrar_jogo(self.game_view.user_id, True)
            embed = discord.Embed(
                title="🎉 Acertou!",
                description=f"O numero era **{secreto}**! Voce acertou!\n\n✅ **+{xp} XP**\n🎮 Jogos restantes: **{restantes}/50**",
                color=discord.Color.green()
            )
            await interaction.response.edit_message(embed=embed, view=None)
        elif self.game_view.tentativas <= 0:
            self.game_view.finalizado = True
            _, restantes = registrar_jogo(self.game_view.user_id, False)
            embed = discord.Embed(
                title="💀 Tentativas esgotadas!",
                description=f"O numero era **{secreto}**!\n\n❌ Voce perdeu!\n🎮 Jogos restantes: **{restantes}/50**",
                color=discord.Color.red()
            )
            await interaction.response.edit_message(embed=embed, view=None)
        else:
            dica = "⬆️ O numero e **MAIOR**!" if secreto > chute else "⬇️ O numero e **MENOR**!"
            embed = discord.Embed(
                title="🔢 Adivinhe o Numero (1-20)",
                description=f"Seu chute: **{chute}**\n{dica}\n\n🔄 Tentativas restantes: **{self.game_view.tentativas}**",
                color=discord.Color.gold()
            )
            await interaction.response.edit_message(embed=embed, view=self.game_view)

async def iniciar_numero(interaction: discord.Interaction, user_id: str):
    numero = random.randint(1, 20)
    
    embed = discord.Embed(
        title="🔢 Adivinhe o Numero (1-20)",
        description="Eu pensei em um numero de **1 a 20**!\nVoce tem **3 tentativas** para acertar.\n\nClique no botao para chutar!",
        color=discord.Color.purple()
    )
    embed.set_footer(text="A cada tentativa voce recebera uma dica!")
    
    view = NumeroView(user_id, numero)
    await interaction.response.edit_message(embed=embed, view=view)


# --- PEDRA PAPEL TESOURA ---
class PPTView(discord.ui.View):
    def __init__(self, user_id: str):
        super().__init__(timeout=30)
        self.user_id = user_id
        self.jogado = False

    @discord.ui.button(label="Pedra", style=discord.ButtonStyle.secondary, custom_id="ppt_pedra_x", emoji="🪨")
    async def pedra_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if str(interaction.user.id) != self.user_id:
            return await interaction.response.send_message("❌ Este jogo nao e seu!", ephemeral=True)
        await jogar_ppt(interaction, self.user_id, "pedra", self)

    @discord.ui.button(label="Papel", style=discord.ButtonStyle.secondary, custom_id="ppt_papel_x", emoji="📄")
    async def papel_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if str(interaction.user.id) != self.user_id:
            return await interaction.response.send_message("❌ Este jogo nao e seu!", ephemeral=True)
        await jogar_ppt(interaction, self.user_id, "papel", self)

    @discord.ui.button(label="Tesoura", style=discord.ButtonStyle.secondary, custom_id="ppt_tesoura_x", emoji="✂️")
    async def tesoura_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if str(interaction.user.id) != self.user_id:
            return await interaction.response.send_message("❌ Este jogo nao e seu!", ephemeral=True)
        await jogar_ppt(interaction, self.user_id, "tesoura", self)

async def jogar_ppt(interaction: discord.Interaction, user_id: str, escolha_user: str, view: PPTView):
    if view.jogado:
        return await interaction.response.send_message("❌ Voce ja jogou!", ephemeral=True)
    view.jogado = True
    
    opcoes = ["pedra", "papel", "tesoura"]
    escolha_bot = random.choice(opcoes)
    
    emojis = {"pedra": "🪨", "papel": "📄", "tesoura": "✂️"}
    
    # Determinar vencedor
    if escolha_user == escolha_bot:
        # Empate = derrota (nao ganha XP)
        resultado = "empate"
        ganhou = False
    elif (escolha_user == "pedra" and escolha_bot == "tesoura") or \
         (escolha_user == "papel" and escolha_bot == "pedra") or \
         (escolha_user == "tesoura" and escolha_bot == "papel"):
        resultado = "vitoria"
        ganhou = True
    else:
        resultado = "derrota"
        ganhou = False
    
    xp, restantes = registrar_jogo(user_id, ganhou)
    
    if resultado == "vitoria":
        embed = discord.Embed(
            title="✂️ Pedra, Papel, Tesoura",
            description=(
                f"Voce: {emojis[escolha_user]} **{escolha_user.title()}**\n"
                f"Bot: {emojis[escolha_bot]} **{escolha_bot.title()}**\n\n"
                f"✅ **Voce venceu! +{xp} XP**\n🎮 Jogos restantes: **{restantes}/50**"
            ),
            color=discord.Color.green()
        )
    elif resultado == "empate":
        embed = discord.Embed(
            title="✂️ Pedra, Papel, Tesoura",
            description=(
                f"Voce: {emojis[escolha_user]} **{escolha_user.title()}**\n"
                f"Bot: {emojis[escolha_bot]} **{escolha_bot.title()}**\n\n"
                f"🤝 **Empate! Nenhum XP ganho.**\n🎮 Jogos restantes: **{restantes}/50**"
            ),
            color=discord.Color.gold()
        )
    else:
        embed = discord.Embed(
            title="✂️ Pedra, Papel, Tesoura",
            description=(
                f"Voce: {emojis[escolha_user]} **{escolha_user.title()}**\n"
                f"Bot: {emojis[escolha_bot]} **{escolha_bot.title()}**\n\n"
                f"❌ **Voce perdeu!**\n🎮 Jogos restantes: **{restantes}/50**"
            ),
            color=discord.Color.red()
        )

    await interaction.response.edit_message(embed=embed, view=None)

async def iniciar_ppt(interaction: discord.Interaction, user_id: str):
    embed = discord.Embed(
        title="✂️ Pedra, Papel, Tesoura",
        description="Escolha sua jogada contra o bot!\n\n🪨 **Pedra** vence Tesoura\n📄 **Papel** vence Pedra\n✂️ **Tesoura** vence Papel\n\n⚠️ Empate = nenhum XP",
        color=discord.Color.blue()
    )
    
    view = PPTView(user_id)
    await interaction.response.edit_message(embed=embed, view=view)


# --- CARA OU COROA ---
class MoedaView(discord.ui.View):
    def __init__(self, user_id: str):
        super().__init__(timeout=30)
        self.user_id = user_id
        self.jogado = False

    @discord.ui.button(label="😎 Cara", style=discord.ButtonStyle.primary, custom_id="moeda_cara_x")
    async def cara_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if str(interaction.user.id) != self.user_id:
            return await interaction.response.send_message("❌ Este jogo nao e seu!", ephemeral=True)
        await jogar_moeda(interaction, self.user_id, "cara", self)

    @discord.ui.button(label="🦅 Coroa", style=discord.ButtonStyle.primary, custom_id="moeda_coroa_x")
    async def coroa_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if str(interaction.user.id) != self.user_id:
            return await interaction.response.send_message("❌ Este jogo nao e seu!", ephemeral=True)
        await jogar_moeda(interaction, self.user_id, "coroa", self)

async def jogar_moeda(interaction: discord.Interaction, user_id: str, escolha: str, view: MoedaView):
    if view.jogado:
        return await interaction.response.send_message("❌ Voce ja jogou!", ephemeral=True)
    view.jogado = True
    
    resultado = random.choice(["cara", "coroa"])
    emojis = {"cara": "😎", "coroa": "🦅"}
    
    ganhou = escolha == resultado
    xp, restantes = registrar_jogo(user_id, ganhou)
    
    if ganhou:
        embed = discord.Embed(
            title=f"🃏 Cara ou Coroa - {emojis[resultado]} {resultado.title()}!",
            description=f"Sua escolha: {emojis[escolha]} **{escolha.title()}**\n\n✅ **Voce acertou! +{xp} XP**\n🎮 Jogos restantes: **{restantes}/50**",
            color=discord.Color.green()
        )
    else:
        embed = discord.Embed(
            title=f"🃏 Cara ou Coroa - {emojis[resultado]} {resultado.title()}!",
            description=f"Sua escolha: {emojis[escolha]} **{escolha.title()}**\n\n❌ **Errou! Sem XP dessa vez.**\n🎮 Jogos restantes: **{restantes}/50**",
            color=discord.Color.red()
        )
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="aviso", description="📢 Envia um aviso profissional com embed estilizado")
@app_commands.describe(
    mensagem="A mensagem que será enviada (use \\n para pular linha)",
    titulo="O título do aviso (Padrão: AVISO AOS MEMBROS)",
    imagem="URL de uma imagem ou banner para o aviso",
    mencionar="Escolha o tipo de menção (Padrão: Nenhum)"
)
@app_commands.choices(mencionar=[
    app_commands.Choice(name="🔔 Mencionar: @here", value="here"),
    app_commands.Choice(name="🔇 Não mencionar", value="none")
])
async def aviso(interaction: discord.Interaction, mensagem: str, titulo: str = "📢 ┃ AVISO AOS MEMBROS", imagem: str = None, mencionar: str = "none"):
    # Verificar permissão de administrador
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message(
            "❌ Você não tem permissão para usar este comando!",
            ephemeral=True
        )
        return

    # Buscar canal de avisos automaticamente
    guild = interaction.guild
    canal_avisos = None
    palavras_chave = ["aviso", "avisos", "comunicado", "announcement"]
    
    # Tenta encontrar em categorias específicas
    for category in guild.categories:
        nome_cat = normalizar_nome(category.name)
        if any(x in nome_cat for x in ["importante", "informacao", "staff"]):
            for channel in category.text_channels:
                nome_ch = normalizar_nome(channel.name)
                if any(p in nome_ch for p in palavras_chave):
                    canal_avisos = channel
                    break
            if canal_avisos: break
    
    # Se não achou, tenta no servidor todo
    if not canal_avisos:
        for channel in guild.text_channels:
            nome_ch = normalizar_nome(channel.name)
            if any(p in nome_ch for p in palavras_chave):
                canal_avisos = channel
                break
                
    # Se ainda não achou, usa o canal atual
    if not canal_avisos:
        canal_avisos = interaction.channel

    # Criar embed PREMIUM
    embed = discord.Embed(
        title=titulo,
        description="",
        color=0xFFFFFF, # Branco Puro
        timestamp=datetime.now()
    )
    
    # Formatação da descrição com divisores profissionais e texto GRANDE (White Header)
    divisor = "━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    embed.description = f"{divisor}\n\n### {mensagem}\n\n{divisor}"

    embed.set_author(
        name=f"Publicado por: {interaction.user.display_name}",
        icon_url=interaction.user.avatar.url if interaction.user.avatar else interaction.user.default_avatar.url
    )
    
    if guild.icon:
        embed.set_thumbnail(url=guild.icon.url)
    
    if imagem:
        # Validar se é uma URL de imagem básica
        if imagem.startswith("http"):
            embed.set_image(url=imagem)
    
    embed.set_footer(
        text=f"© {guild.name} • Sistema de Notificações Oficiais",
        icon_url=bot.user.avatar.url if bot.user.avatar else None
    )

    # Definir conteúdo da menção
    content = ""
    if mencionar == "everyone":
        content = "@everyone"
    elif mencionar == "here":
        content = "@here"

    # Enviar o aviso
    try:
        await canal_avisos.send(content=content, embed=embed)
        await interaction.response.send_message(f"✅ Seu aviso foi publicado com sucesso no canal {canal_avisos.mention}!", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"❌ Erro ao enviar aviso: {e}", ephemeral=True)

@bot.command(name="aviso")
async def aviso_prefix(ctx, *, mensagem: str = None):
    # Verificar permissão
    if not ctx.author.guild_permissions.administrator:
        return

    if not mensagem:
        await ctx.send("❓ Use: `!aviso [mensagem]`", delete_after=5)
        return

    # Usar a lógica profissional do slash command por baixo
    guild = ctx.guild
    canal_avisos = None
    
    # Busca rápida de canal
    for category in guild.categories:
        if "importante" in normalizar_nome(category.name):
            for channel in category.text_channels:
                if any(p in normalizar_nome(channel.name) for p in ["aviso", "avisos"]):
                    canal_avisos = channel
                    break
            if canal_avisos: break

    if not canal_avisos:
        for channel in guild.text_channels:
            if any(p in normalizar_nome(channel.name) for p in ["aviso", "avisos"]):
                canal_avisos = channel
                break
    
    if not canal_avisos:
        canal_avisos = ctx.channel

    # Deletar mensagem do comando
    try: await ctx.message.delete()
    except: pass

    # Embed simplificado mas profissional para o comando de prefixo
    embed = discord.Embed(
        title="📢 ┃ AVISO AOS MEMBROS",
        description=f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n### {mensagem}\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        color=0xFFFFFF, # Branco Puro
        timestamp=datetime.now()
    )
    embed.set_author(name=f"Admin: {ctx.author.display_name}", icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
    if guild.icon: embed.set_thumbnail(url=guild.icon.url)
    embed.set_footer(text=f"© {guild.name} • Notificações", icon_url=bot.user.avatar.url if bot.user.avatar else None)

    await canal_avisos.send(content="", embed=embed)

# =====================================================
# SISTEMA DE IAS - /geraria & /encerrar_ias
# =====================================================

# --- Sistema de IA Removido ---


# --- Evento de Mensagem: captura chat nos canais de IA ---
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    # Processar comandos normais
    await bot.process_commands(message)

# =====================================================
# NOVOS COMANDOS ADICIONADOS
# =====================================================

@bot.hybrid_command(name="youtube", aliases=["tuber"], description="Inicia o vídeo diretamente do link do YouTube")
async def youtube_cmd(ctx, *, link: str):
    # Regex para extrair o ID limpo do vídeo e ignorar outros textos
    video_id = None
    match = re.search(r'(?:v=|/)([0-9A-Za-z_-]{11})', link)
    if match:
        video_id = match.group(1)
    
    if not video_id:
        return await ctx.send("❌ Por favor, envie um link normal válido do YouTube. Exemplo: `https://www.youtube.com/watch?v=...`")

    video_url = f"https://www.youtube.com/watch?v={video_id}"

    # Botão opcional para abrir no navegador
    view = discord.ui.View()
    view.add_item(discord.ui.Button(label="Ver no Navegador", url=video_url, style=discord.ButtonStyle.link, emoji="🔗"))

    # Mandar a URL limpa garante que o Discord vai iniciar o próprio player embutido no chat
    await ctx.send(
        content=f"📺 **Painel YouTube de {ctx.author.mention}**\n▶️ O vídeo está pronto para iniciar logo abaixo!\n\n{video_url}",
        view=view
    )

import uuid

pending_script_requests = {}

class AcceptScriptView(discord.ui.View):
    def __init__(self, requester_id: int, request_id: str):
        super().__init__(timeout=None)
        self.requester_id = requester_id
        self.request_id = request_id

    @discord.ui.button(label="Aceitar", style=discord.ButtonStyle.success, emoji="✅", custom_id="accept_script_btn")
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Disable the button for the user who clicked
        button.disabled = True
        button.label = "Aceito por você"
        await interaction.response.edit_message(view=self)
        
        # Notify the user who requested the script
        try:
            requester = await interaction.client.fetch_user(self.requester_id)
            import random
            chaves = ["lambo057", "lambo506", "lambo641", "lambo321", "lambo630", "lambo703"]
            chave_escolhida = random.choice(chaves)
            script_str = 'loadstring(game:HttpGet("https://raw.githubusercontent.com/gabriel62sx/lamborguini/refs/heads/main/README.md"))()'
            
            embed_msg = discord.Embed(
                title="✅ Pedido de Script Aceito!",
                description=f"Seu pedido no servidor **{interaction.guild.name if interaction.guild else 'Joker'}** foi aceito por {interaction.user.mention}!",
                color=discord.Color.green()
            )
            embed_msg.add_field(name="📜 Script", value=f"```lua\n{script_str}\n```", inline=False)
            embed_msg.add_field(name="🔑 Chave de Acesso", value=f"`{chave_escolhida}`", inline=False)
            embed_msg.set_footer(text="Aproveite o seu script e não o compartilhe!")

            await requester.send(embed=embed_msg)
        except Exception as e:
            print(f"Erro ao notificar usuário: {e}")
            
        # Notify the staff who accepted
        try:
            await interaction.user.send(f"✅ Você aceitou o pedido de script de <@{self.requester_id}>. O script e a chave já foram enviados automaticamente para a DM dele!")
        except:
            pass
            
        # Expire other notifications
        if self.request_id in pending_script_requests:
            messages = pending_script_requests.pop(self.request_id)
            for staff_id, msg_id in messages:
                if staff_id != interaction.user.id:
                    try:
                        staff_user = await interaction.client.fetch_user(staff_id)
                        dm_channel = await staff_user.create_dm()
                        msg = await dm_channel.fetch_message(msg_id)
                        if msg:
                            # Disable buttons for other staff
                            for item in self.children:
                                item.disabled = True
                                if isinstance(item, discord.ui.Button):
                                    item.label = f"Aceito por {interaction.user.name}"
                            await msg.edit(view=self)
                    except Exception as e:
                        pass

class ScriptKeyView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Gerar Script", style=discord.ButtonStyle.success, emoji="📜", custom_id="gerar_script_btn")
    async def gerar_script(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Acknowledge the interaction first to prevent timeout
        await interaction.response.defer(ephemeral=True)
        
        # Verificar se o usuário que clicou JÁ É STAFF!
        is_user_staff = False
        if interaction.user.guild_permissions.administrator or interaction.user.id == interaction.guild.owner_id:
            is_user_staff = True
        else:
            for role in interaction.user.roles:
                role_name = role.name.lower()
                if "adm" in role_name or "dono" in role_name or "atendente" in role_name or "staff" in role_name:
                    is_user_staff = True
                    break
                    
        if is_user_staff:
            # Se for staff, manda direto!
            import random
            chaves = ["lambo057", "lambo506", "lambo641", "lambo321", "lambo630", "lambo703"]
            chave_escolhida = random.choice(chaves)
            script_str = 'loadstring(game:HttpGet("https://raw.githubusercontent.com/gabriel62sx/lamborguini/refs/heads/main/README.md"))()'
            
            embed_msg = discord.Embed(
                title="✅ Pedido de Script Aceito!",
                description=f"Aqui está o seu script, {interaction.user.mention}!",
                color=discord.Color.green()
            )
            embed_msg.add_field(name="📜 Script", value=f"```lua\n{script_str}\n```", inline=False)
            embed_msg.add_field(name="🔑 Chave de Acesso", value=f"`{chave_escolhida}`", inline=False)
            embed_msg.set_footer(text="Aproveite o seu script e não o compartilhe!")

            await interaction.followup.send(embed=embed_msg, ephemeral=True)
            return

        staff_members = []
        for member in interaction.guild.members:
            if member.bot: continue
            is_staff = False
            
            # Check for Administrator permission or server owner
            if member.guild_permissions.administrator or member.id == interaction.guild.owner_id:
                is_staff = True
            else:
                # Check for specific roles
                for role in member.roles:
                    role_name = role.name.lower()
                    if "adm" in role_name or "dono" in role_name or "atendente" in role_name or "staff" in role_name:
                        is_staff = True
                        break
                        
            if is_staff:
                staff_members.append(member)
        
        if not staff_members:
            await interaction.followup.send("❌ Não encontrei nenhum staff disponível no momento.", ephemeral=True)
            return
            
        # Generate a unique ID for this request
        request_id = str(uuid.uuid4())
        messages_sent = []
        
        embed_staff = discord.Embed(
            title="🔔 Novo Pedido de Script",
            description=f"O usuário {interaction.user.mention} (`{interaction.user.name}`) solicitou a geração de um script no servidor **{interaction.guild.name}**.\n\nClique no botão abaixo para atender este pedido.",
            color=discord.Color.blue()
        )
        embed_staff.set_thumbnail(url=interaction.user.avatar.url if interaction.user.avatar else interaction.user.default_avatar.url)
        embed_staff.set_footer(text=f"ID do Usuário: {interaction.user.id}")
        
        view_accept = AcceptScriptView(interaction.user.id, request_id)
        
        # Send DMs to all identified staff members
        for staff in staff_members:
            try:
                msg = await staff.send(embed=embed_staff, view=view_accept)
                messages_sent.append((staff.id, msg.id))
            except Exception as e:
                # Some staff might have DMs disabled
                pass
                
        if messages_sent:
            # Store the message IDs to expire them later if someone accepts
            pending_script_requests[request_id] = messages_sent
            await interaction.followup.send("✅ Seu pedido foi enviado para os administradores. Aguarde o retorno na sua DM!", ephemeral=True)
        else:
            await interaction.followup.send("❌ Não foi possível contatar a Staff (Possivelmente estão com as DMs fechadas). Tente chamar em um ticket.", ephemeral=True)


@bot.tree.command(name="script", description="📜 Mostra o script oficial do servidor")
@app_commands.default_permissions(administrator=True)
async def script_cmd(interaction: discord.Interaction):
    import random
    chaves = ["lambo057", "lambo506", "lambo641", "lambo321", "lambo630", "lambo703"]
    chave_escolhida = random.choice(chaves)
    script_str = 'loadstring(game:HttpGet("https://raw.githubusercontent.com/gabriel62sx/lamborguini/refs/heads/main/README.md"))()'
    
    embed = discord.Embed(
        title="📜 ┃ SISTEMA DE SCRIPT - OFICIAL",
        description=(
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"🚀 **Script Carregado com Sucesso!**\n\n"
            f"📜 **Script:**\n```lua\n{script_str}\n```\n"
            f"🔑 **Chave de Acesso:** `{chave_escolhida}`\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        ),
        color=0x2b2d31
    )
    
    # Foto grande do bot
    if bot.user and bot.user.avatar:
        embed.set_image(url=bot.user.avatar.url)
        
    embed.set_author(name="🧧 Joker", icon_url=bot.user.avatar.url if bot.user and bot.user.avatar else None)
    embed.set_footer(text=f"Enviado por {interaction.user.name}", icon_url=interaction.user.avatar.url if interaction.user.avatar else None)
    
    await interaction.response.send_message(embed=embed)


# Iniciar o bot
if __name__ == "__main__":
    token = os.getenv('TOKEN')
    
    if not token:
        print("❌ ERRO: Token não encontrado no arquivo .env!")
        print("📋 Crie um arquivo .env com: TOKEN=seu_token_aqui")
    else:
        print("🚀 Iniciando bot...")
        try:
            bot.run(token)
        except Exception:
            import os
            print("\n❌ [ERRO DE LOGIN] O token fornecido no seu arquivo .env ('seu_token_aqui') é falso!")
            print("❌ O Discord recusou a conexão. Insira o token oficial do seu bot no arquivo .env para ligar.")
            os._exit(1)