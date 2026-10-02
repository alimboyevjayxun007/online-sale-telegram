from aiogram.filters.callback_data import CallbackData


class Menu(CallbackData, prefix="m"):
    a: str


class Fl(CallbackData, prefix="f"):  # purchase-flow step
    s: str
    v: str = ""


class Pay(CallbackData, prefix="p"):
    a: str
    id: str = ""


class Ord(CallbackData, prefix="o"):
    a: str
    id: str = ""
    page: int = 0


class Wal(CallbackData, prefix="w"):
    a: str
    v: str = ""
    page: int = 0


class Set(CallbackData, prefix="s"):
    a: str
    v: str = ""


class Adm(CallbackData, prefix="a"):
    sec: str
    act: str = "open"
    id: str = ""
    page: int = 0


class Cf(CallbackData, prefix="cf"):
    token: str
    yes: bool
