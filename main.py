import os
import discord
import random
import time
import traceback
from discord.ext import commands

TOKEN = os.getenv("BOT_TOKEN")
GUILD_ID = 1398256208887939214  # 서버 ID

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)
user_points = {}
last_play_time = {}

class MinesButton(discord.ui.Button):
    def __init__(self, x, y):
        # emoji 파라미터로 커스텀 이모지 지정
        super().__init__(emoji="<:emoji_13:1404845832028557414>", style=discord.ButtonStyle.secondary, row=y)
        self.x = x
        self.y = y

    async def callback(self, interaction: discord.Interaction):
        if interaction.user != self.view.player:
            await interaction.response.send_message("이 게임은 당신 것이 아닙니다!", ephemeral=True)
            return

        cell = self.view.board[self.y][self.x]

        if cell == "💎":
            self.emoji = "💎"
            self.style = discord.ButtonStyle.success
            self.disabled = True
            self.view.found_gems += 1

            await interaction.response.edit_message(view=self.view)

            if self.view.found_gems == self.view.gems_to_find:
                user_points[interaction.user.id] = user_points.get(interaction.user.id, 0) + 1
                await interaction.followup.send(
                    f"🎉 {interaction.user.mention} 보석 {self.view.gems_to_find}개 모두 찾았습니다! "
                    f"(+1점, 총 {user_points[interaction.user.id]}점)",
                    ephemeral=True
                )
                for item in self.view.children:
                    item.disabled = True
                await interaction.edit_original_response(view=self.view)

        else:  # 폭탄
            self.emoji = "💣"
            self.style = discord.ButtonStyle.danger
            self.disabled = True
            await interaction.response.edit_message(view=self.view)

            await interaction.followup.send(
                f"💥 {interaction.user.mention} 폭탄을 뽑아 탈락했습니다!",
                ephemeral=True
            )
            for item in self.view.children:
                item.disabled = True
            await interaction.edit_original_response(view=self.view)

class MinesGame(discord.ui.View):
    def __init__(self, player):
        super().__init__(timeout=60)
        self.player = player
        self.gems_to_find = 3   # 승리 조건 (3개 찾으면 끝)
        self.total_gems = 7     # 보드에 배치할 보석 총 개수
        self.found_gems = 0

        # 5x5 보드 모두 폭탄으로 초기화
        self.board = [["💣" for _ in range(5)] for _ in range(5)]

        # 보석 7개를 랜덤 위치에 배치
        positions = random.sample([(x, y) for y in range(5) for x in range(5)], self.total_gems)
        for x, y in positions:
            self.board[y][x] = "💎"

        for y in range(5):
            for x in range(5):
                self.add_item(MinesButton(x, y))

@bot.tree.command(name="미니게임", description="5x5 보석 맞추기 게임 (30분 쿨타임)", guild=discord.Object(id=GUILD_ID))
async def minigame(interaction: discord.Interaction):
    await interaction.response.defer()

    try:
        now = time.time()
        last_time = last_play_time.get(interaction.user.id, 0)

        if now - last_time < 1800:
            remaining = int(1800 - (now - last_time))
            minutes = remaining // 60
            seconds = remaining % 60
            await interaction.followup.send(
                f"{minutes}분 {seconds}초 후에 다시 시도하세요.",
                ephemeral=True
            )
            return

        last_play_time[interaction.user.id] = now

        try:
            view = MinesGame(interaction.user)
        except Exception as e:
            traceback.print_exc()
            await interaction.followup.send(
                f"게임 생성 중 오류가 발생했습니다: `{e}`",
                ephemeral=True
            )
            return

        await interaction.followup.send(
            f"**보석 {view.gems_to_find}개를 찾으면 포인트 하나 드립니다**\n"
            f"총 {view.total_gems}개의 보석이 숨겨져 있습니다!",
            view=view
        )

    except Exception as e:
        traceback.print_exc()
        await interaction.followup.send(
            f"명령어 실행 중 오류 발생: `{e}`",
            ephemeral=True
        )

@bot.tree.command(name="포인트", description="내 포인트 확인", guild=discord.Object(id=GUILD_ID))
async def check_points(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    points = user_points.get(interaction.user.id, 0)
    await interaction.followup.send(f"💰 현재 포인트: {points}점", ephemeral=True)

@bot.event
async def on_ready():
    await bot.tree.sync(guild=discord.Object(id=GUILD_ID))
    print(f"✅ 로그인됨: {bot.user} | 명령어 동기화 완료!")

bot.run(TOKEN)
