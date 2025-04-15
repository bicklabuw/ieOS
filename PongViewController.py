from ViewController import ViewController
from View import View
import random
import Display
from typing import Optional, Tuple

import Main

from PIL import ImageDraw
from Components import Component, MultiLineTextComponent, TextAnchor, VerticalAnchor, HorizontalAnchor
from Components import LineComponent, CircleComponent, RectangleComponent
import math
import time

from MathUtils import rad_to_deg

class PongViewController(ViewController):
    def __init__(self, user_paddle_dist_from_edge: int = Display.SCREEN_WIDTH // 8,
                 user_paddle_width: int = 3, user_paddle_height: int = 25, 
                 user_paddle_speed: float = 3, user_paddle_init_y: int = Display.SCREEN_HEIGHT // 2, 
                 cpu_paddle_dist_frome_edge: int = Display.SCREEN_WIDTH // 8, 
                 cpu_paddle_width: int = 3, cpu_paddle_height: int = 15, 
                 cpu_paddle_speed: float = 1.5, cpu_paddle_init_y: int = Display.SCREEN_HEIGHT // 2,
                 ball_radius: int = 3, ball_init_speed: float = 1.5, 
                 ball_speed_multiplier_per_hit: float = 0.25, ball_speed_exponential: bool = False, 
                 ball_init_angle: Optional[float] = None, paddle_bounce_angle_range: float = 90, 
                 min_ball_angle_from_paddle: float = 20, 
                 ball_init_x: Optional[int] = Display.SCREEN_WIDTH // 2,
                 ball_init_y: Optional[int] = Display.SCREEN_HEIGHT // 2):
        super().__init__()

        self.user_paddle_dist_from_edge = user_paddle_dist_from_edge
        self.user_paddle_width = user_paddle_width
        self.user_paddle_height = user_paddle_height
        self.user_paddle_init_y = user_paddle_init_y

        self.cpu_paddle_dist_from_edge = cpu_paddle_dist_frome_edge
        self.cpu_paddle_width = cpu_paddle_width
        self.cpu_paddle_height = cpu_paddle_height
        self.cpu_paddle_init_y = cpu_paddle_init_y
        
        self.user_paddle_speed = user_paddle_speed
        self.cpu_paddle_speed = cpu_paddle_speed

        self.paddle_bounce_angle_range = math.pi * paddle_bounce_angle_range / 180
        self.min_ball_angle_from_paddle = math.pi * min_ball_angle_from_paddle / 180

        self.ball_radius = ball_radius
        self.ball_init_speed = ball_init_speed
        self.ball_speed_multiplier_per_hit = ball_speed_multiplier_per_hit
        self.ball_speed_exponential = ball_speed_exponential
        self.ball_init_angle = ball_init_angle
        self.ball_speed = self.ball_init_speed

        self.ball_init_x = ball_init_x
        self.ball_init_y = ball_init_y

        self.ball_x = ball_init_x
        self.ball_y = ball_init_y
        
        self.start_view = PongTextView()
        self.game_over_view = GameOverView()

        self.game_over = True
        
        self.present_view(self.start_view)

    def start_new_game(self):
        if self.ball_init_x is None:
            x_init_mod = 2/3
            x_change = ((Display.SCREEN_WIDTH - 
                       (self.user_paddle_dist_from_edge + self.user_paddle_width) - 
                       (self.cpu_paddle_dist_from_edge + self.cpu_paddle_width)) * 
                       (1 - x_init_mod)) / 2
            x_range_start = self.user_paddle_dist_from_edge + self.user_paddle_width + x_change
            x_range_end = (Display.SCREEN_WIDTH - self.cpu_paddle_dist_from_edge - 
                           self.cpu_paddle_width - x_change)
            
            self.ball_init_x = random.randint(x_range_start, x_range_end)

        if self.ball_init_y is None:
            self.ball_init_y = random.randint(0, Display.SCREEN_HEIGHT)
        
        if self.ball_init_x < self.user_paddle_dist_from_edge + self.user_paddle_width:
            self.ball_init_x = self.user_paddle_dist_from_edge + self.user_paddle_width + self.ball_radius
        elif self.ball_init_x > Display.SCREEN_WIDTH - self.cpu_paddle_dist_from_edge - self.cpu_paddle_width:
            self.ball_init_x = Display.SCREEN_WIDTH - self.cpu_paddle_dist_from_edge - self.cpu_paddle_width - self.ball_radius

        if self.ball_init_angle is None:
            ball_init_towards_user = random.choice([True, False])
            low_angle, high_angle = self.calculate_legal_initial_ball_angles(for_user=ball_init_towards_user)
            self.ball_init_angle = random.uniform(low_angle, high_angle)
        else:
            principal_angle = self.ball_init_angle % (2 * math.pi)
            if principal_angle > math.pi / 2 and principal_angle < 3 * math.pi / 2:
                low_angle, high_angle = self.calculate_legal_initial_ball_angles(for_user=True)
                if principal_angle < low_angle:
                    self.ball_init_angle = low_angle
                elif principal_angle > high_angle:
                    self.ball_init_angle = high_angle
            else:
                low_angle, high_angle = self.calculate_legal_initial_ball_angles(for_user=False)
                if principal_angle - (2 * math.pi) < low_angle:
                    self.ball_init_angle = low_angle
                elif principal_angle > high_angle:
                    self.ball_init_angle = high_angle
        
        self.ball_angle = self.ball_init_angle
        
        self.ball_speed = self.ball_init_speed

        self.pong_view = PongView(
            user_paddle_dist_from_edge=self.user_paddle_dist_from_edge,
            user_paddle_width=self.user_paddle_width,
            user_paddle_height=self.user_paddle_height,
            user_paddle_init_y=self.user_paddle_init_y,
            cpu_paddle_dist_from_edge=self.cpu_paddle_dist_from_edge,
            cpu_paddle_width=self.cpu_paddle_width,
            cpu_paddle_height=self.cpu_paddle_height,
            cpu_paddle_init_y=self.cpu_paddle_init_y,
            ball_radius=self.ball_radius,
            ball_init_x=self.ball_init_x,
            ball_init_y=self.ball_init_y
        )

        self.ball_x = self.ball_init_x
        self.ball_y = self.ball_init_y
        
        print(self.ball_x)
        print(self.ball_y)
        
        self._score = 0

        self.game_over = False
        self.pause = False
        self.present_view(self.pong_view)

    def calculate_legal_initial_ball_angles(self, for_user: bool) -> Tuple[int, int]:
        if for_user:
            top_angle = math.pi / 2 + abs(math.atan2(
                self.ball_init_x - self.user_paddle_dist_from_edge - self.user_paddle_width,
                self.ball_init_y - self.ball_radius))
            bottom_angle = 3 * math.pi / 2 - abs(math.atan2(
                self.ball_init_x - self.user_paddle_dist_from_edge - self.user_paddle_width,
                Display.SCREEN_HEIGHT - self.ball_init_y - self.ball_radius))
            
            if top_angle < math.pi / 2 + self.min_ball_angle_from_paddle:
                top_angle = math.pi / 2 + self.min_ball_angle_from_paddle
            if bottom_angle > 3 * math.pi / 2 - self.min_ball_angle_from_paddle:
                bottom_angle = 3 * math.pi / 2 - self.min_ball_angle_from_paddle
            
            return [top_angle, bottom_angle]
        else:
            top_angle = math.pi / 2 - abs(math.atan2(
                (Display.SCREEN_WIDTH - self.cpu_paddle_dist_from_edge - 
                 self.cpu_paddle_width - self.ball_init_x),
                self.ball_init_y - self.ball_radius))
            bottom_angle = -math.pi / 2 + abs(math.atan2(
                (Display.SCREEN_WIDTH - self.cpu_paddle_dist_from_edge - 
                 self.cpu_paddle_width - self.ball_init_x),
                Display.SCREEN_HEIGHT - self.ball_init_y - self.ball_radius))
            
            if top_angle > math.pi / 2 - self.min_ball_angle_from_paddle:
                top_angle = math.pi / 2 - self.min_ball_angle_from_paddle
            if bottom_angle < -math.pi / 2 + self.min_ball_angle_from_paddle:
                bottom_angle = -math.pi / 2 + self.min_ball_angle_from_paddle
            
            return [bottom_angle, top_angle]
    
    def detect_ball_collision(self, detect_for_user_paddle: bool) -> bool:
        rx = self.user_paddle_dist_from_edge if detect_for_user_paddle else \
            Display.SCREEN_WIDTH - self.cpu_paddle_dist_from_edge - self.cpu_paddle_width
        ry = self.pong_view.get_paddle_y(detect_for_user_paddle)
        rw = self.user_paddle_width if detect_for_user_paddle else self.cpu_paddle_width
        rh = self.user_paddle_height if detect_for_user_paddle else self.cpu_paddle_height
        cx = self.ball_x
        cy = self.ball_y
        r = self.ball_radius

        # Find the closest point on the rect to the circle center
        closest_x = max(rx, min(cx, rx + rw))
        closest_y = max(ry, min(cy, ry + rh))

        # Compute the distance between circle center and this point
        dx = cx - closest_x
        dy = cy - closest_y

        # If the distance is less than the radius, there's a collision
        return (dx * dx + dy * dy) <= (r * r)
    
    def move_paddle(self, move_user_paddle: bool, move_up: bool):
        amt = self.user_paddle_speed if move_user_paddle else self.cpu_paddle_speed
        
        if move_up:
            amt = -amt
        
        if not self.game_over and not self.pause:
            paddle_y = self.pong_view.get_paddle_y(move_user_paddle)
            paddle_height = (self.user_paddle_height if move_user_paddle
                            else self.cpu_paddle_height)
            
            if paddle_y + amt >= 0 and paddle_y + amt <= Display.SCREEN_HEIGHT - paddle_height:
                self.pong_view.set_paddle_y(move_user_paddle, paddle_y + amt)
            elif paddle_y + amt < 0:
                self.pong_view.set_paddle_y(move_user_paddle, 0)
            else:
                self.pong_view.set_paddle_y(move_user_paddle, 
                                            Display.SCREEN_HEIGHT - paddle_height)

    def get_new_angle_on_collision(self, collision_with_user_paddle: bool) -> float:
        def_angle = (math.pi - self.ball_angle) % (2 * math.pi)
        

        paddle_y = self.pong_view.get_paddle_y(collision_with_user_paddle)
        paddle_height = (self.user_paddle_height if collision_with_user_paddle
                            else self.cpu_paddle_height)
        ball_y = self.pong_view.get_ball_coords()[1]

        paddle_center = paddle_y + paddle_height / 2
        mult_upwards_factor = ((paddle_center - ball_y) / 
                                (paddle_height / 2 + self.ball_radius))
        
        angle_change = (self.paddle_bounce_angle_range / 2) * mult_upwards_factor
        angle = def_angle + angle_change
        
        print("----------------ANGLE STUFF----------------")
        print("Ball Angle: ", rad_to_deg(self.ball_angle))
        print("Def Angle: ", rad_to_deg(def_angle))
        
        print()
        
        print("Paddle Height: ", paddle_height)
        print("Paddle Divisor: ", (paddle_height / 2 + self.ball_radius))
        print("Paddle Center: ", paddle_center)
        print("Ball  Y: ", ball_y)
        
        print()
        
        print("Mult Upwards: ", mult_upwards_factor)
        
        print()
        
        print("Paddle Bounce Angle Range: ", self.paddle_bounce_angle_range)
        print("Angle Change: ", rad_to_deg(angle_change))
        print("Angle: ", rad_to_deg(angle))
        
        print()
        
        print("Angle from Paddle: ", rad_to_deg((angle - math.pi / 2) % math.pi))
        print("Min Angle From Paddle: ", rad_to_deg(self.min_ball_angle_from_paddle))
        print("Inner Condition: ", rad_to_deg(angle % (2 * math.pi))) 
        
        print()
        
        angle_from_paddle = (angle - math.pi / 2) % math.pi
        if angle_from_paddle < self.min_ball_angle_from_paddle or \
           math.pi - angle_from_paddle < self.min_ball_angle_from_paddle :
            if angle % (2 * math.pi) > math.pi:
                if collision_with_user_paddle:
                    angle = 3 * math.pi / 2 + self.min_ball_angle_from_paddle
                else:
                    angle = 3 * math.pi / 2 - self.min_ball_angle_from_paddle
            else:
                if collision_with_user_paddle:
                    angle = math.pi / 2 - self.min_ball_angle_from_paddle
                else:
                    angle = math.pi / 2 + self.min_ball_angle_from_paddle
                    
        print("Final Angle: ", rad_to_deg(angle))
        print("-------------------------------------------")
            
        return angle
        

    def on_appear(self):
        self.prev_collided = False
        while True:
            if not self.game_over:
                if not self.pause:
                    ball_change_x = self.ball_speed * math.cos(self.ball_angle)
                    ball_change_y = self.ball_speed * -math.sin(self.ball_angle)
                    
                    self.ball_x += ball_change_x
                    self.ball_y += ball_change_y
                    
                    if ball_change_x > 0:
                        cpu_paddle_y = self.pong_view.get_paddle_y(False)
                        cpu_mv_dir = int(round((self.ball_y - (cpu_paddle_y + self.cpu_paddle_height/2)) \
                                               / self.cpu_paddle_speed))
                        if cpu_mv_dir > 0:
                            self.move_paddle(False, False)
                        elif cpu_mv_dir < 0:
                            self.move_paddle(False, True)
                    
                    if not self.prev_collided:
                        if self.detect_ball_collision(detect_for_user_paddle=True):
                            self.prev_collided = True
                            if self.ball_speed_exponential:
                                self.ball_speed *= self.ball_speed_multiplier_per_hit
                            else:
                                self.ball_speed += self.ball_speed_multiplier_per_hit
                            self.ball_angle = self.get_new_angle_on_collision(collision_with_user_paddle=True)
                            print("Ball Angle: ", self.ball_angle)
                            self.ball_x = (self.user_paddle_dist_from_edge + self.user_paddle_width + 
                                                    self.ball_radius)
                            self._score += 1
                            self.pong_view.set_score(self._score)

                        if self.detect_ball_collision(detect_for_user_paddle=False):
                            self.prev_collided = True
                            self.ball_angle = self.get_new_angle_on_collision(collision_with_user_paddle=False)
                            print("Ball Angle: ", self.ball_angle)
                            self.ball_x = (Display.SCREEN_WIDTH - 
                                           self.cpu_paddle_dist_from_edge - 
                                           self.cpu_paddle_width - self.ball_radius)
                    else:
                        self.prev_collided = False
                        
                    if self.ball_y <= self.ball_radius:
                        self.ball_y = self.ball_radius
                        self.ball_angle = -self.ball_angle
                        print("Ball Angle: ", self.ball_angle)
                    elif self.ball_y >= Display.SCREEN_HEIGHT - self.ball_radius:
                        self.ball_y = Display.SCREEN_HEIGHT - self.ball_radius
                        self.ball_angle = -self.ball_angle
                        print("Ball Angle: ", self.ball_angle)
                    
                    self.pong_view.set_ball_coords(int(round(self.ball_x)), int(round(self.ball_y)))

                    if self.ball_x <= self.user_paddle_dist_from_edge - self.ball_radius:
                        self.game_over = True
                        self.user_winner = False
                        self.game_over_view.set_winner(self.user_winner, self._score)
                        self.present_view(self.game_over_view)
                    elif self.ball_x >= Display.SCREEN_WIDTH - self.cpu_paddle_dist_from_edge + self.ball_radius:
                        print("Ball info:")
                        print(self.ball_x)
                        print(Display.SCREEN_WIDTH)
                        print(self.cpu_paddle_dist_from_edge)
                        print(self.ball_radius)
                        self.game_over = True
                        self.user_winner = True
                        self.game_over_view.set_winner(self.user_winner, self._score)
                        self.present_view(self.game_over_view)
            time.sleep(0.1)


    def on_key_3_press(self):
        if self.game_over:
            self.start_new_game()

    def on_key_2_press(self):
        if self.game_over:
            self.start_new_game()
        else:
            self.pause = not self.pause
            self.pong_view.pause(self.pause)

    def on_key_1_press(self):
        if self.game_over:
            self.start_new_game()

    def on_joy_up_press(self):
        self.move_paddle(True, True)

    def on_joy_up_hold(self):
        self.move_paddle(True, True)

    def on_joy_down_press(self):
        self.move_paddle(True, False)

    def on_joy_down_hold(self):
        self.move_paddle(True, False)

class PauseComponent(Component):
    def __init__(self, x: int = 0, y: int = 0, width: int = Display.SCREEN_WIDTH, 
                 height: int = Display.SCREEN_HEIGHT, space_between_bars: int = 15):
        _bar_1 = RectangleComponent(x=0, y=0, width=1, height=1)
        _bar_2 = RectangleComponent(x=0, y=0, width=1, height=1)
        super().__init__(x=x, y=y, width=width, height=height, 
                         space_between_bars=space_between_bars, _bar_1=_bar_1, _bar_2=_bar_2)

    def draw(self, draw: ImageDraw):
        bar_width = (self.width - self.space_between_bars) // 2
        self._bar_1.x = self.x
        self._bar_1.y = self.y
        self._bar_2.x = self.x + bar_width + self.space_between_bars
        self._bar_2.y = self.y

        self._bar_1.width = bar_width
        self._bar_1.height = self.height
        self._bar_2.width = bar_width
        self._bar_2.height = self.height

        self._bar_1.draw(draw)
        self._bar_2.draw(draw)
        

class PongView(View):
    def __init__(self, user_paddle_dist_from_edge: int = Display.SCREEN_WIDTH // 8,
                 user_paddle_width: int = 3, user_paddle_height: int = 10,
                 user_paddle_init_y: int = Display.SCREEN_HEIGHT // 2,
                 cpu_paddle_dist_from_edge: int = Display.SCREEN_WIDTH // 8,
                 cpu_paddle_width: int = 3, cpu_paddle_height: int = 10, ball_radius: int = 3,
                 cpu_paddle_init_y: int = Display.SCREEN_HEIGHT // 2,
                 ball_init_x: int = Display.SCREEN_WIDTH // 2, 
                 ball_init_y: int = Display.SCREEN_HEIGHT // 2,
                 score_text_x: int = Display.SCREEN_WIDTH // 2,
                 score_text_y: int = Display.SCREEN_HEIGHT // 8,
                 score_text_font_size: int = 16,
                 score_prefix: str = "", score_suffix: str = "", score: int = 0,
                 pause_big_x: int = 3 * Display.SCREEN_WIDTH // 8,
                 pause_big_y: int = Display.SCREEN_HEIGHT // 4,
                 pause_big_width: int = Display.SCREEN_WIDTH // 4,
                 pause_big_height: int = Display.SCREEN_HEIGHT // 2,
                 pause_big_space_between_bars: int = 15,
                 pause_small_x: int = 57 * Display.SCREEN_WIDTH // 60,
                 pause_small_y: int = 14 * Display.SCREEN_HEIGHT // 30,
                 pause_small_width: int = Display.SCREEN_WIDTH // 30,
                 pause_small_height: int = Display.SCREEN_HEIGHT // 15,
                 pause_small_space_between_bars: int = 2):
        super().__init__()

        self._ball = CircleComponent(ball_init_x, ball_init_y, ball_radius)
        self._user_paddle = RectangleComponent(user_paddle_dist_from_edge, user_paddle_init_y, 
                                              user_paddle_width, user_paddle_height)
        self._cpu_paddle = RectangleComponent(
            Display.SCREEN_WIDTH - cpu_paddle_dist_from_edge - cpu_paddle_width, 
            cpu_paddle_init_y, cpu_paddle_width, cpu_paddle_height)
        
        self.score_prefix = score_prefix
        self.score_suffix = score_suffix
        
        self.score_text = MultiLineTextComponent(score_text_x, score_text_y,
                                                 text=f"{score_prefix}{score}{score_suffix}",
                                                 anchor=TextAnchor(VerticalAnchor.ASCENDER, 
                                                                   HorizontalAnchor.MIDDLE))
        
        self.pause_small_x = pause_small_x
        self.pause_small_y = pause_small_y
        self.pause_small_width = pause_small_width
        self.pause_small_height = pause_small_height
        self.pause_small_space_between_bars = pause_small_space_between_bars

        self.pause_big_x = pause_big_x
        self.pause_big_y = pause_big_y
        self.pause_big_width = pause_big_width
        self.pause_big_height = pause_big_height
        self.pause_big_space_between_bars = pause_big_space_between_bars
        
        self.pause_component = PauseComponent(self.pause_small_x, self.pause_small_y, self.pause_small_width, 
                                         self.pause_small_height, self.pause_small_space_between_bars)
        
        print("HERE")
        self.add_component(self._ball)
        self.add_component(self._user_paddle)
        self.add_component(self._cpu_paddle)
        self.add_component(self.score_text)
        self.add_component(self.pause_component)

    def get_ball_coords(self) -> Tuple[int, int]:
        return self._ball.x, self._ball.y
    
    def get_paddle_y(self, get_user_paddle: bool) -> Tuple[int, int]:
        return self._user_paddle.y if get_user_paddle else self._cpu_paddle.y
    
    def set_ball_coords(self, x: int, y: int):
        self._ball.x = x
        self._ball.y = y

    def set_paddle_y(self, set_user_paddle: bool, y: int):
        if set_user_paddle:
            self._user_paddle.y = y
        else:
            self._cpu_paddle.y = y

    def set_score(self, score: int, score_prefix: Optional[str] = None, 
                  score_suffix: Optional[str] = None, score_text_x: Optional[int] = None, 
                  score_text_y: Optional[int] = None, score_text_font_size: Optional[int] = None):
        self.score_prefix = score_prefix if score_prefix is not None else self.score_prefix
        self.score_suffix = score_suffix if score_suffix is not None else self.score_suffix

        self.score_text.x = score_text_x if score_text_x is not None else self.score_text.x
        self.score_text.y = score_text_y if score_text_y is not None else self.score_text.y
#         self.score_text.font_size = score_text_font_size if score_text_font_size is not None \
#             else self.score_text.font_size

        self.score_text.text = f"{self.score_prefix}{score}{self.score_suffix}"
        
    def pause(self, paused: bool):
        if paused:
            self.pause_component.x = self.pause_big_x
            self.pause_component.y = self.pause_big_y
            self.pause_component.width = self.pause_big_width
            self.pause_component.height = self.pause_big_height
            self.pause_component.space_between_bars = self.pause_big_space_between_bars
        else:
            self.pause_component.x = self.pause_small_x
            self.pause_component.y = self.pause_small_y
            self.pause_component.width = self.pause_small_width
            self.pause_component.height = self.pause_small_height
            self.pause_component.space_between_bars = self.pause_small_space_between_bars

# NOTE: FOR ALL VIEWS ____ FONT SIZE ____ has been disabled. Requires loading in a different font.
class PongTextView(View):
    def __init__(self, title_text: str = "PONG", title_font_size: int = 24, 
                 desc_text: str = "Press a key to start", desc_font_size: int = 16,
                 divider: bool = True, divider_width: int = Display.SCREEN_WIDTH, 
                 divider_height: int = 1):
        super().__init__()
        self.title = MultiLineTextComponent(Display.SCREEN_WIDTH // 2, Display.SCREEN_HEIGHT // 3,
                                            text=title_text, anchor=TextAnchor(VerticalAnchor.MIDDLE, 
                                            HorizontalAnchor.MIDDLE))
        
        self.start_text = MultiLineTextComponent(Display.SCREEN_WIDTH // 2, 
                                                 2 * Display.SCREEN_HEIGHT // 3,
                                                 text=desc_text, anchor=TextAnchor(VerticalAnchor.MIDDLE, 
                                                 HorizontalAnchor.MIDDLE))
        
        self.add_component(self.title)
        self.add_component(self.start_text)

        if divider:
            divider_x = (Display.SCREEN_WIDTH - divider_width) // 2
            self.divider = LineComponent(divider_x, Display.SCREEN_HEIGHT // 2, 
                                         Display.SCREEN_WIDTH - divider_x, 
                                         Display.SCREEN_HEIGHT // 2, width=divider_height)
        
            self.add_component(self.divider)

class GameOverView(PongTextView):
    def __init__(self, user_won: bool = False, title_font_size: int = 24, desc_font_size: int = 16, 
                 score_y_space_above: int = 4, score_font_size: int = 16, divider: bool = True,  
                 divider_width: int = Display.SCREEN_WIDTH, divider_height: int = 1):
        super().__init__(title_text="You Win!" if user_won else "Game Over", 
                         title_font_size=title_font_size, desc_text="Press any key\nto restart", 
                         desc_font_size=desc_font_size, divider=divider, 
                         divider_width=divider_width, divider_height=divider_height)
        
        _title_height, _ = self.title.get_text_size()
        self.score_text = MultiLineTextComponent(Display.SCREEN_WIDTH // 2, 
                                                  self.title.y + _title_height + score_y_space_above,
                                                  text="Score: ",
                                                  anchor=TextAnchor(VerticalAnchor.MIDDLE, 
                                                                   HorizontalAnchor.MIDDLE))
        
    def set_winner(self, user_winner: bool, score: int):
        self.title.text = "You Win!" if user_winner else "Game Over"
        self.score_text.text = f"Score: {score}"

if __name__ == "__main__":
    # Example usage
    pong_view_controller = PongViewController()
    Main.main(pong_view_controller)
