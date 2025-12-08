"""莲池宇宙生物体系"""

from .organism import Organism
from .simple_organism import SimpleOrganism
from .intelligent_organism import IntelligentOrganism
from .reproduction import ReproductionSystem
from .component_acquisition import ComponentAcquisitionSystem

__all__ = [
    "Organism",
    "SimpleOrganism",
    "IntelligentOrganism",
    "ReproductionSystem",
    "ComponentAcquisitionSystem"
]