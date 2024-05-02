# define Python user-defined exceptions
class CustomNetworkError(Exception):
    'Raised when the MCU has a network issue'
    pass

class CustomResetError(Exception):
    'Raised for a reset error'
    pass

class CustomHWError(Exception):
    'Raised for a hardware error'
    pass

class CustomMoistureSensorError(Exception):
    'Raised for a Moisture Sensor error'
    pass

class CustomLDRSensorError(Exception):
    'Raised for a LDR Sensor error'
    pass
