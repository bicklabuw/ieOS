from Main import main
from OSGlobals import OSVersion
from ViewController import ViewController
from RecordSetupViewController import RecordSetupViewController

STARTUP_TITLE_TEXT = "Insect Eavesdropper"
STARTUP_SUBTITLE_TEXT = "Version: " + OSVersion
STARTUP_DURATION = 3  # seconds
STARTING_VIEW_CONTROLLER = RecordSetupViewController

DEFAULT_STARTUP_DURATION = STARTUP_DURATION  # seconds

if __name__ == "__main__":
    # Create the startup view controller
    startup_vc = StartupViewController(
        starting_vc=STARTING_VIEW_CONTROLLER(),
        title=STARTUP_TITLE_TEXT,
        subtitle=STARTUP_SUBTITLE_TEXT,
        on_screen_sec=DEFAULT_STARTUP_DURATION
    )

    Main.main(startup_vc)

def StartupViewController(ViewController):
    def __init__(self, starting_vc: ViewController, title: str, subtitle: str, 
                 on_screen_sec: int = DEFAULT_STARTUP_DURATION):
        super().__init__()

        self.starting_vc = starting_vc
        self.on_screen_sec = on_screen_sec
        
        self.view = TitleView()
        self.view.text = title
        #self.view.title_text = title
        #self.view.subtitle_text = subtitle
        self.present_view(self.view)

    def on_appear(self):
        time.sleep(self.on_screen_sec)
        self.change_view_controller(self.starting_vc, ChangeViewControllerType.CLEAR)