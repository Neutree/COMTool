
from ctypes import WinDLL, c_bool, c_int, c_longlong, POINTER, byref, Structure
from ctypes.wintypes import DWORD, HWND, LONG, LPCVOID
from enum import Enum


class DWMNCRENDERINGPOLICY(Enum):
    DWMNCRP_USEWINDOWSTYLE = 0
    DWMNCRP_DISABLED = 1
    DWMNCRP_ENABLED = 2
    DWMNCRP_LAS = 3

class DWMWINDOWATTRIBUTE(Enum):
    DWMWA_NCRENDERING_ENABLED = 1
    DWMWA_NCRENDERING_POLICY = 2
    DWMWA_TRANSITIONS_FORCEDISABLED = 3
    DWMWA_ALLOW_NCPAINT = 4
    DWMWA_CAPTION_BUTTON_BOUNDS = 5
    DWMWA_NONCLIENT_RTL_LAYOUT = 6
    DWMWA_FORCE_ICONIC_REPRESENTATION = 7
    DWMWA_FLIP3D_POLICY = 8
    DWMWA_EXTENDED_FRAME_BOUNDS = 9
    DWMWA_HAS_ICONIC_BITMAP = 10
    DWMWA_DISALLOW_PEEK = 11
    DWMWA_EXCLUDED_FROM_PEEK = 12
    DWMWA_CLOAK = 13
    DWMWA_CLOAKED = 14
    DWMWA_FREEZE_REPRESENTATION = 25
    DWMWA_LAST = 16

class GWL(Enum):
    GWL_EXSTYLE = -20
    # Retrieves the extended window styles.
    GWL_HINSTANCE = -6
    # Retrieves a handle to the application instance.
    GWL_HWNDPARENT = -8
    # Retrieves a handle to the parent window, if any.
    GWL_ID = -12
    # Retrieves the identifier of the window.
    GWL_STYLE = -16
    # Retrieves the window styles.
    GWL_USERDATA = -21
    # Retrieves the user data associated with the window. This data is intended for use by the application that created the window. Its value is initially zero.
    GWL_WNDPROC = -4

class WINDOW_STYLE(Enum):
    '''
        windows window style enumerate
    '''
    WS_BORDER = 0x00800000
    WS_CAPTION = 0x00C00000
    WS_CHILD = 0x40000000
    WS_CHILDWINDOW = 0x40000000
    WS_CLIPCHILDREN = 0x02000000
    WS_CLIPSIBLINGS = 0x04000000
    WS_DISABLED = 0x08000000
    WS_DLGFRAME = 0x00400000
    WS_GROUP = 0x00020000
    WS_HSCROLL = 0x00100000
    WS_ICONIC = 0x20000000
    WS_MAXIMIZE = 0x01000000
    WS_MAXIMIZEBOX = 0x00010000
    WS_MINIMIZE = 0x20000000
    WS_MINIMIZEBOX = 0x00020000
    WS_OVERLAPPED = 0x00000000
    WS_OVERLAPPEDWINDOW = 0x00CF0000
    WS_POPUP = 0x80000000
    WS_POPUPWINDOW = 0x80880000
    WS_SIZEBOX = 0x00040000
    WS_SYSMENU = 0x00080000
    WS_TABSTOP = 0x00010000
    WS_THICKFRAME = 0x00040000
    WS_TILED = 0x00000000
    WS_TILEDWINDOW = 0x00CF0000
    WS_VISIBLE = 0x10000000
    WS_VSCROLL = 0x00200000

class MARGINS(Structure):
    _fields_ = [
        ("cxLeftWidth", c_int),
        ("cxRightWidth", c_int),
        ("cyTopHeight", c_int),
        ("cyBottomHeight", c_int),
    ]

def addShadowEffect(hWnd):
    dwmapi = WinDLL("dwmapi")
    DwmExtendFrameIntoClientArea = dwmapi.DwmExtendFrameIntoClientArea
    DwmSetWindowAttribute = dwmapi.DwmSetWindowAttribute
    DwmExtendFrameIntoClientArea.restype = LONG
    DwmSetWindowAttribute.restype = LONG
    DwmSetWindowAttribute.argtypes = [c_int, DWORD, LPCVOID, DWORD]
    DwmExtendFrameIntoClientArea.argtypes = [c_int, POINTER(MARGINS)]
    hWnd = int(hWnd)
    DwmSetWindowAttribute(
        hWnd,
        DWMWINDOWATTRIBUTE.DWMWA_NCRENDERING_POLICY.value,
        byref(c_int(DWMNCRENDERINGPOLICY.DWMNCRP_ENABLED.value)),
        4,
    )
    margins = MARGINS(-1, -1, -1, -1)
    DwmExtendFrameIntoClientArea(hWnd, byref(margins))
    # set auto maxium window
    # TODO: how to make maiximumble when move window to the edge of screen ?
    # winuser = WinDLL("user32")
    # userGetWindowLong = winuser.GetWindowLongA
    # style = userGetWindowLong(hWnd, GWL.GWL_STYLE.value)
    # userSetWindowLongPtr = winuser.SetWindowLongPtrA
    # userSetWindowLongPtr(hWnd, GWL.GWL_STYLE.value,
    #     style |  WINDOW_STYLE.WS_THICKFRAME.value |  WINDOW_STYLE.WS_MAXIMIZEBOX.value )
