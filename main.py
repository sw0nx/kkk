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
        super().__init__(label="\u200b", style=discord.ButtonStyle.secondary, row=y)
        self.x = x
        self.y = y

    async def callback(self, interaction: discord.Interaction):
        if interaction.user != self.view.player:
            await interaction.response.send_message("이 게임은 당신 것이 아닙니다!", ephemeral=True)
            return

        cell = self.view.board[self.y][self.x]

        if cell == "💎":  # 보석 클릭
            self.label = "💎"
            self.style = discord.ButtonStyle.success
            self.disabled = True
            self.view.found_gems += 1
            await interaction.response.edit_message(view=self.view)

            if self.view.found_gems == self.view.gems_to_find:
                user_points[interaction.user.id] = user_points.get(interaction.user.id, 0) + 1
                for item in self.view.children:
                    item.disabled = True
                # 전체 공개로 업데이트
                await interaction.message.edit(view=self.view)

                await interaction.followup.send(
                    f"🎉 {interaction.user.mention} 보석 {self.view.gems_to_find}개 모두 찾았습니다! "
                    f"(+1점, 총 {user_points[interaction.user.id]}점)",
                    ephemeral=True
                )

        else:  # 폭탄 클릭
            self.label = "💣"
            self.style = discord.ButtonStyle.danger  # 클릭한 폭탄 빨간색
            self.disabled = True

            # 나머지 폭탄/보석 표시
            for item in self.view.children:
                if isinstance(item, MinesButton) and not item.disabled:
                    if self.view.board[item.y][item.x] == "💣":
                        item.label = "💣"
                        item.style = discord.ButtonStyle.secondary  # 다른 폭탄 회색
                    elif self.view.board[item.y][item.x] == "💎":
                        item.label = "💎"
                        item.style = discord.ButtonStyle.secondary  # 다른 보석 회색
                    item.disabled = True

            # 게임판은 전체 공개로 수정
            await interaction.message.edit(view=self.view)

            # 폭탄 클릭 메시지는 개인만 보기
            await interaction.response.send_message(
                f"💥 {interaction.user.mention} 폭탄을 뽑아 탈락했습니다!",
                ephemeral=True
            )

class MinesGame(discord.ui.View):
    def __init__(self, player):
        super().__init__(timeout=60)
        self.player = player
        self.gems_to_find = 3
        self.total_gems = 7
        self.found_gems = 0

        self.board = [["💣" for _ in range(5)] for _ in range(5)]

        positions = random.sample([(x, y) for y in range(5) for x in range(5)], self.total_gems)
        for x, y in positions:
            self.board[y][x] = "💎"

        for y in range(5):
            for x in range(5):
                self.add_item(MinesButton(x, y))

@bot.tree.command(name="미니게임", description="5x5 보석 맞추기 게임 (30분 쿨타임)", guild=discord.Object(id=GUILD_ID))
async def minigame(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)  # 쿨타임 안내는 개인

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
        view = MinesGame(interaction.user)

        # 게임 시작은 전체 공개
        await interaction.followup.send(
            f"**보석 {view.gems_to_find}개를 찾으면 포인트 하나 드립니다**\n"
            f"총 {view.total_gems}개의 보석이 숨겨져 있습니다!",
            view=view,
            ephemeral=False
        )

    except Exception as e:
        traceback.print_exc()
        await interaction.followup.send(
            f"명령어 실행 중 오류 발생: {e}",
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
