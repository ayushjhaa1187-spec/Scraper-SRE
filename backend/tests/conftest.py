import sys
import unittest.mock

# Mock missing dependencies
sys.modules['bs4'] = unittest.mock.MagicMock()
sys.modules['lxml'] = unittest.mock.MagicMock()
