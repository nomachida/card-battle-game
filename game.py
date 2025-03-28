import pygame
import sys
import json
import random
import math

# 設定ファイルを読み込む
with open('config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)

# Pygameを初期化
pygame.init()
pygame.font.init()

# 画面設定
WINDOW_WIDTH = config['features']['graphics']['resolution']['width']
WINDOW_HEIGHT = config['features']['graphics']['resolution']['height']
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption(config['game_name'])

# フォント設定
FONT_LARGE = pygame.font.SysFont('Arial', 32)
FONT_MEDIUM = pygame.font.SysFont('Arial', 24)
FONT_SMALL = pygame.font.SysFont('Arial', 16)

# 色の定義
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
GRAY = (128, 128, 128)

class Card:
    def __init__(self, card_id, card_data):
        self.id = card_id
        self.name = card_data['name']
        self.type = card_data['type']
        self.cost = card_data['cost']
        self.description = card_data['description']
        self.damage = card_data.get('damage', 0)
        self.block = card_data.get('block', 0)
        self.effects = card_data.get('effects', [])
        
        # カードの表示位置
        self.x = 0
        self.y = 0
        self.width = config['features']['graphics']['sprites']['card']['size'][0]
        self.height = config['features']['graphics']['sprites']['card']['size'][1]
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)
        self.selected = False
        
    def draw(self, screen, x, y):
        self.x = x
        self.y = y
        self.rect = pygame.Rect(x, y, self.width, self.height)
        
        # カードの背景
        color = BLUE if self.type == 'attack' else GREEN if self.type == 'skill' else GRAY
        pygame.draw.rect(screen, color, self.rect)
        if self.selected:
            pygame.draw.rect(screen, WHITE, self.rect, 2)
        
        # カード情報の描画
        cost_text = FONT_MEDIUM.render(str(self.cost), True, WHITE)
        name_text = FONT_SMALL.render(self.name, True, WHITE)
        desc_text = FONT_SMALL.render(self.description, True, WHITE)
        
        screen.blit(cost_text, (x + 5, y + 5))
        screen.blit(name_text, (x + 5, y + 30))
        screen.blit(desc_text, (x + 5, y + 100))

class Character:
    def __init__(self, is_player=True):
        self.is_player = is_player
        if is_player:
            self.max_health = config['features']['gameplay']['player']['max_health']
            self.energy = config['features']['gameplay']['player']['starting_energy']
            self.max_energy = self.energy
        else:
            enemy_type = 'slime'  # 最初の敵は固定
            self.max_health = config['features']['gameplay']['enemies'][enemy_type]['max_health']
            self.actions = config['features']['gameplay']['enemies'][enemy_type]['actions']
        
        self.health = self.max_health
        self.block = 0
        self.effects = dict()
        
    def draw(self, screen, x, y):
        # キャラクターの表示
        size = config['features']['graphics']['sprites']['character' if self.is_player else 'enemy']['size']
        rect = pygame.Rect(x, y, size[0], size[1])
        pygame.draw.rect(screen, BLUE if self.is_player else RED, rect)
        
        # HPバーの表示
        hp_width = (self.health / self.max_health) * size[0]
        pygame.draw.rect(screen, RED, (x, y - 20, size[0], 10))
        pygame.draw.rect(screen, GREEN, (x, y - 20, hp_width, 10))
        
        # HP数値の表示
        hp_text = FONT_SMALL.render(str(self.health) + "/" + str(self.max_health), True, WHITE)
        screen.blit(hp_text, (x, y - 40))
        
        # ブロックの表示
        if self.block > 0:
            block_text = FONT_SMALL.render(str(self.block), True, WHITE)
            pygame.draw.circle(screen, GRAY, (x + size[0] - 20, y - 20), 15)
            screen.blit(block_text, (x + size[0] - 25, y - 30))
        
        # プレイヤーの場合、エネルギーも表示
        if self.is_player:
            energy_text = FONT_LARGE.render("[" + str(self.energy) + "]", True, BLUE)
            screen.blit(energy_text, (x - 50, y))

class Game:
    def __init__(self):
        self.player = Character(True)
        self.enemy = Character(False)
        self.deck = []
        self.hand = []
        self.discard = []
        
        # デッキの初期化
        for card_info in config['features']['gameplay']['player']['deck']:
            card_id = card_info['id']
            card_data = config['features']['gameplay']['cards'][card_id]
            for _ in range(card_info['count']):
                self.deck.append(Card(card_id, card_data))
        
        # デッキをシャッフル
        random.shuffle(self.deck)
        
        # 初期手札を引く
        self.draw_cards(config['features']['gameplay']['player']['hand_size'])
    
    def draw_cards(self, count):
        for _ in range(count):
            if not self.deck:
                # デッキが空の場合、捨て札をシャッフルしてデッキにする
                if not self.discard:
                    break
                self.deck = self.discard
                self.discard = []
                random.shuffle(self.deck)
            
            if self.deck:
                self.hand.append(self.deck.pop())
    
    def play_card(self, card, target):
        if self.player.energy >= card.cost:
            self.player.energy -= card.cost
            
            # ダメージの処理
            if card.damage > 0:
                damage = card.damage
                if 'vulnerable' in target.effects:
                    damage = math.floor(damage * config['features']['gameplay']['status_effects']['vulnerable']['modifier'])
                if 'weak' in self.player.effects:
                    damage = math.floor(damage * config['features']['gameplay']['status_effects']['weak']['modifier'])
                if target.block >= damage:
                    target.block -= damage
                else:
                    damage -= target.block
                    target.block = 0
                    target.health -= damage
            
            # ブロックの処理
            if card.block > 0:
                self.player.block += card.block
            
            # 効果の処理
            for effect in card.effects:
                if effect['type'] not in target.effects:
                    target.effects[effect['type']] = 0
                target.effects[effect['type']] += effect['amount']
            
            # カードを捨て札に移動
            self.hand.remove(card)
            self.discard.append(card)
            
            return True
        return False
    
    def enemy_turn(self):
        # 敵の行動をランダムに選択
        action = random.choices(self.enemy.actions, weights=[a['weight'] for a in self.enemy.actions])[0]
        
        if action['type'] == 'attack':
            damage = action['damage']
            if 'vulnerable' in self.player.effects:
                damage = math.floor(damage * config['features']['gameplay']['status_effects']['vulnerable']['modifier'])
            if 'weak' in self.enemy.effects:
                damage = math.floor(damage * config['features']['gameplay']['status_effects']['weak']['modifier'])
            if self.player.block >= damage:
                self.player.block -= damage
            else:
                damage -= self.player.block
                self.player.block = 0
                self.player.health -= damage
        
        elif action['type'] == 'defend':
            self.enemy.block += action['block']
        
        elif action['type'] == 'buff':
            if action['effect'] not in self.enemy.effects:
                self.enemy.effects[action['effect']] = 0
            self.enemy.effects[action['effect']] += action['amount']
    
    def start_turn(self):
        self.player.energy = self.player.max_energy
        self.draw_cards(config['features']['gameplay']['player']['hand_size'] - len(self.hand))
        
        # 効果の持続時間を減らす
        for effect in list(self.player.effects.keys()):
            self.player.effects[effect] -= 1
            if self.player.effects[effect] <= 0:
                del self.player.effects[effect]
        for effect in list(self.enemy.effects.keys()):
            self.enemy.effects[effect] -= 1
            if self.enemy.effects[effect] <= 0:
                del self.enemy.effects[effect]
    
    def draw(self, screen):
        # 背景
        screen.fill(BLACK)
        
        # キャラクターの描画
        player_pos = config['features']['ui']['status']['player']
        enemy_pos = config['features']['ui']['status']['enemy']
        self.player.draw(screen, player_pos['x'], player_pos['y'])
        self.enemy.draw(screen, enemy_pos['x'], enemy_pos['y'])
        
        # 手札の描画
        hand_pos = config['features']['ui']['card_positions']['hand']
        card_width = config['features']['graphics']['sprites']['card']['size'][0]
        spacing = 10
        total_width = len(self.hand) * (card_width + spacing) - spacing
        start_x = hand_pos['x'] - total_width // 2
        
        for i, card in enumerate(self.hand):
            card.draw(screen, start_x + i * (card_width + spacing), hand_pos['y'])
        
        # デッキと捨て札の枚数表示
        deck_pos = config['features']['ui']['card_positions']['deck']
        discard_pos = config['features']['ui']['card_positions']['discard']
        deck_text = FONT_MEDIUM.render("山札: " + str(len(self.deck)), True, WHITE)
        discard_text = FONT_MEDIUM.render("捨て札: " + str(len(self.discard)), True, WHITE)
        screen.blit(deck_text, (deck_pos['x'], deck_pos['y']))
        screen.blit(discard_text, (discard_pos['x'], discard_pos['y']))
        
        # 効果の表示
        effect_y = 50
        for effect, duration in self.player.effects.items():
            effect_data = config['features']['gameplay']['status_effects'][effect]
            effect_text = FONT_SMALL.render(effect_data['name'] + ": " + str(duration), True, WHITE)
            screen.blit(effect_text, (player_pos['x'], player_pos['y'] - effect_y))
            effect_y += 20
        
        effect_y = 50
        for effect, duration in self.enemy.effects.items():
            effect_data = config['features']['gameplay']['status_effects'][effect]
            effect_text = FONT_SMALL.render(effect_data['name'] + ": " + str(duration), True, WHITE)
            screen.blit(effect_text, (enemy_pos['x'], enemy_pos['y'] - effect_y))
            effect_y += 20

# ゲームの初期化
game = Game()
clock = pygame.time.Clock()
running = True
selected_card = None
player_turn = True

# ゲームループ
while running:
    # イベント処理
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN and player_turn:
            mouse_pos = pygame.mouse.get_pos()
            
            # カードの選択
            for card in game.hand:
                if card.rect.collidepoint(mouse_pos):
                    if selected_card == card:
                        # カードを使用
                        if game.play_card(card, game.enemy):
                            selected_card = None
                            if not game.hand:  # 手札が空になったら敵のターン
                                player_turn = False
                    else:
                        selected_card = card
                        for other_card in game.hand:
                            if other_card != card:
                                other_card.selected = False
                        card.selected = True
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE and not player_turn:
                # 敵のターン
                game.enemy_turn()
                player_turn = True
                game.start_turn()
    
    # 画面の描画
    game.draw(screen)
    
    # 画面の更新
    pygame.display.flip()
    
    # フレームレートの制御
    clock.tick(60)

# ゲームの終了
pygame.quit()
sys.exit()
