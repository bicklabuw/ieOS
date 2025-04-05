from abc import ABC, abstractmethod
import Display
from Components import Component
from typing import List

class View(ABC):
    def __init__(self):
        # Set General Default View Constants
        self.CHAR_LINE_SPACE = 1 # Added space to each line (built in space)
        self.CHAR_WIDTH: int = 6 # No Space Between some chars - ONLY WORKS FOR DEFAULT FONT
        self.CHAR_HEIGHT: int = 9 # ONLY WORKS FOR DEFAULT FONT
        self.LINE_HEIGHT: int = self.CHAR_HEIGHT + self.CHAR_LINE_SPACE
        self.LINE_SPACING: int = 1 # Space between lines
        self.TEXT_ALIGN: str = "center"
        
        self.TEXT_COLOR: str = "WHITE"

        # Get the Screen Width and Height
        self.SCREEN_WIDTH: int = Display.SCREEN_WIDTH
        self.SCREEN_HEIGHT: int = Display.SCREEN_HEIGHT

        # Set the list of components
        self._components: List[Component] = []

    def add_component(self, component: Component):
        if not isinstance(component, Component):
            raise TypeError("Component must be an instance of the Component class")
        
        if component in self._components:
            raise ValueError("Component already exists in the view")
        
        # Add the component to the list
        self._components.append(component)

    def remove_component(self, component: Component):
        if component not in self._components:
            raise ValueError("Component not found in the view")
        
        # Remove the component from the list
        self._components.remove(component)

    def get_components(self) -> List[Component]:
        return self._components
    
    def clear_components(self):
        self._components.clear()
    

    
    