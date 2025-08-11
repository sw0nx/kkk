import os
import discord
import random
import time
from discord.ext import commands

# ==== 설정 ====
TOKEN = os.getenv("BOT_TOKEN")  # Zeabur 환경변수에서 불러오기
GUILD_ID = 1398256208887939214  # 서버 ID

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)
user_points = {}
last_play_time = {}  # 마지막 게임 시간 기록

# ===== 버튼 클래스 =====
class MinesButton(discord.ui.Button):
    def __init__(self, x, y):
        super().__init__(label="⬛", style=discord.ButtonStyle.secondary, row=y)
        self.x = x
        self.y = y

    async def callback(self, interaction: discord.Interaction):
        if interaction.user != self.view.player:
            await interaction.response.send_message("⛔ 이 게임은 당신 것이 아닙니다!", ephemeral=True)
            return

        cell = self.view.board[self.y][self.x]

        if cell == "💎":
            self.label = "💎"
            self.style = discord.ButtonStyle.success
        else:
            self.label = "💣"
            self.style = discord.ButtonStyle.danger

        self.disabled = True
        await interaction.response.edit_message(view=self.view)

        if self.view.check_win():
            points = 10
            user_points[interaction.user.id] = user_points.get(interaction.user.id, 0) + points
            await interaction.followup.send(
                f"🎉 {interaction.user.mention} 승리! (+{points}점, 총 {user_points[interaction.user.id]}점)",
                ephemeral=True
            )
            for item in self.view.children:
                item.disabled = True
            await interaction.edit_original_response(view=self.view)

# ===== 게임 뷰 =====
class MinesGame(discord.ui.View):
    def __init__(self, player):
        super().__init__(timeout=60)
        self.player = player
        self.board = [[("💎" if random.random() < 0.3 else "💣") for _ in range(5)] for _ in range(5)]
        for y in range(5):
            for x in range(5):
                self.add_item(MinesButton(x, y))

    def check_win(self):
        # 가로, 세로
        for y in range(5):
            for x in range(3):
                if self.board[y][x] == self.board[y][x+1] == self.board[y][x+2] == "💎":
                    return True
        for x in range(5):
            for y in range(3):
                if self.board[y][x] == self.board[y+1][x] == self.board[y+2][x] == "💎":
                    return True
        # 대각선
        for y in range(3):
            for x in range(3):
                if self.board[y][x] == self.board[y+1][x+1] == self.board[y+2][x+2] == "💎":
                    return True
                if self.board[y][x+2] == self.board[y+1][x+1] == self.board[y+2][x] == "💎":
                    return True
        return False

# ===== 명령어 =====
@bot.tree.command(name="미니게임", description="5x5 보석 맞추기 게임 (30분 쿨타임)")
async def minigame(interaction: discord.Interaction):
    now = time.time()
    last_time = last_play_time.get(interaction.user.id, 0)

    # 30분(1800초) 제한
    if now - last_time < 1800:
        remaining = int(1800 - (now - last_time))
        minutes = remaining // 60
        seconds = remaining % 60
        await interaction.response.send_message(
            f"⏳ 아직 쿨타임입니다! {minutes}분 {seconds}초 후에 다시 시도하세요.",
            ephemeral=True
        )
        return

    last_play_time[interaction.user.id] = now  # 마지막 실행 시간 저장
    view = MinesGame(interaction.user)
    await interaction.response.send_message(
        "💎 **보석 3개를 찾으시면 포인트 하나를 드립니다!**",
        view=view
    )

@bot.tree.command(name="포인트", description="내 포인트 확인")
async def check_points(interaction: discord.Interaction):
    points = user_points.get(interaction.user.id, 0)
    await interaction.response.send_message(f"💰 현재 포인트: {points}점", ephemeral=True)

# ===== 강제 동기화 명령어 =====
@bot.command()
async def sync(ctx):
    await bot.tree.sync(guild=discord.Object(id=GUILD_ID))
    await ctx.send("✅ 명령어가 동기화되었습니다! (서버 전용)")

# ===== 봇 준비 시 자동 동기화 =====
@bot.event
async def on_ready():
    await bot.tree.sync(guild=discord.Object(id=GUILD_ID))
    print(f"✅ 로그인됨: {bot.user}")

bot.run(TOKEN)
