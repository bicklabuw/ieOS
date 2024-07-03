import SH1106

disp = None

def init():
    global disp
    # If not created yet, create display object
    if disp is None:
        print("HI")
        # Create, Initialize and Clear display object.
        disp = SH1106.SH1106()
        disp.Init()
        disp.clear()