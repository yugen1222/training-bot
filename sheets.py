import gspread
from google.oauth2.service_account import Credentials
from config import GOOGLE_SHEET_NAME, SERVICE_ACCOUNT_FILE

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]


def open_sheet():
    creds = Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE,
        scopes=SCOPES
    )
    client = gspread.authorize(creds)
    return client.open(GOOGLE_SHEET_NAME)


def get_summary_rows():
    sheet = open_sheet()
    ws = sheet.worksheet("Сводка")
    return ws.get_all_records()


def get_branches():
    rows = get_summary_rows()
    branches = sorted(set(row.get("Филиал") for row in rows if row.get("Филиал")))
    return branches


def get_employees_by_branch(branch):
    rows = get_summary_rows()
    return [
        row for row in rows
        if str(row.get("Филиал", "")).strip().lower() == branch.strip().lower()
    ]


def find_employee(text):
    rows = get_summary_rows()
    text = text.strip().lower()

    result = []
    for row in rows:
        fio = str(row.get("ФИО", "")).lower()
        emp_id = str(row.get("ID сотрудника", "")).lower()

        if text in fio or text in emp_id:
            result.append(row)


def get_bot_users():
    sheet = open_sheet()
    ws = sheet.worksheet("Пользователи")
    return ws.get_all_records()


def get_tm_chat_ids():
    users = get_bot_users()
    return [
        int(row.get("Telegram ID"))
        for row in users
        if str(row.get("Роль", "")).strip().lower() == "tm"
        and str(row.get("Telegram ID", "")).strip()
    ]


def get_ready_for_tm():
    rows = get_summary_rows()
    return [
        row for row in rows
        if str(row.get("Уведомить ТМ", "")).strip().lower() == "да"
    ]

    return result
