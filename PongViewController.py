from ViewController import ViewController
from View import View
import random
import Display
from typing import Optional, Tuple
import Main
from PIL import ImageDraw
from Views import TextView, LineView, CircleView, RectangleView, TextAnchor
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
                 ball_radius: int = 4, ball_init_speed: float = 1.5, 
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
        self.pong_view = None
        self.game_over_view.visible = False

        self.game_over = True
        
        self.view.add_subview(self.start_view)
        self.view.add_subview(self.game_over_view)

    def start_new_game(self):
        if self.pong_view is not None:
            self.view.remove_subview(self.pong_view)
        
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
            self.ball_init_y = random.randint(self.ball_radius, Display.SCREEN_HEIGHT - self.ball_radius)
        
        if self.ball_init_x < self.user_paddle_dist_from_edge + self.user_paddle_width:
            self.ball_init_x = self.user_paddle_dist_from_edge + self.user_paddle_width + self.ball_radius
        elif self.ball_init_x > Display.SCREEN_WIDTH - self.cpu_paddle_dist_from_edge - self.cpu_paddle_width:
            self.ball_init_x = Display.SCREEN_WIDTH - self.cpu_paddle_dist_from_edge - self.cpu_paddle_width - self.ball_radius

        if self.ball_init_y < self.ball_radius:
            self.ball_init_y = self.ball_radius
        elif self.ball_init_y > Display.SCREEN_HEIGHT - self.ball_radius:
            self.ball_init_y = Display.SCREEN_HEIGHT - self.ball_radius

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

        self.start_view.visible = False
        self.game_over_view.visible = False
        self.view.add_subview(self.pong_view)

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
                        
                    if self.ball_y < self.ball_radius - 1:
                        print("BALL_Y: ", self.ball_y)
                        self.ball_y = self.ball_radius - 1
                        self.ball_angle = -self.ball_angle
                        print("Ball Angle: ", self.ball_angle)
                    elif self.ball_y >= Display.SCREEN_HEIGHT - self.ball_radius:
                        self.ball_y = Display.SCREEN_HEIGHT - self.ball_radius
                        self.ball_angle = -self.ball_angle
                        print("Ball Angle: ", self.ball_angle)
                    
                    self.pong_view.set_ball_coords(int(round(self.ball_x)), int(round(self.ball_y)))

                    if self.ball_x < self.user_paddle_dist_from_edge - self.ball_radius:
                        self.game_over = True
                        self.user_winner = False
                        self.game_over_view.set_winner(self.user_winner, self._score)
                        self.game_over_view.visible = True
                        self.pong_view.visible = False
                    elif self.ball_x >= Display.SCREEN_WIDTH - self.cpu_paddle_dist_from_edge + self.ball_radius:
                        print("Ball info:")
                        print(self.ball_x)
                        print(Display.SCREEN_WIDTH)
                        print(self.cpu_paddle_dist_from_edge)
                        print(self.ball_radius)
                        self.game_over = True
                        self.user_winner = True
                        self.game_over_view.set_winner(self.user_winner, self._score)
                        self.game_over_view.visible = True
                        self.pong_view.visible = False
            time.sleep(0.1)


    def on_key3_press(self):
        if self.game_over:
            self.start_new_game()
            return True
        return False

    def on_key2_press(self):
        if self.game_over:
            self.start_new_game()
        else:
            self.pause = not self.pause
            self.pong_view.pause(self.pause)
            
            # if self.pause:
            #     self.rect_view = RectangleView(self.ball_x, self.ball_y, 1, 1)
            #     self.view.add_subview(self.rect_view)
            #     # self.pong_view._ball.visible = False

            #     print("Ball Coords:", (self.ball_x, self.ball_y))
            #     print("Ball Radius: ", self.ball_radius)
            #     print("User Paddle Coords:", (self.user_paddle_dist_from_edge, self.pong_view.get_paddle_y(True)))
            #     print("User Paddle Size: ", (self.user_paddle_width, self.user_paddle_height))
            #     print("CPU Paddle Coords: ", (Display.SCREEN_WIDTH - self.cpu_paddle_dist_from_edge - self.cpu_paddle_width, self.pong_view.get_paddle_y(False)))
            #     print("CPU Paddle Height: ", (self.cpu_paddle_width, self.cpu_paddle_height))
            #     print()
            # else:
            #     self.view.remove_subview(self.rect_view)
            #     # self.pong_view._ball.visible = True
            return True
        return False

    def on_key1_press(self):
        if self.game_over:
            self.start_new_game()
            return True
        return False

    def on_up_press(self):
        print("Joy Up Press")
        self.move_paddle(True, True)
        return self.game_over

    def on_up_hold(self):
        self.move_paddle(True, True)
        return self.game_over

    def on_down_press(self):
        self.move_paddle(True, False)
        return self.game_over

    def on_down_hold(self):
        self.move_paddle(True, False)
        return self.game_over

class PauseView(View):
    def __init__(self, x: int = 0, y: int = 0, width: int = Display.SCREEN_WIDTH, 
                 height: int = Display.SCREEN_HEIGHT, space_between_bars: int = 15):
        super().__init__(x=x, y=y, width=width, height=height)

        self.space_between_bars = space_between_bars
        self._bar_1 = RectangleView(x=0, y=0, width=1, height=1) 
        self._bar_2 = RectangleView(x=0, y=0, width=1, height=1)

        self.add_subview(self._bar_1)
        self.add_subview(self._bar_2)

    def _layout(self, parent_abs_x = 0, parent_abs_y = 0):
        super()._layout(parent_abs_x, parent_abs_y)

        # print("PauseView Layout Official")
        # print(self.x, self.y, self.width, self.height, self.space_between_bars)

        bar_width = (self.width - self.space_between_bars) // 2
        self._bar_1.x = 0
        self._bar_1.y = 0
        self._bar_2.x = bar_width + self.space_between_bars
        self._bar_2.y = 0

        self._bar_1.width = bar_width
        self._bar_1.height = self.height
        self._bar_2.width = bar_width
        self._bar_2.height = self.height

        # print("Bar 1:", self._bar_1.x, self._bar_1.y, self._bar_1.width, self._bar_1.height)
        # print("Bar 2:", self._bar_2.x, self._bar_2.y, self._bar_2.width, self._bar_2.height)
        

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
        super().__init__(0, 0, Display.SCREEN_WIDTH, Display.SCREEN_HEIGHT)

        self._ball_radius = ball_radius - 1/2
        self._ball = CircleView(ball_init_x + self._ball_radius, ball_init_y + self._ball_radius, self._ball_radius)
        self._user_paddle = RectangleView(user_paddle_dist_from_edge, user_paddle_init_y, 
                                              user_paddle_width, user_paddle_height)
        self._cpu_paddle = RectangleView(
            Display.SCREEN_WIDTH - cpu_paddle_dist_from_edge - cpu_paddle_width, 
            cpu_paddle_init_y, cpu_paddle_width, cpu_paddle_height)
        
        self.score_prefix = score_prefix
        self.score_suffix = score_suffix
        
        self.score_text_x = score_text_x
        self.score_text_y = score_text_y
        self.score_text = TextView(score_text_x, score_text_y,
                                                 text=f"{score_prefix}{score}{score_suffix}",
                                                 anchor=TextAnchor.LEFT_TOP)
        
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
        
        self.pause_view = PauseView(self.pause_small_x, self.pause_small_y, self.pause_small_width, 
                                         self.pause_small_height, self.pause_small_space_between_bars)
        
        print("HERE")
        self.add_subview(self._ball)
        self.add_subview(self._user_paddle)
        self.add_subview(self._cpu_paddle)
        self.add_subview(self.score_text)
        self.add_subview(self.pause_view)

    def get_ball_coords(self) -> Tuple[int, int]:
        return self._ball.x + self._ball_radius, self._ball.y + self._ball_radius
    
    def get_paddle_y(self, get_user_paddle: bool) -> Tuple[int, int]:
        return self._user_paddle.y if get_user_paddle else self._cpu_paddle.y
    
    def set_ball_coords(self, x: int, y: int):
        self._ball.x = x - self._ball_radius
        self._ball.y = y - self._ball_radius

    def set_paddle_y(self, set_user_paddle: bool, y: int):
        print("Setting paddle Y:", y, "for user paddle:", set_user_paddle)
        if set_user_paddle:
            self._user_paddle.y = y
            print("User Paddle Y:", self._user_paddle.y)
            print("Set Y:", y)
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
            self.pause_view.x = self.pause_big_x
            self.pause_view.y = self.pause_big_y
            self.pause_view.width = self.pause_big_width
            self.pause_view.height = self.pause_big_height
            self.pause_view.space_between_bars = self.pause_big_space_between_bars
        else:
            self.pause_view.x = self.pause_small_x
            self.pause_view.y = self.pause_small_y
            self.pause_view.width = self.pause_small_width
            self.pause_view.height = self.pause_small_height
            self.pause_view.space_between_bars = self.pause_small_space_between_bars
            # print("Pause View Layout")
            # print(self.pause_view.x, self.pause_view.y,
            #       self.pause_view.width, self.pause_view.height,
            #       self.pause_view.space_between_bars)
            
    def _layout(self, parent_abs_x = 0, parent_abs_y = 0):
        super()._layout(parent_abs_x, parent_abs_y)

        score_text_width, _ = self.score_text.get_text_size()
        self.score_text.x = self.score_text_x - score_text_width // 2
        self.score_text.y = self.score_text_y

# NOTE: FOR ALL VIEWS ____ FONT SIZE ____ has been disabled. Requires loading in a different font.
class PongTextView(View):
    def __init__(self, title_text: str = "PONG", title_font_size: int = 24, title_y: int = Display.SCREEN_HEIGHT // 3,
                 desc_text: str = "Press a key to start", desc_font_size: int = 16, desc_y: int = 2 * Display.SCREEN_HEIGHT // 3,
                 divider: bool = True, divider_width: int = Display.SCREEN_WIDTH, 
                 divider_height: int = 1):
        super().__init__()
        self.title = TextView(0, 0, text=title_text, anchor=TextAnchor.LEFT_TOP)
        
        self.start_text = TextView(0, 0, text=desc_text, anchor=TextAnchor.LEFT_TOP)

        self._title_y = title_y
        self._desc_y = desc_y
        
        self.add_subview(self.title)
        self.add_subview(self.start_text)

        if divider:
            self.divider_width = divider_width
            self.divider = LineView(0, 0, 0, 0, stroke_width=divider_height)
            self.add_subview(self.divider)
    
    def _layout(self, parent_abs_x = 0, parent_abs_y = 0):
        super()._layout(parent_abs_x, parent_abs_y)

        self.width = self.superview.width
        self.height = self.superview.height
        self.x = 0
        self.y = 0

        title_width, title_height = self.title.get_text_size()
        self.title.x = (self.width- title_width) // 2
        self.title.y = self._title_y - title_height // 2

        start_text_width, start_text_height = self.start_text.get_text_size()
        self.start_text.x = (self.width - start_text_width) // 2
        self.start_text.y = self._desc_y - start_text_height // 2

        if self.divider is not None:
            divider_x = (self.width - self.divider_width) // 2

            self.divider.update_line_points(
                divider_x, self.height // 2, 
                self.width - divider_x, self.height // 2
            )


class GameOverView(PongTextView):
    def __init__(self, user_won: bool = False, title_font_size: int = 24, desc_font_size: int = 16, 
                 score_y_space_above: int = 4, score_font_size: int = 16, divider: bool = True,  
                 divider_width: int = Display.SCREEN_WIDTH, divider_height: int = 1):
        super().__init__(title_text="You Win!" if user_won else "Game Over", title_y=Display.SCREEN_HEIGHT // 5,
                         title_font_size=title_font_size, desc_text="Press any key to restart", 
                         desc_font_size=desc_font_size, divider=divider, 
                         divider_width=divider_width, divider_height=divider_height)
        
        self.score_y_space_above = score_y_space_above
        self.score_text = TextView(0, 0, text="Score: ", anchor=TextAnchor.LEFT_TOP)
        
        self.add_subview(self.score_text)
        
    def set_winner(self, user_winner: bool, score: int):
        self.title.text = "You Win!" if user_winner else "Game Over"
        self.score_text.text = f"Score: {score}"

    def _layout(self, parent_abs_x = 0, parent_abs_y = 0):
        super()._layout(parent_abs_x, parent_abs_y)
        

        self.width = self.superview.width
        self.height = self.superview.height
        self.x = 0
        self.y = 0

        score_text_width, score_text_height = self.score_text.get_text_size()
        _, title_height = self.title.get_text_size()
        self.score_text.x = (self.width - score_text_width) // 2
        self.score_text.y = self.title.y + title_height + self.score_y_space_above

if __name__ == "__main__":
    # Example usage
    pong_view_controller = PongViewController()
    Main.main(pong_view_controller)
