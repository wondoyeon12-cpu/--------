import pygame
import json
import sys
import os
import time

# 초기화
pygame.init()
pygame.display.set_caption("Pixel AI Office (Dummy)")

# 크기 및 설정
WIDTH, HEIGHT = 600, 400
FPS = 30
screen = pygame.display.set_mode((WIDTH, HEIGHT))

# 색상
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)
WORK_COLOR = (100, 150, 255)
BG_COLOR = (40, 44, 52)

# 한글 폰트 설정 (기본 폰트를 쓰되 안되면 시스템 폰트 탐색, 여기선 윈도우 맑은고딕)
try:
    font_path = "C:/Windows/Fonts/malgun.ttf"
    font = pygame.font.Font(font_path, 20)
    font_small = pygame.font.Font(font_path, 14)
except:
    font = pygame.font.SysFont("malgun gothic", 20)
    font_small = pygame.font.SysFont("malgun gothic", 14)

def load_status():
    status_file = "agent_status.json"
    if os.path.exists(status_file):
        try:
            with open(status_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            pass
    return {}

def draw_agent(screen, name, data, x, y, blink_state):
    status = data.get("status", "idle")
    task = data.get("task", "")
    
    # 더미 박스 (캐릭터)
    rect = pygame.Rect(x, y, 60, 80)
    
    color = GRAY
    if status == "working":
        # 약간 깜빡이는 효과 (일하는 척)
        color = WORK_COLOR if blink_state else (80, 130, 230)
        
    pygame.draw.rect(screen, color, rect, border_radius=5)
    
    # 이름 텍스트
    name_surface = font.render(name, True, WHITE)
    name_rect = name_surface.get_rect(center=(x + 30, y + 100))
    screen.blit(name_surface, name_rect)
    
    # 꼬리표 (말풍선 느낌 박스)
    if status == "working":
        task_surface = font_small.render(task, True, BLACK)
        task_rect = task_surface.get_rect(center=(x + 30, y - 20))
        
        # 말풍선 배경
        bg_rect = task_rect.inflate(10, 10)
        pygame.draw.rect(screen, WHITE, bg_rect, border_radius=4)
        screen.blit(task_surface, task_rect)

def main():
    clock = pygame.time.Clock()
    running = True
    
    last_update_time = 0
    agent_data = {}
    blink_timer = 0
    blink_state = True
    
    # 위치 설정
    positions = [
        (100, 150),
        (250, 150),
        (400, 150),
        (250, 280) # 코다리 부장은 밑에
    ]

    while running:
        current_time = time.time()
        
        # 0.5초마다 파일 읽기
        if current_time - last_update_time > 0.5:
            agent_data = load_status()
            last_update_time = current_time
            
        # 깜빡임 토글용 (작업 중 애니메이션 효과)
        blink_timer += clock.get_time()
        if blink_timer > 300: # 300ms
            blink_state = not blink_state
            blink_timer = 0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                
        screen.fill(BG_COLOR)
        
        # 오피스 타이틀
        title = font.render("Pixel AI Office (Proto)", True, WHITE)
        screen.blit(title, (20, 20))
        
        # 그리기
        idx = 0
        names = list(agent_data.keys())
        for name in names:
            if idx < len(positions):
                x, y = positions[idx]
                draw_agent(screen, name, agent_data[name], x, y, blink_state)
            idx += 1
            
        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
